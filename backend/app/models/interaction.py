from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.database.base import Base, TimestampMixin
except ImportError:
    from backend.app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.destination import Place


class Review(Base, TimestampMixin):
    """User rating and qualitative review for a place."""
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_user_place_review"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    place: Mapped["Place"] = relationship("Place", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(user_id={self.user_id}, place_id={self.place_id}, rating={self.rating})>"


class SavedPlace(Base, TimestampMixin):
    """User bookmark / wishlist of places they want to visit."""
    __tablename__ = "saved_places"
    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_user_saved_place"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    place_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_places")
    place: Mapped["Place"] = relationship("Place", back_populates="saved_by_users")

    def __repr__(self) -> str:
        return f"<SavedPlace(user_id={self.user_id}, place_id={self.place_id})>"

