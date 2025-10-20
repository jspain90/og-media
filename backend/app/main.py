from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.routers import channels, sources, player

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("Initializing database...")
    init_db()

    print("Starting background scheduler...")
    start_scheduler()

    yield

    # Shutdown
    print("Stopping background scheduler...")
    stop_scheduler()

app = FastAPI(
    title="OG Media API",
    description="Backend API for the OG Media YouTube channel player",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://localhost:3000",
        "https://media.galahad.cc",  # Cloudflare tunnel frontend
        "https://media-api.galahad.cc",  # Cloudflare tunnel backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(channels.router)
app.include_router(sources.router)
app.include_router(player.router)

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "OG Media API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
