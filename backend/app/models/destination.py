from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.database.base import Base, TimestampMixin
except ImportError:
    from backend.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip import Trip, ItineraryPlace
    from app.models.interaction import Review, SavedPlace


class Destination(Base, TimestampMixin):
    """Geographic travel destination (city, region, or country)."""
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    places: Mapped[List["Place"]] = relationship(
        "Place",
        back_populates="destination",
        cascade="all, delete-orphan",
    )
    trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="destination",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Destination(id={self.id}, name='{self.name}', country='{self.country}')>"


class Place(Base, TimestampMixin):
    """Specific point of interest, tourist attraction, activity, or venue."""
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    external_place_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    estimated_visit_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # in minutes
    opening_hours: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entrance_fee: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), default="internal", nullable=True)
    image_attribution: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    image_verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)

    # Foreign Key to Destination
    destination_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    destination: Mapped["Destination"] = relationship("Destination", back_populates="places")
    itinerary_places: Mapped[List["ItineraryPlace"]] = relationship(
        "ItineraryPlace",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    saved_by_users: Mapped[List["SavedPlace"]] = relationship(
        "SavedPlace",
        back_populates="place",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Place(id={self.id}, name='{self.name}', category='{self.category}')>"


class AttractionImageCache(Base, TimestampMixin):
    """Persistent cache for attraction-specific verified photograph lookups."""
    __tablename__ = "attraction_image_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    lookup_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    attraction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    attraction_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_source: Mapped[str] = mapped_column(String(50), default="wikimedia", nullable=False)
    image_attribution: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    image_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<AttractionImageCache(name='{self.attraction_name}', city='{self.city}', verified={self.image_verified})>"


