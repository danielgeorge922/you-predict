"""
Health check endpoints for monitoring system status.

These endpoints help you verify that all system components
are working correctly. Essential for production monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import redis
import structlog

# TODO: setthis up when db ready
# from src.utils.database import get_db, db_manager

from src.config.settings import settings

logger = structlog.get_logger()

# Create router for health endpoints
router = APIRouter()


@router.get("/")
async def health_check():
    """
    Check if server is even running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "youtube-view-predictor",
        "version": "1.0.0"
    }

# this is essentially at the endpoint /health/database
# TODO: Uncomment when database setup is ready

# @router.get("/database")
# async def database_health(db: Session = Depends(get_db)):
    """
    Check database connectivity and basic operations.
    
    This verifies:
    1. Can connect to PostgreSQL
    2. Can execute simple queries
    3. Database is responding normally
    """
    try:
        # Simple query to test database
        result = db.execute("SELECT 1 as test_value")
        test_value = result.fetchone()
        
        if test_value and test_value[0] == 1:
            return {
                "status": "healthy",
                "database": "postgresql",
                "connection": "ok",
                "timestamp": datetime.utcnow()
            }
        else:
            raise Exception("Unexpected query result")
            
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "postgresql", 
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )


@router.get("/redis")
async def redis_health():
    """
    Check Redis connectivity and basic operations.
    
    Redis is used for:
    - Caching predictions
    - Celery task queue
    - Session storage
    """
    try:
        # Connect to Redis
        redis_client = redis.from_url(settings.redis_url)
        
        # Test basic operations
        test_key = "health_check_test"
        test_value = f"test_{datetime.utcnow().timestamp()}"
        
        # Set and get a test value
        redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = redis_client.get(test_key)
        
        if retrieved_value and retrieved_value.decode() == test_value:
            # Clean up test key
            redis_client.delete(test_key)
            
            return {
                "status": "healthy",
                "redis": "ok",
                "operations": ["set", "get", "delete"],
                "timestamp": datetime.utcnow()
            }
        else:
            raise Exception("Redis operations failed")
            
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "redis": "error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )


# TODO: Uncomment when comprehensive health check is ready

# @router.get("/comprehensive")
# async def comprehensive_health(db: Session = Depends(get_db)):
#     """
#     Comprehensive health check of all system components.
    
#     This checks:
#     - API server
#     - Database connectivity
#     - Redis connectivity  
#     - Configuration validity
#     - System resources (basic)
#     """
#     health_results = {
#         "timestamp": datetime.utcnow(),
#         "overall_status": "healthy",
#         "components": {}
#     }
    
#     # Check API server (if we're here, it's working)
#     health_results["components"]["api"] = {
#         "status": "healthy",
#         "details": "FastAPI server responding"
#     }
    
#     # Check database
#     try:
#         result = db.execute("SELECT 1")
#         result.fetchone()
#         health_results["components"]["database"] = {
#             "status": "healthy",
#             "details": "PostgreSQL connection OK"
#         }
#     except Exception as e:
#         health_results["components"]["database"] = {
#             "status": "unhealthy",
#             "details": f"Database error: {str(e)}"
#         }
#         health_results["overall_status"] = "degraded"
    
#     # Check Redis
#     try:
#         redis_client = redis.from_url(settings.redis_url)
#         redis_client.ping()
#         health_results["components"]["redis"] = {
#             "status": "healthy",
#             "details": "Redis connection OK"
#         }
#     except Exception as e:
#         health_results["components"]["redis"] = {
#             "status": "unhealthy", 
#             "details": f"Redis error: {str(e)}"
#         }
#         health_results["overall_status"] = "degraded"
    
#     # Check configuration
#     try:
#         # Basic config validation
#         assert settings.api_port > 0
#         assert settings.database_url
#         assert settings.redis_url
        
#         health_results["components"]["configuration"] = {
#             "status": "healthy",
#             "details": "All required settings present"
#         }
#     except Exception as e:
#         health_results["components"]["configuration"] = {
#             "status": "unhealthy",
#             "details": f"Configuration error: {str(e)}"
#         }
#         health_results["overall_status"] = "degraded"
    
#     # Return appropriate status code
#     if health_results["overall_status"] == "unhealthy":
#         raise HTTPException(status_code=503, detail=health_results)
#     elif health_results["overall_status"] == "degraded":
#         raise HTTPException(status_code=207, detail=health_results)  # Multi-status
    
#     return health_results


@router.get("/metrics")
async def basic_metrics():
    """
    Basic system metrics for monitoring.
    
    In production, you'd integrate with Prometheus here.
    For now, returns basic information about the system.
    """
    import psutil
    import os
    
    try:
        # Get basic system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.utcnow(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "process": {
                "pid": os.getpid(),
                "python_version": f"{psutil.version_info}",
            },
            "application": {
                "name": "youtube-view-predictor",
                "version": "1.0.0",
                "environment": "development"  # TODO: Get from env var
            }
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )