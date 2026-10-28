from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import (
    APP_NAME,
    APP_DESCRIPTION,
    APP_VERSION,
    STATIC_DIR,
    TEMPLATES_DIR,
    SAMPLES_DIR,
)
from app.api.routes import router as api_router
from app.services.sample_data import generate_sample_files_if_needed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("btp.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure sample test files are created
    try:
        generate_sample_files_if_needed(SAMPLES_DIR)
        logger.info(f"Fichiers d'exemples BTP initialisés dans {SAMPLES_DIR}")
    except Exception as e:
        logger.warning(f"Impossible de pré-générer les fichiers exemples: {e}")
    yield

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API endpoints
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse)
async def root_view(request: Request):
    """Renders the main application with landing page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "initial_view": "landing",
        },
    )

@app.get("/app", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Renders directly the artisan dashboard workspace."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "initial_view": "dashboard",
        },
    )
