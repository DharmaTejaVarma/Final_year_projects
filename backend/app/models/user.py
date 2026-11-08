from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.database.base import Base, TimestampMixin
except ImportError:
    from backend.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.interaction import Review, SavedPlace


class User(Base, TimestampMixin):
    """User account entity for travelers and administrators."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 1-to-1 relationship with UserPreferences
    preferences: Mapped[Optional["UserPreference"]] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-many relationships
    trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_places: Mapped[List["SavedPlace"]] = relationship(
        "SavedPlace",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"


class UserPreference(Base, TimestampMixin):
    """Travel preferences associated with a user."""
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    preferred_categories: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string or comma-separated
    preferred_activities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_transport: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_budget: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_travel_style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, style='{self.preferred_travel_style}')>"

