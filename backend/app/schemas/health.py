from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(
        default="success",
        description="Health status indicator",
        examples=["success"]
    )
    message: str = Field(
        default="TravelSenseAI backend is running",
        description="Detailed status message",
        examples=["TravelSenseAI backend is running"]
    )

