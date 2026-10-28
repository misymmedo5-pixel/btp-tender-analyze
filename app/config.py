import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
SAMPLES_DIR = STATIC_DIR / "samples"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure runtime directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Application metadata
APP_NAME = "BTP Public Tender Analyzer"
APP_DESCRIPTION = "Analyseur d'Appels d'Offres BTP pour Artisans & Entreprises de Travaux"
APP_VERSION = "2.0.0"

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# File upload constraints
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_CCTP_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_DPGF_EXTENSIONS = {".xlsx", ".xls", ".csv"}
