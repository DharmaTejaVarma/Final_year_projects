import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score

EARTH_RADIUS_KM = 6371.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great-Circle distance between two points on the Earth's surface in kilometers."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def run_dbscan_haversine(
    coordinates: List[Tuple[float, float]],
    eps_km: float = 3.5,
    min_samples: int = 2,
) -> List[int]:
    """Execute DBSCAN density clustering over geographic coordinates using Haversine distance metric.

    Args:
        coordinates: List of (latitude, longitude) tuples.
        eps_km: Search radius epsilon in kilometers.
        min_samples: Minimum neighborhood samples required for a core point.

    Returns:
        List of cluster labels corresponding to each input coordinate.
        -1 denotes noise / spatial outliers; 0, 1, 2... denote cluster indices.
    """
    n_points = len(coordinates)
    if n_points == 0:
        return []

    if n_points < min_samples:
        # Fewer points than min_samples cannot form a core cluster
        return [-1] * n_points

    # Scikit-learn DBSCAN with metric='haversine' expects radians in [lat, lon] order
    coords_rad = np.radians(np.array(coordinates, dtype=np.float64))
    eps_rad = eps_km / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine")
    db.fit(coords_rad)

    return db.labels_.tolist()


def run_kmeans_comparison(
    coordinates: List[Tuple[float, float]],
    k: Optional[int] = None,
) -> Dict[str, Any]:
    """Run K-Means clustering as a comparison baseline against density-based DBSCAN.

    Args:
        coordinates: List of (latitude, longitude) tuples.
        k: Optional pre-set number of clusters. If None, chosen adaptively.

    Returns:
        Dictionary containing K-Means evaluation metrics and cluster assignments.
    """
    n_points = len(coordinates)
    if n_points == 0:
        return {
            "k": 0,
            "clusters_count": 0,
            "labels": [],
            "inertia": 0.0,
            "silhouette_score": None,
            "cluster_distribution": {},
            "summary": "No coordinates provided for K-Means clustering.",
        }

    # Determine K
    if k is None or k < 1:
        # Default adaptive K: min(3, n_points)
        target_k = min(3, n_points)
    else:
        target_k = min(k, n_points)

    if target_k == 1 or n_points == 1:
        labels = [0] * n_points
        return {
            "k": 1,
            "clusters_count": 1,
            "labels": labels,
            "inertia": 0.0,
            "silhouette_score": None,
            "cluster_distribution": {"Cluster 0": n_points},
            "summary": (
                "K-Means with k=1 grouped all points into a single cluster. "
                "Silhouette score is undefined for k=1."
            ),
        }

    # Fit K-Means
    coords_arr = np.array(coordinates, dtype=np.float64)
    kmeans = KMeans(n_clusters=target_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords_arr).tolist()

    # Calculate silhouette score if valid
    sil_score: Optional[float] = None
    if 1 < target_k < n_points:
        try:
            sil_score = round(float(silhouette_score(coords_arr, labels)), 3)
        except Exception:
            sil_score = None

    # Count distribution
    distribution: Dict[str, int] = {}
    for label in labels:
        key = f"Cluster {label}"
        distribution[key] = distribution.get(key, 0) + 1

    summary = (
        f"K-Means partitioned {n_points} places into k={target_k} rigid clusters "
        f"with inertia {kmeans.inertia_:.2f}. "
    )
    if sil_score is not None:
        summary += f"Silhouette score: {sil_score:.3f}. "
    summary += "Notice that K-Means forces every outlier into a cluster, which distorts cluster centroids."

    return {
        "k": target_k,
        "clusters_count": target_k,
        "labels": labels,
        "inertia": round(float(kmeans.inertia_), 2),
        "silhouette_score": sil_score,
        "cluster_distribution": distribution,
        "summary": summary,
    }


def calculate_cluster_envelope(
    coordinates: List[Tuple[float, float]],
) -> Dict[str, Any]:
    """Calculate the geographic centroid, maximum radius, and bounding box for a set of coordinates."""
    if not coordinates:
        return {
            "centroid": {"latitude": 0.0, "longitude": 0.0},
            "radius_km": 0.0,
            "bounding_box": {"min_lat": 0.0, "max_lat": 0.0, "min_lon": 0.0, "max_lon": 0.0},
        }

    lats = [c[0] for c in coordinates]
    lons = [c[1] for c in coordinates]

    centroid_lat = sum(lats) / len(lats)
    centroid_lon = sum(lons) / len(lons)

    max_radius_km = 0.0
    for lat, lon in coordinates:
        dist = haversine_distance_km(centroid_lat, centroid_lon, lat, lon)
        if dist > max_radius_km:
            max_radius_km = dist

    return {
        "centroid": {
            "latitude": round(centroid_lat, 6),
            "longitude": round(centroid_lon, 6),
        },
        "radius_km": round(max_radius_km, 2),
        "bounding_box": {
            "min_lat": round(min(lats), 6),
            "max_lat": round(max(lats), 6),
            "min_lon": round(min(lons), 6),
            "max_lon": round(max(lons), 6),
        },
    }


def get_dbscan_suitability_explanation() -> str:
    """Return comprehensive domain justification explaining why DBSCAN is preferred over K-Means for tourism clustering."""
    return (
        "DBSCAN (Density-Based Spatial Clustering of Applications with Noise) is substantially superior "
        "to centroid-based algorithms like K-Means for geographic tourist attraction clustering for four key reasons:\n\n"
        "1. Arbitrary Cluster Geometries: Tourist attractions naturally cluster along riverbanks, historical "
        "corridors, and commercial avenues. DBSCAN discovers arbitrary non-spherical shapes, whereas K-Means "
        "enforces isotropic, convex spherical clusters.\n\n"
        "2. No Prior Cluster Count (K) Required: Travelers select varying numbers of attractions across cities. "
        "DBSCAN discovers natural clusters dynamically based on spatial density (eps and min_samples), whereas "
        "K-Means requires guessing or forcing an arbitrary cluster count K in advance.\n\n"
        "3. Explicit Noise & Outlier Segregation: Suburban attractions or remote day-trip destinations (e.g., "
        "Ramoji Film City 35 km away from central Hyderabad) are properly labeled as noise (cluster_id = -1). "
        "K-Means forcibly pulls distant outliers into the nearest cluster, skewing centroids and ruining itinerary efficiency.\n\n"
        "4. Geodetic Distance Fidelity: DBSCAN natively executes over great-circle Haversine distances on the spherical Earth "
        "without projection distortions that occur with Euclidean planar metrics."
    )

