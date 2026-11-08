from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.database.base import Base, TimestampMixin
except ImportError:
    from backend.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.destination import Destination, Place


class Trip(Base, TimestampMixin):
    """User planned or booked travel itinerary container."""
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    budget: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    travelers_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    transportation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planned", nullable=False, index=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trips")
    destination: Mapped["Destination"] = relationship("Destination", back_populates="trips")
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="trip",
        cascade="all, delete-orphan",
    )
    preferences: Mapped[Optional["TripPreference"]] = relationship(
        "TripPreference",
        back_populates="trip",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, user_id={self.user_id}, destination_id={self.destination_id}, status='{self.status}')>"


class TripPreference(Base, TimestampMixin):
    """Specific parameters and preferences configured for an individual trip."""
    __tablename__ = "trip_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("trips.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    pace: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # relaxed, moderate, packed
    interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON or comma-separated
    dietary_restrictions: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    accommodation_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship back to Trip
    trip: Mapped["Trip"] = relationship("Trip", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<TripPreference(trip_id={self.trip_id}, pace='{self.pace}')>"


class Itinerary(Base, TimestampMixin):
    """Generated or customized daily schedule for a trip."""
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    total_estimated_cost: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    total_distance: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)  # in km
    total_duration: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)  # in hours

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="itineraries")
    days: Mapped[List["ItineraryDay"]] = relationship(
        "ItineraryDay",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryDay.day_number",
    )

    def __repr__(self) -> str:
        return f"<Itinerary(id={self.id}, title='{self.title}', trip_id={self.trip_id})>"


class ItineraryDay(Base, TimestampMixin):
    """Single day schedule within a multi-day itinerary."""
    __tablename__ = "itinerary_days"
    __table_args__ = (
        UniqueConstraint("itinerary_id", "day_number", name="uq_itinerary_day_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    itinerary_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("itineraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    travel_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    itinerary: Mapped["Itinerary"] = relationship("Itinerary", back_populates="days")
    places: Mapped[List["ItineraryPlace"]] = relationship(
        "ItineraryPlace",
        back_populates="itinerary_day",
        cascade="all, delete-orphan",
        order_by="ItineraryPlace.visit_order",
    )

    def __repr__(self) -> str:
        return f"<ItineraryDay(id={self.id}, itinerary_id={self.itinerary_id}, day_number={self.day_number})>"


class ItineraryPlace(Base, TimestampMixin):
    """Association connecting a specific attraction/place to an itinerary day with order and times."""
    __tablename__ = "itinerary_places"
    __table_args__ = (
        UniqueConstraint("itinerary_day_id", "visit_order", name="uq_day_place_visit_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    itinerary_day_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("itinerary_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visit_order: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g. "09:30"
    departure_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g. "11:30"

    # Relationships
    itinerary_day: Mapped["ItineraryDay"] = relationship("ItineraryDay", back_populates="places")
    place: Mapped["Place"] = relationship("Place", back_populates="itinerary_places")

    def __repr__(self) -> str:
        return f"<ItineraryPlace(day_id={self.itinerary_day_id}, place_id={self.place_id}, order={self.visit_order})>"

