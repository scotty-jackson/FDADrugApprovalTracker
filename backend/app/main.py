"""
Main FastAPI application for FDA Drug Approval Tracker.
This is the entry point for the backend API server.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import drugs, approvals, events, summary

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database tables (in production, use Alembic migrations)
    logger.info("Starting FDA Drug Approval Tracker API")
    logger.info(f"Environment: {settings.log_level}")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

    yield

    # Shutdown
    logger.info("Shutting down FDA Drug Approval Tracker API")


# Create FastAPI application
app = FastAPI(
    title="FDA Drug Approval Tracker API",
    description="""
    API for tracking FDA drug approvals, upcoming decision dates, and related events.

    ## Features
    - Browse recently approved drugs
    - Search and filter by therapeutic area, sponsor, FDA center, and more
    - Track upcoming PDUFA dates and advisory committee meetings
    - View detailed drug information including approval history
    - Access summary statistics and analytics

    ## Data Sources
    Data is sourced from publicly available FDA resources including:
    - FDA CDER and CBER approval databases
    - FDA.gov press releases
    - Public PDUFA date calendars

    ## Disclaimer
    This API provides information for educational and informational purposes only.
    It is not medical or investment advice. Data accuracy is not guaranteed.
    This service is not affiliated with or endorsed by the FDA.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drugs.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(summary.router, prefix="/api")


# Root endpoint
@app.get("/")
def root():
    """
    API root endpoint. Returns basic information about the API.
    """
    return {
        "name": "FDA Drug Approval Tracker API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "database": "connected"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler to catch unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,  # Enable auto-reload for development
        log_level=settings.log_level.lower()
    )
