from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from app.api.router import api_router
    from app.core.config import settings
    from app.core.exceptions import (
        AppException,
        app_exception_handler,
        http_exception_handler,
        unhandled_exception_handler,
        validation_exception_handler,
    )
    from app.core.logger import logger
    from app.database.init_db import init_db, seed_sample_destinations
except ImportError:
    from backend.app.api.router import api_router
    from backend.app.core.config import settings
    from backend.app.core.exceptions import (
        AppException,
        app_exception_handler,
        http_exception_handler,
        unhandled_exception_handler,
        validation_exception_handler,
    )
    from backend.app.core.logger import logger
    from backend.app.database.init_db import init_db, seed_sample_destinations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    logger.info(f"Allowed CORS origins: {settings.CORS_ORIGINS}")
    
    # Initialize database tables and seed initial data
    try:
        init_db()
        seed_sample_destinations()
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}", exc_info=True)

    yield
    # Shutdown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # 1. CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Centralized Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 3. Mount API Routers
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Root endpoint for basic discovery
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "health": f"{settings.API_PREFIX}/health",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
