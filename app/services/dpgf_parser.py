import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from app.models.tender import DPGFItem

logger = logging.getLogger("btp.dpgf_parser")

class DPGFParser:
    """Parses Excel (.xlsx/.xls) and CSV pricing grids (DPGF / BPU) for French construction tenders."""

    DESIGNATION_KEYWORDS = ["designation", "désignation", "description", "libelle", "libellé", "prestation", "ouvrage", "nature des travaux"]
    UNIT_KEYWORDS = ["unite", "unité", "u", "unit"]
    QTY_KEYWORDS = ["quantite", "quantité", "qte", "qté", "qte prevue", "quantités"]
    PU_KEYWORDS = ["prix unitaire", "p.u.", "pu ht", "p.u. ht", "pu", "prix unitaire ht"]
    TOTAL_KEYWORDS = ["total ht", "montant ht", "prix total", "total", "montant"]
    ITEM_KEYWORDS = ["n°", "no", "num", "numero", "numéro", "item", "poste", "code", "article"]

    @classmethod
    def parse_pricing_grid(cls, file_path: Path) -> List[DPGFItem]:
        """
        Loads and parses a DPGF/BPU Excel or CSV file into a list of DPGFItem objects.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Le fichier DPGF spécifié est introuvable: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix in [".xlsx", ".xls"]:
            return cls._parse_excel(file_path)
        elif suffix == ".csv":
            return cls._parse_csv(file_path)
        else:
            raise ValueError(f"Format de fichier non pris en charge pour la DPGF: {suffix}")

    @classmethod
    def _parse_csv(cls, file_path: Path) -> List[DPGFItem]:
        # Try semicolon separator first (standard French CSV), then comma
        for sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(file_path, sep=sep, encoding="utf-8-sig", dtype=str)
                if len(df.columns) >= 2:
                    return cls._extract_items_from_dataframe(df)
            except Exception:
                continue
        # Fallback with latin-1
        try:
            df = pd.read_csv(file_path, sep=";", encoding="latin-1", dtype=str)
            return cls._extract_items_from_dataframe(df)
        except Exception as e:
            logger.error(f"Erreur de lecture CSV: {e}")
            return []

    @classmethod
    def _parse_excel(cls, file_path: Path) -> List[DPGFItem]:
        try:
            excel_file = pd.ExcelFile(file_path)
            # Pick first sheet or sheet with 'dpgf' or 'bpu' in name
            sheet_names = excel_file.sheet_names
            target_sheet = sheet_names[0]
            for s in sheet_names:
                if any(k in s.lower() for k in ["dpgf", "bpu", "chiffrage", "devis", "prix", "bordereau"]):
                    target_sheet = s
                    break

            # Read up to 20 rows to find header row index
            df_preview = pd.read_excel(file_path, sheet_name=target_sheet, header=None, nrows=25, dtype=str)
            header_idx = cls._find_header_row_index(df_preview)

            df = pd.read_excel(file_path, sheet_name=target_sheet, skiprows=header_idx, dtype=str)
            return cls._extract_items_from_dataframe(df)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier Excel: {e}")
            return []

    @classmethod
    def _find_header_row_index(cls, df_preview: pd.DataFrame) -> int:
        best_score = 0
        best_idx = 0
        for idx, row in df_preview.iterrows():
            row_str = " ".join([str(val).lower() for val in row.dropna()])
            score = 0
            if any(k in row_str for k in cls.DESIGNATION_KEYWORDS):
                score += 3
            if any(k in row_str for k in cls.QTY_KEYWORDS):
                score += 2
            if any(k in row_str for k in cls.UNIT_KEYWORDS):
                score += 2
            if any(k in row_str for k in cls.PU_KEYWORDS):
                score += 2
            if any(k in row_str for k in cls.ITEM_KEYWORDS):
                score += 1
            if score > best_score:
                best_score = score
                best_idx = idx
        return int(best_idx)

    @classmethod
    def _extract_items_from_dataframe(cls, df: pd.DataFrame) -> List[DPGFItem]:
        df = df.dropna(how="all")
        if df.empty:
            return []

        col_map = cls._map_columns(df)
        desig_col = col_map.get("designation")
        if not desig_col:
            # Fallback: Pick first text column with longest string contents
            for col in df.columns:
                non_nulls = df[col].dropna()
                if len(non_nulls) > 0 and non_nulls.astype(str).str.len().mean() > 10:
                    desig_col = col
                    break
        if not desig_col and len(df.columns) > 1:
            desig_col = df.columns[1]

        items: List[DPGFItem] = []
        current_lot = "Lot Principal"

        for idx, row in df.iterrows():
            desig_val = str(row.get(desig_col, "")).strip()
            if not desig_val or desig_val.lower() in ["nan", "none", ""]:
                continue

            # Check if this row is a lot header (e.g. "LOT 02 - ELECTRICITE", "CHAPITRE 1")
            if re.match(r"^(lot|chapitre|section|partie)\s+[\d\w]", desig_val, re.IGNORECASE) or (
                len(desig_val) < 60 and ("lot" in desig_val.lower() or "chapitre" in desig_val.lower())
            ):
                current_lot = desig_val
                continue

            item_num = ""
            if col_map.get("item"):
                raw_item = str(row.get(col_map["item"], "")).strip()
                if raw_item.lower() not in ["nan", "none"]:
                    item_num = raw_item
            if not item_num:
                item_num = f"{len(items) + 1}"

            unit = "u"
            if col_map.get("unit"):
                raw_unit = str(row.get(col_map["unit"], "")).strip()
                if raw_unit.lower() not in ["nan", "none"] and raw_unit:
                    unit = raw_unit.lower()

            qty = 1.0
            if col_map.get("qty"):
                qty = cls._clean_number(row.get(col_map["qty"]))
                if qty == 0.0:
                    qty = 1.0

            pu = 0.0
            if col_map.get("pu"):
                pu = cls._clean_number(row.get(col_map["pu"]))

            total = 0.0
            if col_map.get("total"):
                total = cls._clean_number(row.get(col_map["total"]))
            if total == 0.0 and pu > 0.0:
                total = round(pu * qty, 2)

            # Avoid adding subtotal / summary lines
            clean_lower = desig_val.lower()
            if any(k in clean_lower for k in ["total", "sous-total", "tva", "recapitulatif", "récapitulatif", "montant global"]):
                continue

            items.append(
                DPGFItem(
                    item_number=item_num,
                    designation=desig_val,
                    unit=unit,
                    quantity=qty,
                    unit_price=pu if pu > 0 else None,
                    total_price=total if total > 0 else None,
                    lot=current_lot,
                )
            )

        return items

    @classmethod
    def _map_columns(cls, df: pd.DataFrame) -> Dict[str, str]:
        mapping = {}
        for col in df.columns:
            clean_name = str(col).lower().strip()
            if not mapping.get("designation") and any(k in clean_name for k in cls.DESIGNATION_KEYWORDS):
                mapping["designation"] = col
            elif not mapping.get("qty") and any(k in clean_name for k in cls.QTY_KEYWORDS):
                mapping["qty"] = col
            elif not mapping.get("unit") and any(clean_name == k or f" {k}" in clean_name for k in cls.UNIT_KEYWORDS):
                mapping["unit"] = col
            elif not mapping.get("pu") and any(k in clean_name for k in cls.PU_KEYWORDS):
                mapping["pu"] = col
            elif not mapping.get("total") and any(k in clean_name for k in cls.TOTAL_KEYWORDS):
                mapping["total"] = col
            elif not mapping.get("item") and any(k in clean_name for k in cls.ITEM_KEYWORDS):
                mapping["item"] = col
        return mapping

    @staticmethod
    def _clean_number(val: Any) -> float:
        if val is None or pd.isna(val):
            return 0.0
        val_str = str(val).strip()
        # Remove currency symbols, spaces, NBSP
        val_str = re.sub(r"[€\$\s\xa0]", "", val_str)
        # Replace French comma with dot
        val_str = val_str.replace(",", ".")
        try:
            return float(val_str)
        except ValueError:
            return 0.0
