"""Main FastAPI Application for Kyro Backend.

Integrates REST API (/api/v1) and Socket.IO real-time server (/ws).
"""

import os
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1 import api_v1_router
from backend.app.realtime.server import sio_app

# Read CORS origins from environment
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000",
)
origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app = FastAPI(
    title="Kyro Backend API",
    description="Autonomous Healthcare Vendor Intelligence & Risk Assessment for Indian Hospitals",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """Liveness probe: verifies service availability."""
    return {
        "status": "ok",
        "db": False,  # Updated to True once P1 database session is initialized
        "redis": False,  # Updated to True once Redis client is initialized
        "version": "0.1.0",
        "service": "kyro-backend",
    }


# Mount API v1 router
app.include_router(api_v1_router)

# Mount Socket.IO realtime server at /ws
app.mount("/ws", sio_app)
