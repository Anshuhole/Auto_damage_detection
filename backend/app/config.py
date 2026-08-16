import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    STATIC_DIR = Path("/tmp/static")
    DATABASE_URL = "sqlite:////tmp/autoinspect.db"
else:
    STATIC_DIR = BASE_DIR / "static"
    DATABASE_URL = f"sqlite:///{BASE_DIR}/autoinspect.db"

UPLOAD_DIR = STATIC_DIR / "uploads"
GRADCAM_DIR = STATIC_DIR / "gradcam"
REPORT_DIR = STATIC_DIR / "reports"
WEIGHTS_DIR = BASE_DIR / "app" / "ml" / "weights"

for folder in [STATIC_DIR, UPLOAD_DIR, GRADCAM_DIR, REPORT_DIR, WEIGHTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Model Configuration
MODEL_NAME = "resnet50"
MODEL_WEIGHTS_PATH = WEIGHTS_DIR / "car_damage_resnet50.pth"
DEVICE = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"

# Damage Classes
DAMAGE_CLASSES = [
    "scratch",
    "dent",
    "crack",
    "shattered_glass",
    "no_damage"
]

DAMAGE_DISPLAY_NAMES = {
    "scratch": "Surface Scratch / Paint Scrape",
    "dent": "Panel Dent / Body Deformation",
    "crack": "Bumper / Panel Crack",
    "shattered_glass": "Shattered / Broken Glass",
    "no_damage": "No Visible Damage Detected"
}

SEVERITY_LEVELS = ["minor", "moderate", "severe", "none"]

# Base Repair Cost Matrix (Rule-Based Industry Estimates in USD)
COST_ESTIMATE_MATRIX = {
    "scratch": {
        "minor": {"min": 120, "max": 280, "labor_hours": 1.5, "paint": 100, "parts": 0, "desc": "Buffing, touch-up polish, clear coat blend"},
        "moderate": {"min": 300, "max": 650, "labor_hours": 3.0, "paint": 250, "parts": 50, "desc": "Deep scratch sanding, primer, base coat + clear coat refinishing"},
        "severe": {"min": 700, "max": 1400, "labor_hours": 5.5, "paint": 500, "parts": 150, "desc": "Multi-panel deep gouge repair and complete re-spray"}
    },
    "dent": {
        "minor": {"min": 150, "max": 350, "labor_hours": 2.0, "paint": 0, "parts": 0, "desc": "Paintless Dent Repair (PDR) localized massage"},
        "moderate": {"min": 400, "max": 950, "labor_hours": 4.5, "paint": 250, "parts": 100, "desc": "Panel pulling, body filler, localized paint blend"},
        "severe": {"min": 1100, "max": 2800, "labor_hours": 8.0, "paint": 600, "parts": 650, "desc": "Structural crease repair or complete panel replacement"}
    },
    "crack": {
        "minor": {"min": 200, "max": 450, "labor_hours": 2.5, "paint": 120, "parts": 50, "desc": "Plastic welding repair, reinforcement mesh, spot paint"},
        "moderate": {"min": 500, "max": 1100, "labor_hours": 4.0, "paint": 300, "parts": 250, "desc": "Bumper/trim fracture heat bonding, primer, full panel spray"},
        "severe": {"min": 1200, "max": 3200, "labor_hours": 7.0, "paint": 550, "parts": 900, "desc": "OEM bumper cover/body panel replacement and alignment"}
    },
    "shattered_glass": {
        "minor": {"min": 180, "max": 350, "labor_hours": 1.5, "paint": 0, "parts": 150, "desc": "Quarter glass / side window replacement + seal"},
        "moderate": {"min": 400, "max": 850, "labor_hours": 2.5, "paint": 0, "parts": 400, "desc": "OEM windshield replacement + ADAS sensor calibration"},
        "severe": {"min": 900, "max": 2200, "labor_hours": 4.5, "paint": 0, "parts": 1100, "desc": "Panoramic sunroof / rear heated glass assembly & framing"}
    },
    "no_damage": {
        "none": {"min": 0, "max": 0, "labor_hours": 0, "paint": 0, "parts": 0, "desc": "Vehicle body in sound condition. No repairs required."}
    }
}
