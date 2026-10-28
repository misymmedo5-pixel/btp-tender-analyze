import logging
from pathlib import Path
from typing import Dict, Any, List
import pymupdf as fitz

logger = logging.getLogger("btp.pdf_parser")

class PDFParser:
    """Extracts text, metadata, and structural sections from French BTP public tender PDFs (CCTP, CCAP, RC)."""

    @staticmethod
    def extract_text_and_metadata(pdf_path: Path) -> Dict[str, Any]:
        """
        Parses a PDF file and returns extracted text, per-page contents, and document metadata.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"Le fichier PDF spécifié n'existe pas: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du document PDF: {e}")
            raise ValueError(f"Impossible de lire le fichier PDF ({e})")

        page_count = len(doc)
        full_text_parts: List[str] = []
        pages_data: List[Dict[str, Any]] = []

        toc = doc.get_toc() # Table of contents bookmarks if present

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_text = page.get_text("text") or ""
            clean_text = page_text.strip()
            
            full_text_parts.append(f"--- PAGE {page_idx + 1} ---\n" + clean_text)
            pages_data.append({
                "page_number": page_idx + 1,
                "text": clean_text,
                "char_count": len(clean_text),
            })

        doc_metadata = doc.metadata or {}
        doc.close()

        combined_text = "\n\n".join(full_text_parts)

        return {
            "page_count": page_count,
            "metadata": doc_metadata,
            "toc": toc,
            "full_text": combined_text,
            "pages": pages_data,
        }
