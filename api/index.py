import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path for module resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Mark environment as Vercel serverless
os.environ["VERCEL"] = "1"

from app.main import app
