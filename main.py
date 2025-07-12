from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from routes.auth import router as auth_router
from routes.question import router as question_router
from routes.answer import router as answer_router
from routes.notification import router as notification_router
from database import Database

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    Database.initialize()
    yield
    # Shutdown
    print("Shutting down...")
    Database.close_connection()

# Create FastAPI app
app = FastAPI(
    title="GAN-ster API",
    description="A FastAPI application with user authentication and AI-powered features",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware - Allow frontend on port 8080
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Frontend development server
        "http://127.0.0.1:8080",
        "http://localhost:3000",  # Alternative frontend port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(question_router)
app.include_router(answer_router)
app.include_router(notification_router)

# Serve static files from frontend build (when available)
frontend_build_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_build_path):
    app.mount("/static", StaticFiles(directory=frontend_build_path), name="static")
    
    # Serve frontend index.html for all routes not starting with /api
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # API routes should not serve the frontend
        if path.startswith("api/") or path in ["docs", "redoc", "openapi.json"]:
            return {"error": "Not found"}
        
        # Serve index.html for frontend routes
        index_file = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to GAN-ster API", "frontend_available": os.path.exists(frontend_build_path)}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "GAN-ster API",
        "database": Database.get_connection_status(),
        "atlas_connected": Database.is_connected_to_atlas()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)