"""
KIVI Backend - FastAPI Application

Purpose:
    Main FastAPI application for KIVI hackathon project. Provides REST API
    endpoints for WhatsApp integration, AI chat, financial transaction tracking,
    and user profile management for gig workers.

Architecture:
    - FastAPI web framework with async/await
    - MongoDB with Motor async driver
    - JWT authentication
    - Pluggable AI providers (OpenAI, Anthropic)
    - WhatsApp Cloud API integration

Features:
    - WhatsApp webhook handling
    - AI-powered chat (mobile app + WhatsApp)
    - SMS transaction parsing and categorization
    - Financial dashboard and reports
    - User profile management
    - Proactive notifications

Dependencies:
    - fastapi: Web framework
    - uvicorn: ASGI server
    - motor: Async MongoDB driver
    - pydantic: Data validation
    - httpx: Async HTTP client
    - pyjwt: JWT token handling

Usage:
    # Development
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    # Production
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

Reference:
    Project Brief: /mnt/data/MumbaiHacks 2025.pdf
    Requirements: 12.3, 12.4
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import configuration and logging
from app.config.logging_config import setup_logging, logger
from app.db.mongodb import connect_db, close_db

# Import route modules
from app.api.v1 import routes_auth
from app.api.v1 import routes_user
from app.api.v1 import routes_finance
from app.api.v1 import routes_whatsapp
from app.api.v1 import routes_ai

# Import exception handling
from app.core.exceptions import (
    KiviException,
    kivi_exception_to_http
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize logging and database connection
    - Shutdown: Close database connection
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("=" * 60)
    logger.info("KIVI Backend Starting Up")
    logger.info("=" * 60)
    
    # Initialize logging
    setup_logging()
    logger.info("Logging configured successfully")
    
    # Connect to database
    try:
        await connect_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise
    
    logger.info("KIVI Backend ready to accept requests")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("KIVI Backend Shutting Down")
    logger.info("=" * 60)
    
    # Close database connection
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}", exc_info=True)
    
    logger.info("KIVI Backend shutdown complete")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title="KIVI Backend API",
    description=(
        "AI-powered financial management platform for gig workers. "
        "Provides WhatsApp integration, SMS transaction parsing, "
        "AI chat capabilities, and financial insights."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Alternative dev port
        "https://kivi-app.vercel.app",  # Production mobile app (example)
        "*"  # Allow all origins for hackathon (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Include route modules
app.include_router(routes_auth.router)
app.include_router(routes_user.router)
app.include_router(routes_finance.router)
app.include_router(routes_whatsapp.router)
app.include_router(routes_ai.router)


# Import response models
from app.core.response_models import success_response, error_response, ResponseCode


# Root endpoint
@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> dict:
    """
    Root endpoint providing API information.
    
    Returns basic information about the KIVI Backend API including
    project name, description, version, and reference to project brief.
    
    Returns:
        dict: Standardized API information response
    """
    return success_response(
        data={
            "project": "KIVI Backend",
            "description": "AI-powered financial management for gig workers",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
            "project_brief": "/mnt/data/MumbaiHacks 2025.pdf",
            "features": [
                "WhatsApp integration",
                "AI chat (OpenAI, Anthropic)",
                "SMS transaction parsing",
                "Financial dashboard and reports",
                "User profile management",
                "Proactive notifications"
            ],
            "target_audience": "Gig workers with uncertain income streams"
        },
        message="KIVI Backend API is running",
        code=ResponseCode.SUCCESS
    )


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns service health status for monitoring and load balancers.
    
    Returns:
        dict: Standardized health status response
    """
    return success_response(
        data={
            "status": "healthy",
            "service": "kivi-backend",
            "timestamp": "2025-11-24T15:06:21Z"
        },
        message="Service is healthy",
        code=ResponseCode.SUCCESS
    )


# Global exception handler for KIVI custom exceptions
@app.exception_handler(KiviException)
async def kivi_exception_handler(request: Request, exc: KiviException) -> JSONResponse:
    """
    Global exception handler for KIVI custom exceptions.
    
    Converts KIVI custom exceptions to appropriate HTTP responses.
    Logs the exception with full context for debugging.
    
    Args:
        request: FastAPI request object
        exc: KIVI custom exception
    
    Returns:
        JSONResponse with error details
    """
    logger.error(
        f"KIVI exception in {request.method} {request.url.path}: {exc.message}",
        exc_info=True
    )
    
    # Convert to HTTP exception
    http_exc = kivi_exception_to_http(exc)
    
    # Map HTTP status to response code
    code_map = {
        400: ResponseCode.BAD_REQUEST,
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        409: ResponseCode.CONFLICT,
        500: ResponseCode.INTERNAL_ERROR
    }
    
    response_code = code_map.get(http_exc.status_code, ResponseCode.INTERNAL_ERROR)
    
    return JSONResponse(
        status_code=http_exc.status_code,
        content=error_response(
            message=http_exc.detail,
            code=response_code,
            error_type=exc.__class__.__name__
        )
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unexpected errors.
    
    Catches all unhandled exceptions and returns a generic 500 error.
    Logs the full exception traceback for debugging.
    
    Args:
        request: FastAPI request object
        exc: Unhandled exception
    
    Returns:
        JSONResponse with generic error message
    """
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="An unexpected error occurred",
            code=ResponseCode.INTERNAL_ERROR,
            error_type=type(exc).__name__,
            details=str(exc) if logger.level == 10 else None  # DEBUG level
        )
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests.
    
    Logs request method, path, and response status code.
    Useful for debugging and monitoring.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler
    
    Returns:
        Response from next handler
    """
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"-> {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(
            f"Request failed: {request.method} {request.url.path} -> {e}",
            exc_info=True
        )
        raise


if __name__ == "__main__":
    import uvicorn
    
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
