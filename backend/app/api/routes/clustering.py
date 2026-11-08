from fastapi import APIRouter, status

try:
    from app.schemas.clustering_and_routing import ClusteringRequest, ClusteringResponse
    from app.services.clustering_service import clustering_service
except ImportError:
    from backend.app.schemas.clustering_and_routing import ClusteringRequest, ClusteringResponse
    from backend.app.services.clustering_service import clustering_service

router = APIRouter(prefix="/clustering", tags=["Geographic Clustering"])


@router.post(
    "/generate",
    response_model=ClusteringResponse,
    status_code=status.HTTP_200_OK,
    summary="Group tourist attractions using spatial density clustering (DBSCAN)",
    description=(
        "Executes DBSCAN with Haversine great-circle distance to group nearby tourist attractions "
        "into natural spatial clusters, identifies isolated outliers as noise, computes geographic centroids "
        "and bounding envelopes, and optionally compares results against rigid K-Means clustering."
    ),
)
def generate_clusters(
    payload: ClusteringRequest,
) -> ClusteringResponse:
    """Perform spatial clustering on provided attractions."""
    return clustering_service.generate_clusters(payload)

