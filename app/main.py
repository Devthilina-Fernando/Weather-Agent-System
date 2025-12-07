"""Main FastAPI application"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.weather import router as weather_router
from app.routes.agent import router as agent_router
from app.scheduler import weather_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Weather Pipeline Application")
    await weather_scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Weather Pipeline Application")
    await weather_scheduler.shutdown()


# Create FastAPI application
app = FastAPI(
    title="Weather Data Pipeline API",
    description="API for fetching and storing weather data from OpenWeatherMap",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(weather_router)
app.include_router(agent_router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "Weather Data Pipeline",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)