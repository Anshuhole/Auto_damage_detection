import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.database import engine, Base
from app.routes import predict, history, report, stats

# Create Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AutoInspect AI - Backend API",
    description="Intelligent Vehicle Damage Detection, Grad-CAM Localization, and Repair Cost Estimation API",
    version="1.0.0"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for serving uploaded images and generated reports
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API Routers
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(report.router)
app.include_router(stats.router)

@app.get("/")
def root():
    return {
        "service": "AutoInspect AI",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": [
            "/api/predict",
            "/api/predict/base64",
            "/api/history",
            "/api/report/{id}/pdf",
            "/api/stats"
        ]
    }

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "AutoInspect AI API"}
