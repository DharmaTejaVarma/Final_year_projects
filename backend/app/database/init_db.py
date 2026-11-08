try:
    from app.core.logger import logger
    from app.database.base import Base
    from app.database.connection import SessionLocal, engine
    # Import all models to ensure they are registered with Base.metadata
    from app.models import (
        Destination,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
        Place,
        AttractionImageCache,
        Review,
        SavedPlace,
        Trip,
        TripPreference,
        User,
        UserPreference,
    )
except ImportError:
    from backend.app.core.logger import logger
    from backend.app.database.base import Base
    from backend.app.database.connection import SessionLocal, engine
    from backend.app.models import (
        Destination,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
        Place,
        AttractionImageCache,
        Review,
        SavedPlace,
        Trip,
        TripPreference,
        User,
        UserPreference,
    )


def init_db() -> None:
    """Create all database tables defined in SQLAlchemy models."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # Safe SQLite column migration for places table
    try:
        with engine.connect() as conn:
            # Check existing columns on places
            res = conn.exec_driver_sql("PRAGMA table_info(places)").fetchall()
            col_names = [r[1] for r in res] if res else []
            if "image_attribution" not in col_names and col_names:
                conn.exec_driver_sql("ALTER TABLE places ADD COLUMN image_attribution VARCHAR(300)")
            if "image_verified" not in col_names and col_names:
                conn.exec_driver_sql("ALTER TABLE places ADD COLUMN image_verified BOOLEAN DEFAULT 1")
            conn.commit()
    except Exception as e:
        logger.debug(f"Column migration check note: {e}")

    logger.info("Database schema initialized successfully.")


def seed_sample_destinations() -> None:
    """Seed initial sample destination and attraction data if table is empty."""
    db = SessionLocal()
    try:
        if db.query(Destination).first() is None:
            logger.info("Seeding initial destination and place data...")
            
            dest_tokyo = Destination(
                name="Tokyo",
                country="Japan",
                latitude=35.6762,
                longitude=139.6503,
                description="A vibrant metropolis fusing ultramodern technology with historic temples.",
            )
            dest_paris = Destination(
                name="Paris",
                country="France",
                latitude=48.8566,
                longitude=2.3522,
                description="The City of Light, famed for haute cuisine, art museums, and iconic monuments.",
            )
            db.add_all([dest_tokyo, dest_paris])
            db.flush()

            place_sensoji = Place(
                destination_id=dest_tokyo.id,
                name="Senso-ji Temple",
                category="Cultural & Historical",
                description="Tokyo's oldest and most significant ancient Buddhist temple located in Asakusa.",
                latitude=35.7148,
                longitude=139.7967,
                address="2-3-1 Asakusa, Taito City, Tokyo",
                estimated_visit_duration=90,
                opening_hours="06:00 - 17:00",
                entrance_fee=0.0,
                source="internal",
            )
            place_louvre = Place(
                destination_id=dest_paris.id,
                name="Louvre Museum",
                category="Art & Museum",
                description="The world's largest art museum and historic landmark home to the Mona Lisa.",
                latitude=48.8606,
                longitude=2.3376,
                address="Rue de Rivoli, 75001 Paris, France",
                estimated_visit_duration=180,
                opening_hours="09:00 - 18:00",
                entrance_fee=17.0,
                source="internal",
            )
            db.add_all([place_sensoji, place_louvre])
            db.commit()
            logger.info("Sample destinations and places seeded successfully.")
    except Exception as e:
        logger.error(f"Error seeding initial database data: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_sample_destinations()

