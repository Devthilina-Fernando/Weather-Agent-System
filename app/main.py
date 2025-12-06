import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from app.config import get_settings
from app.api.routes import router
from app.services.database import BigQueryService
from app.orchestration.scheduler import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/app.log')
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Weather Agent System")
    
    try:
        # Initialize BigQuery schema
        logger.info("Initializing BigQuery schema")
        db_service = BigQueryService()
        db_service.initialize_schema()
        
        # Initialize scheduler
        logger.info("Initializing scheduler")
        SchedulerService.initialize()
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Weather Agent System")


# Create FastAPI application
app = FastAPI(
    title="Weather Agent System",
    description="Agentic Data Pipeline & AI Workflow for Weather Data",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["weather"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "service": "Weather Agent System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/v1/health",
            "current_weather": "/api/v1/weather/current/{city}",
            "weather_history": "/api/v1/weather/history/{city}",
            "average_temperature": "/api/v1/weather/average/{city}",
            "all_cities": "/api/v1/weather/cities",
            "agent_chat": "/api/v1/agent/chat",
            "docs": "/docs",
            "metrics": "/metrics"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.app_env != "production" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env != "production",
        workers=4 if settings.app_env == "production" else 1
    )