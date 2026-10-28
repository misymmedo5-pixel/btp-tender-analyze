import os
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

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

PUBLIC_ACCESS_ENABLED = os.getenv("ENABLE_PUBLIC_ACCESS", "false").lower() in ("true", "1", "yes")
ACCESS_PASSCODE = os.getenv("ACCESS_PASSCODE", "btp2026")
AUTH_COOKIE_NAME = "btp_private_access"

def build_locked_html():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accès Public Désactivé | BTP Public Tender Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0F172A] text-slate-100 min-h-screen flex items-center justify-center p-4 antialiased selection:bg-orange-500 selection:text-white font-sans">
    <div class="max-w-md w-full bg-slate-800/90 border border-slate-700/80 rounded-2xl p-8 text-center space-y-6 shadow-2xl backdrop-blur">
        <div class="w-16 h-16 rounded-2xl bg-orange-500/10 border border-orange-500/20 text-[#EA580C] mx-auto flex items-center justify-center">
            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
        </div>
        
        <div class="space-y-2">
            <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-semibold">
                <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                <span>Mode Privé Actif</span>
            </div>
            <h1 class="text-xl font-extrabold text-white">Accès Public Désactivé</h1>
            <p class="text-xs sm:text-sm text-slate-400 leading-relaxed">
                Le site est actuellement fermé au public par l'administrateur. Les services et analyses ne sont pas accessibles pour le moment.
            </p>
        </div>

        <form method="GET" action="/" class="pt-2 space-y-3">
            <div class="relative">
                <input type="password" name="passcode" placeholder="Code d'accès administrateur..." required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 font-mono focus:border-[#EA580C] focus:outline-none focus:ring-1 focus:ring-[#EA580C]">
            </div>
            <button type="submit" class="w-full py-2.5 rounded-xl bg-[#EA580C] hover:bg-[#C2410C] text-white font-bold text-xs uppercase tracking-wider transition-all shadow-md">
                Déverrouiller l'accès
            </button>
        </form>

        <div class="pt-4 border-t border-slate-700/60 text-[11px] text-slate-500">
            <span>BTP Public Tender Analyzer • Accès Restreint</span>
        </div>
    </div>
</body>
</html>"""

@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def public_access_guard(request: Request, call_next):
    if PUBLIC_ACCESS_ENABLED:
        return await call_next(request)

    path = request.url.path
    if path.startswith("/static"):
        return await call_next(request)

    passcode_param = request.query_params.get("passcode")
    cookie_val = request.cookies.get(AUTH_COOKIE_NAME)

    if passcode_param == ACCESS_PASSCODE or cookie_val == ACCESS_PASSCODE:
        response = await call_next(request)
        if passcode_param == ACCESS_PASSCODE:
            response.set_cookie(key=AUTH_COOKIE_NAME, value=ACCESS_PASSCODE, max_age=86400 * 30, httponly=True)
        return response

    if path.startswith("/api"):
        return JSONResponse(
            status_code=403,
            content={"detail": "Accès public désactivé (Site en mode privé)."}
        )

    return HTMLResponse(content=build_locked_html(), status_code=403)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

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
