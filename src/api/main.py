from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import structlog
from contextlib import asynccontextmanager


from src.api.routes import health
# TODO: Import these as we build them
# from src.api.routes import predictions, channels, metrics
from src.config.settings import settings

# TODO: Import when ready
# from src.utils.database import db_manager

# Set up structured logging
logger = structlog.get_logger()

# ////////////////////////////////////////////////////////////////////////////////////////////////////
# Everything here runs on startup (before yield), when closing everything runs after yield
# ////////////////////////////////////////////////////////////////////////////////////////////////////

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting YouTube View Predictor API...")
    
    # Initialize database

    # TODO: Uncomment when database setup is ready
    # if not db_manager.health_check():
    #     logger.error("Database connection failed!")
    #     raise Exception("Cannot start without database")
    
    # TODO: Load ML models into memory here
    # model_manager.load_latest_model()
    
    logger.info("API startup complete!")
    
    yield  # This is where the app runs
    
    # Shutdown events
    logger.info("Shutting down API...")
    # TODO: Clean up resources, close connections
    logger.info("API shutdown complete!")

# //////////////////////
# Config inital setup
# //////////////////////

app = FastAPI(
    title="YouTube View Predictor API",
    description="""
    A machine learning API that predicts YouTube video view counts.
    
    ## Features
    * Predict 24-hour view counts for new videos
    * Track model performance and drift
    * Manage YouTube channel monitoring
    * Real-time predictions with caching
    
    ## Usage
    1. Add YouTube channels to track
    2. Get predictions for new videos
    3. Monitor model performance over time
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
    lifespan=lifespan
)

# Add CORS middleware (allows web browsers to call your API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (security)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # In production, specify exact hosts
)


# Custom middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information.
    
    This helps you monitor API performance and debug issues.
    """
    start_time = time.time()
    
    # Log the incoming request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    # Process the request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log the response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time_seconds=round(process_time, 3)
    )
    
    # Add timing header to response
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors gracefully.
    
    Instead of crashing, return a proper error response.
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": id(request)  # Simple request ID for debugging
        }
    )


# Include route modules (only health for now)
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health Check"]
)

# TODO: Add these as we build them
# app.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
# app.include_router(channels.router, prefix="/channels", tags=["Channel Management"])  
# app.include_router(metrics.router, prefix="/metrics", tags=["Model Metrics"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Welcome endpoint - shows basic API information.
    """
    return {
        "message": "Welcome to YouTube View Predictor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# This allows running the app directly with: python -m src.api.main
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,  # Auto-reload on code changes (development only)
        log_level=settings.log_level.lower()
    )