try:
    from app.database.base import Base
    from app.models.user import User, UserPreference
    from app.models.destination import Destination, Place, AttractionImageCache
    from app.models.trip import (
        Trip,
        TripPreference,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
    )
    from app.models.interaction import Review, SavedPlace
except ImportError:
    from backend.app.database.base import Base
    from backend.app.models.user import User, UserPreference
    from backend.app.models.destination import Destination, Place, AttractionImageCache
    from backend.app.models.trip import (
        Trip,
        TripPreference,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
    )
    from backend.app.models.interaction import Review, SavedPlace

__all__ = [
    "Base",
    "User",
    "UserPreference",
    "Destination",
    "Place",
    "AttractionImageCache",
    "Trip",
    "TripPreference",
    "Itinerary",
    "ItineraryDay",
    "ItineraryPlace",
    "Review",
    "SavedPlace",
]

