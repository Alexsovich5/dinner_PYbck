from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api.v1.routers import auth, matches, profiles, users
from app.core.database import Base, engine
from app.middleware.middleware import log_requests_middleware

# Create database tables
Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Dinner App API",
    description="API for matching dinner companions",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.middleware("http")(log_requests_middleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    profiles.router,
    prefix="/api/v1/profiles",
    tags=["profiles"]
)
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])


@app.get("/")
async def root():
    """
    Root endpoint to verify API is running
    """
    return {
        "status": "ok",
        "message": "Welcome to the Dinner App API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "database": "connected"
    }
