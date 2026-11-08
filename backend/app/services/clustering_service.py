from typing import Dict, List, Optional
from collections import defaultdict

try:
    from app.algorithms.geographic_clustering import (
        run_dbscan_haversine,
        run_kmeans_comparison,
        calculate_cluster_envelope,
        get_dbscan_suitability_explanation,
    )
    from app.core.logger import logger
    from app.schemas.clustering_and_routing import (
        ClusteringRequest,
        ClusteringResponse,
        ClusterGroup,
        ClusterMember,
        ClusterCentroid,
        ClusterBoundingBox,
        KMeansComparison,
        POIInput,
    )
except ImportError:
    from backend.app.algorithms.geographic_clustering import (
        run_dbscan_haversine,
        run_kmeans_comparison,
        calculate_cluster_envelope,
        get_dbscan_suitability_explanation,
    )
    from backend.app.core.logger import logger
    from backend.app.schemas.clustering_and_routing import (
        ClusteringRequest,
        ClusteringResponse,
        ClusterGroup,
        ClusterMember,
        ClusterCentroid,
        ClusterBoundingBox,
        KMeansComparison,
        POIInput,
    )


class ClusteringService:
    """Service orchestrating spatial clustering for tourist points of interest."""

    @staticmethod
    def generate_clusters(request: ClusteringRequest) -> ClusteringResponse:
        """Perform spatial density clustering using DBSCAN and optional K-Means comparison."""
        places: List[POIInput] = request.places
        total_places = len(places)

        logger.info(
            f"Clustering {total_places} places with DBSCAN (eps={request.eps_km} km, "
            f"min_samples={request.min_samples})"
        )

        coordinates = [(p.latitude, p.longitude) for p in places]

        # Run DBSCAN
        labels = run_dbscan_haversine(
            coordinates=coordinates,
            eps_km=request.eps_km,
            min_samples=request.min_samples,
        )

        # Group places by cluster label
        clusters_map: Dict[int, List[int]] = defaultdict(list)
        for idx, label in enumerate(labels):
            clusters_map[label].append(idx)

        # Build ClusterGroup objects
        cluster_groups: List[ClusterGroup] = []
        noise_count = 0
        clusters_count = 0

        # Sort keys so non-noise clusters come first (0, 1, 2...), then noise (-1) at the end
        sorted_labels = sorted([k for k in clusters_map.keys() if k != -1])
        if -1 in clusters_map:
            sorted_labels.append(-1)

        for label in sorted_labels:
            indices = clusters_map[label]
            member_places = [places[i] for i in indices]
            member_coords = [(places[i].latitude, places[i].longitude) for i in indices]

            is_noise = (label == -1)
            if is_noise:
                noise_count = len(indices)
                label_text = "Noise / Isolated Outliers"
            else:
                clusters_count += 1
                label_text = f"Cluster {clusters_count}"

            envelope = calculate_cluster_envelope(member_coords)

            members = [
                ClusterMember(
                    id=p.id,
                    name=p.name,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    category=p.category,
                    visit_duration_mins=p.visit_duration_mins,
                )
                for p in member_places
            ]

            cluster_group = ClusterGroup(
                cluster_id=label,
                label=label_text,
                is_noise=is_noise,
                members_count=len(members),
                centroid=(
                    ClusterCentroid(
                        latitude=envelope["centroid"]["latitude"],
                        longitude=envelope["centroid"]["longitude"],
                    )
                    if not is_noise and envelope["centroid"]["latitude"] != 0.0
                    else None
                ),
                radius_km=envelope["radius_km"] if not is_noise else 0.0,
                bounding_box=(
                    ClusterBoundingBox(**envelope["bounding_box"])
                    if not is_noise
                    else None
                ),
                places=members,
            )
            cluster_groups.append(cluster_group)

        # K-Means comparison baseline
        kmeans_comparison_res: Optional[KMeansComparison] = None
        if request.compare_kmeans:
            km_data = run_kmeans_comparison(coordinates, k=request.k)
            kmeans_comparison_res = KMeansComparison(
                k=km_data["k"],
                clusters_count=km_data["clusters_count"],
                inertia=km_data["inertia"],
                silhouette_score=km_data["silhouette_score"],
                cluster_distribution=km_data["cluster_distribution"],
                summary=km_data["summary"],
            )

        return ClusteringResponse(
            algorithm_used="DBSCAN (Density-Based Spatial Clustering of Applications with Noise)",
            metric="Haversine (Great-Circle Geodetic Distance on WGS-84 Sphere)",
            eps_km=request.eps_km,
            min_samples=request.min_samples,
            total_places=total_places,
            clusters_count=clusters_count,
            noise_count=noise_count,
            clusters=cluster_groups,
            kmeans_comparison=kmeans_comparison_res,
            dbscan_suitability_explanation=get_dbscan_suitability_explanation(),
        )


clustering_service = ClusteringService()

