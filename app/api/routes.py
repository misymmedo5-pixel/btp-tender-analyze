import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel

from app.config import UPLOAD_DIR, SAMPLES_DIR, GEMINI_API_KEY
from app.models.tender import TenderAnalysis
from app.services.pdf_parser import PDFParser
from app.services.dpgf_parser import DPGFParser
from app.services.analyzer import TenderAnalyzerEngine
from app.services.exporter import DocumentExporter
from app.services.sample_data import (
    SAMPLE_1_CCTP_TEXT,
    SAMPLE_1_DPGF_ITEMS,
    SAMPLE_2_CCTP_TEXT,
    SAMPLE_2_DPGF_ITEMS,
    generate_sample_files_if_needed,
)

logger = logging.getLogger("btp.api")
router = APIRouter(prefix="/api")

# In-memory storage for active analyses
ANALYSIS_CACHE: Dict[str, TenderAnalysis] = {}

class LoadSampleRequest(BaseModel):
    sample_id: str = "1"
    gemini_api_key: Optional[str] = None

class ExportRequest(BaseModel):
    analysis: TenderAnalysis

@router.get("/status")
def get_system_status():
    """Returns engine capabilities, Gemini connectivity status, and version info."""
    api_key_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return {
        "status": "online",
        "engine": "BTP Public Tender Analyzer v2.0",
        "gemini_api_configured": api_key_set,
        "local_nlp_engine": "Active (AFNOR / CSTB / CCAG Travaux 2026)",
        "features": [
            "Analyse instantanée CCTP/CCAP (PDF)",
            "Extraction automatique bordereau DPGF/BPU (Excel/CSV)",
            "Score Go/No-Go 60s & Matrice des risques",
            "Simulateur de marges interactif",
            "Export PDF, Excel & CSV 100% autonome",
        ]
    }

@router.post("/upload", response_model=TenderAnalysis)
async def upload_and_analyze(
    cctp_file: UploadFile = File(..., description="Fichier PDF du CCTP ou CCAP"),
    dpgf_file: Optional[UploadFile] = File(None, description="Fichier Excel ou CSV de la DPGF"),
    gemini_api_key: Optional[str] = Form(None, description="Clé API Gemini optionnelle"),
):
    """
    Uploads CCTP PDF and optional DPGF Excel/CSV, parses both files, and produces a complete analysis.
    """
    if not cctp_file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Le fichier CCTP doit être au format PDF ou TXT.")

    cctp_path = UPLOAD_DIR / f"cctp_{cctp_file.filename}"
    try:
        with open(cctp_path, "wb") as buffer:
            shutil.copyfileobj(cctp_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde du CCTP: {e}")

    # Extract text from CCTP
    cctp_text = ""
    if cctp_path.suffix.lower() == ".pdf":
        try:
            pdf_data = PDFParser.extract_text_and_metadata(cctp_path)
            cctp_text = pdf_data["full_text"]
        except Exception as e:
            logger.error(f"Erreur d'extraction PDF: {e}")
            raise HTTPException(status_code=422, detail=f"Échec de l'extraction textuelle du PDF ({e})")
    else:
        try:
            with open(cctp_path, "r", encoding="utf-8", errors="ignore") as f:
                cctp_text = f.read()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Échec de lecture du fichier texte: {e}")

    # Parse DPGF if provided
    dpgf_items = []
    dpgf_filename = None
    if dpgf_file and dpgf_file.filename:
        dpgf_filename = dpgf_file.filename
        dpgf_path = UPLOAD_DIR / f"dpgf_{dpgf_file.filename}"
        try:
            with open(dpgf_path, "wb") as buffer:
                shutil.copyfileobj(dpgf_file.file, buffer)
            dpgf_items = DPGFParser.parse_pricing_grid(dpgf_path)
        except Exception as e:
            logger.warning(f"Erreur lors du traitement du fichier DPGF ({e}). Poursuite de l'analyse sans DPGF.")

    # Execute analysis engine
    analysis = TenderAnalyzerEngine.analyze(
        cctp_text=cctp_text,
        dpgf_items=dpgf_items,
        filename_cctp=cctp_file.filename,
        filename_dpgf=dpgf_filename,
        gemini_api_key=gemini_api_key,
    )

    ANALYSIS_CACHE[analysis.id] = analysis
    return analysis

@router.post("/load-sample", response_model=TenderAnalysis)
async def load_sample(req: LoadSampleRequest):
    """
    Loads pre-built realistic French BTP public tender examples for instant demo.
    """
    if req.sample_id == "2":
        analysis = TenderAnalyzerEngine.analyze(
            cctp_text=SAMPLE_2_CCTP_TEXT,
            dpgf_items=SAMPLE_2_DPGF_ITEMS,
            filename_cctp="CCTP_Platrerie_Acoustique_Mediatheque.pdf",
            filename_dpgf="DPGF_Lot04_Platrerie.xlsx",
            gemini_api_key=req.gemini_api_key,
        )
    else:
        analysis = TenderAnalyzerEngine.analyze(
            cctp_text=SAMPLE_1_CCTP_TEXT,
            dpgf_items=SAMPLE_1_DPGF_ITEMS,
            filename_cctp="CCTP_Renov_Electrique_Ecole_Pasteur.pdf",
            filename_dpgf="DPGF_Lot02_Electricite.xlsx",
            gemini_api_key=req.gemini_api_key,
        )

    ANALYSIS_CACHE[analysis.id] = analysis
    return analysis

@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    """Generates and returns an executive PDF report."""
    try:
        pdf_bytes = DocumentExporter.generate_pdf(req.analysis)
        filename = f"Synthese_AO_{req.analysis.id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/pdf",
            },
        )
    except Exception as e:
        logger.error(f"Erreur génération PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du PDF: {e}")

@router.post("/export/excel")
async def export_excel(req: ExportRequest):
    """Generates and returns an Excel workbook (.xlsx)."""
    try:
        xlsx_bytes = DocumentExporter.generate_excel(req.analysis)
        filename = f"Chiffrage_DPGF_{req.analysis.id}.xlsx"
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        )
    except Exception as e:
        logger.error(f"Erreur génération Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du fichier Excel: {e}")

@router.post("/export/csv")
async def export_csv(req: ExportRequest):
    """Generates and returns a semicolon-separated CSV of the DPGF items."""
    try:
        csv_str = DocumentExporter.generate_csv(req.analysis)
        filename = f"DPGF_Lignes_{req.analysis.id}.csv"
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    except Exception as e:
        logger.error(f"Erreur génération CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur CSV: {e}")
