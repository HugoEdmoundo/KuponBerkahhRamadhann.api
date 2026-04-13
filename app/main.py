from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine
from .models import Base
from .routers import periodes, registrations, queue_settings, queue_management

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Queue Management API",
    version="1.0.0",
    # docs_url="/docs",  # Default Swagger UI
    # redoc_url="/redoc",  # Default ReDoc
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(periodes.router)
app.include_router(registrations.router)
app.include_router(queue_settings.router)
app.include_router(queue_management.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Queue Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
