from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import demo, auth, home, transactions, goals, profile, notifications, insights, utilities
from app.config.firebase import initialize_firebase, init_firestore
from app.config.mongodb import connect_to_mongodb, close_mongodb_connection
from app.config.gemini import initialize_gemini
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize Firebase and MongoDB
    logger.info("Initializing Firebase...")
    initialize_firebase()
    logger.info("Firebase initialized successfully")
    
    logger.info("Initializing Firestore...")
    init_firestore()
    logger.info("Firestore initialized successfully")
    
    logger.info("Connecting to MongoDB...")
    await connect_to_mongodb()
    logger.info("MongoDB connected successfully")
    
    logger.info("Initializing Gemini AI...")
    initialize_gemini()
    logger.info("Gemini AI initialized successfully")
    
    yield
    
    # Shutdown: Close MongoDB connection
    logger.info("Shutting down...")
    await close_mongodb_connection()


app = FastAPI(
    title="Finweave AI Backend",
    description="Backend API for Finweave AI financial management app",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(profile.router)
app.include_router(notifications.router)
app.include_router(insights.router)
app.include_router(utilities.router)
app.include_router(demo.router)


@app.get("/")
def root():
    return {
        "message": "Finweave AI Backend is running!",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "firebase": "connected",
        "mongodb": "connected",
        "gemini_ai": "initialized",
        "api": "operational"
    }
