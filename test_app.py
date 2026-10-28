import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

curr_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(curr_dir))

from app.config import SAMPLES_DIR
from app.services.sample_data import generate_sample_files_if_needed
from app.services.pdf_parser import PDFParser
from app.services.dpgf_parser import DPGFParser
from app.services.analyzer import TenderAnalyzerEngine
from app.services.exporter import DocumentExporter
from app.api.routes import get_system_status

def run_tests():
    print("=== Démarrage des tests BTP Tender Analyzer ===", flush=True)

    # 1. Generate sample files
    generate_sample_files_if_needed(SAMPLES_DIR)
    pdf1 = SAMPLES_DIR / "CCTP_Electricite_Ecole_Pasteur.pdf"
    xlsx1 = SAMPLES_DIR / "DPGF_Electricite_Ecole_Pasteur.xlsx"
    pdf2 = SAMPLES_DIR / "CCTP_Platrerie_Mediatheque.pdf"
    xlsx2 = SAMPLES_DIR / "DPGF_Platrerie_Mediatheque.xlsx"
    assert pdf1.exists() and xlsx1.exists() and pdf2.exists() and xlsx2.exists(), "Fichiers exemples manquants"
    print("✅ 1. Génération des fichiers de démonstration BTP : OK", flush=True)

    # 2. Test status API
    status = get_system_status()
    assert status["status"] == "online"
    assert "features" in status and len(status["features"]) > 0
    print(f"✅ 2. API Status : OK ({status['engine']})", flush=True)

    # 3. Test PDF extraction
    pdf_res = PDFParser.extract_text_and_metadata(pdf1)
    assert len(pdf_res["full_text"]) > 500
    print(f"✅ 3. Extraction PDF (PyMuPDF) : OK ({len(pdf_res['full_text'])} caractères extraits)", flush=True)

    # 4. Test Excel DPGF extraction
    dpgf_items = DPGFParser.parse_pricing_grid(xlsx1)
    assert len(dpgf_items) == 14
    print(f"✅ 4. Extraction DPGF (Excel/pandas/openpyxl) : OK ({len(dpgf_items)} postes métrés)", flush=True)

    # 5. Test Analysis Engine (Local Expert Engine)
    analysis = TenderAnalyzerEngine.analyze(
        cctp_text=pdf_res["full_text"],
        dpgf_items=dpgf_items,
        filename_cctp=pdf1.name,
        filename_dpgf=xlsx1.name,
    )
    assert analysis.overview.title
    assert analysis.overview.client
    assert analysis.overview.submission_deadline
    assert analysis.scoring.verdict in ["GO", "GO_AVEC_RESERVES", "NO_GO"]
    assert len(analysis.technical_norms) >= 3
    assert len(analysis.financial_risks) >= 3
    print(f"✅ 5. Moteur d'Analyse Réglementaire & Risques : OK", flush=True)
    print(f"   - Marché : {analysis.overview.title}", flush=True)
    print(f"   - Acheteur : {analysis.overview.client}", flush=True)
    print(f"   - Date Limite : {analysis.overview.submission_deadline}", flush=True)
    print(f"   - Décision 60s : {analysis.scoring.verdict} ({analysis.scoring.overall_score}/100)", flush=True)
    print(f"   - Normes détectées : {[n.code for n in analysis.technical_norms]}", flush=True)

    # 6. Test PDF Report Generation
    pdf_bytes = DocumentExporter.generate_pdf(analysis)
    assert len(pdf_bytes) > 2000
    print(f"✅ 6. Générateur de Fiche Décision PDF (ReportLab) : OK ({len(pdf_bytes)} octets)", flush=True)

    # 7. Test Excel Workbook Generation
    xlsx_bytes = DocumentExporter.generate_excel(analysis)
    assert len(xlsx_bytes) > 2000
    print(f"✅ 7. Générateur de Classeur DPGF Excel (openpyxl) : OK ({len(xlsx_bytes)} octets)", flush=True)

    # 8. Test CSV Export Generation
    csv_str = DocumentExporter.generate_csv(analysis)
    assert "Designation" in csv_str or "Poste" in csv_str
    print(f"✅ 8. Générateur de Bordereau CSV : OK ({len(csv_str)} caractères)", flush=True)

    # 9. Test Sample 2 (Plâtrerie)
    pdf2_res = PDFParser.extract_text_and_metadata(pdf2)
    dpgf2_items = DPGFParser.parse_pricing_grid(xlsx2)
    analysis2 = TenderAnalyzerEngine.analyze(
        cctp_text=pdf2_res["full_text"],
        dpgf_items=dpgf2_items,
        filename_cctp=pdf2.name,
        filename_dpgf=xlsx2.name,
    )
    assert analysis2.scoring.overall_score > 0
    print(f"✅ 9. Dossier Plâtrerie / Médiathèque : OK (Score: {analysis2.scoring.overall_score}/100)", flush=True)

    print("\n🎉 TOUS LES COMPOSANTS DU BTP TENDER ANALYZER FONCTIONNENT PARFAITEMENT !", flush=True)

if __name__ == "__main__":
    run_tests()
