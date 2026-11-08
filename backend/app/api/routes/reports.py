import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from app.api.dependencies import get_db, get_optional_current_user
    from app.core.logger import logger
    from app.models.user import User
    from app.schemas.report import (
        ReportGenerateRequest,
        ReportMetadataResponse,
    )
    from app.services.analytics_service import analytics_service
    from app.services.itinerary_service import ITINERARY_CACHE, itinerary_service
    from app.services.pdf_service import pdf_service
except ImportError:
    from backend.app.api.dependencies import get_db, get_optional_current_user
    from backend.app.core.logger import logger
    from backend.app.models.user import User
    from backend.app.schemas.report import (
        ReportGenerateRequest,
        ReportMetadataResponse,
    )
    from backend.app.services.analytics_service import analytics_service
    from backend.app.services.itinerary_service import ITINERARY_CACHE, itinerary_service
    from backend.app.services.pdf_service import pdf_service

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

# In-memory store for generated report metadata
REPORT_METADATA_STORE: Dict[str, Dict[str, Any]] = {}


@router.post(
    "/generate",
    response_model=ReportMetadataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Itinerary PDF Dossier & Analytics",
)
async def generate_travel_report(
    payload: ReportGenerateRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ReportMetadataResponse:
    """Generate an executive PDF travel dossier with ReportLab and compute the 7 visual analytics datasets."""
    itinerary_data: Optional[Dict[str, Any]] = None

    if payload.itinerary_data:
        itinerary_data = payload.itinerary_data
    elif payload.itinerary_id:
        cached_itin = itinerary_service.get_itinerary(payload.itinerary_id)
        if cached_itin:
            itinerary_data = (
                cached_itin.model_dump() if hasattr(cached_itin, "model_dump") else dict(cached_itin)
            )

    if not itinerary_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Itinerary not found. Provide valid 'itinerary_id' or full 'itinerary_data' in request body.",
        )

    report_id = f"rep_{uuid.uuid4().hex[:12]}"

    try:
        # 1. Generate PDF file via ReportLab
        pdf_path, pdf_bytes = pdf_service.generate_itinerary_pdf(
            itinerary=itinerary_data,
            title=payload.title,
            planning_notes=payload.planning_notes,
            report_id=report_id,
        )
        file_size = len(pdf_bytes)

        # 2. Compute the 7 Visual Analytics Datasets
        analytics = analytics_service.compute_itinerary_analytics(itinerary_data)

        # 3. Assemble Metadata
        dest = itinerary_data.get("destination", "Destination")
        s_date = itinerary_data.get("start_date", "TBD")
        e_date = itinerary_data.get("end_date", "TBD")
        travelers = int(itinerary_data.get("travelers_count", 1))
        t_days = max(int(itinerary_data.get("total_days", len(itinerary_data.get("days", [])))), 1)
        b_summary = itinerary_data.get("budget_summary", {})
        t_cost = float(
            b_summary.get("estimated_total_cost")
            if isinstance(b_summary, dict)
            else getattr(b_summary, "estimated_total_cost", 0.0)
        )
        t_dist = float(itinerary_data.get("total_distance_km", 0.0))
        t_travel_mins = float(itinerary_data.get("total_travel_time_mins", 0.0))
        t_visit_mins = float(itinerary_data.get("total_visit_time_mins", 0.0))
        t_hours = round((t_travel_mins + t_visit_mins) / 60.0, 1)

        download_url = f"/api/reports/{report_id}/download"
        created_at_str = datetime.utcnow().isoformat() + "Z"

        meta_dict = {
            "report_id": report_id,
            "itinerary_id": str(payload.itinerary_id or itinerary_data.get("itinerary_id") or "itin_unknown"),
            "title": payload.title or f"{t_days}-Day Executive Travel Dossier: {dest}",
            "destination": dest,
            "travel_dates": f"{s_date} to {e_date}",
            "travelers_count": travelers,
            "total_days": t_days,
            "total_cost": round(t_cost, 2),
            "total_distance_km": round(t_dist, 1),
            "total_duration_hours": t_hours,
            "file_size_bytes": file_size,
            "created_at": created_at_str,
            "download_url": download_url,
            "analytics": analytics,
            "summary": {
                "destination": dest,
                "feasibility_status": itinerary_data.get("feasibility_status", "feasible"),
                "total_attractions": len(analytics.score_distribution),
                "outdoor_count": analytics.attraction_metrics.outdoor_count,
                "indoor_count": analytics.attraction_metrics.indoor_count,
            },
            "user_id": current_user.id if current_user else None,
            "file_path": pdf_path,
        }

        REPORT_METADATA_STORE[report_id] = meta_dict

        return ReportMetadataResponse(
            report_id=report_id,
            itinerary_id=meta_dict["itinerary_id"],
            title=meta_dict["title"],
            destination=dest,
            travel_dates=meta_dict["travel_dates"],
            travelers_count=travelers,
            total_days=t_days,
            total_cost=meta_dict["total_cost"],
            total_distance_km=meta_dict["total_distance_km"],
            total_duration_hours=t_hours,
            file_size_bytes=file_size,
            created_at=created_at_str,
            download_url=download_url,
            analytics=analytics,
            summary=meta_dict["summary"],
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(e)}",
        )


@router.get(
    "/{report_id}",
    response_model=ReportMetadataResponse,
    summary="Get Report Metadata & Visual Analytics",
)
async def get_travel_report(
    report_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ReportMetadataResponse:
    """Retrieve metadata and analytical breakdown for a previously generated report."""
    report = REPORT_METADATA_STORE.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' was not found or has expired.",
        )

    # Secure report access: if report is bound to a user, enforce authorized requester
    if report.get("user_id") is not None:
        if current_user and current_user.id != report["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to view this report.",
            )

    return ReportMetadataResponse(
        report_id=report["report_id"],
        itinerary_id=report["itinerary_id"],
        title=report["title"],
        destination=report["destination"],
        travel_dates=report["travel_dates"],
        travelers_count=report["travelers_count"],
        total_days=report["total_days"],
        total_cost=report["total_cost"],
        total_distance_km=report["total_distance_km"],
        total_duration_hours=report["total_duration_hours"],
        file_size_bytes=report["file_size_bytes"],
        created_at=report["created_at"],
        download_url=report["download_url"],
        analytics=report["analytics"],
        summary=report["summary"],
    )


@router.get(
    "/{report_id}/download",
    summary="Download Generated PDF Dossier",
)
async def download_travel_report(
    report_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """Download the generated ReportLab PDF document as an attachment."""
    report = REPORT_METADATA_STORE.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' was not found.",
        )

    # Secure report access
    if report.get("user_id") is not None:
        if current_user and current_user.id != report["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to download this report.",
            )

    pdf_file_path = report.get("file_path")
    if not pdf_file_path or not os.path.exists(pdf_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested PDF file is no longer available on disk.",
        )

    dest_slug = report["destination"].lower().replace(" ", "_")
    filename = f"TravelSenseAI_{dest_slug}_itinerary_{report_id}.pdf"

    return FileResponse(
        path=pdf_file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
