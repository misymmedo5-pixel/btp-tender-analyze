import io
import csv
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models.tender import TenderAnalysis

class DocumentExporter:
    """Generates professional PDF, Excel, and CSV export files for BTP contractors."""

    @classmethod
    def generate_pdf(cls, analysis: TenderAnalysis) -> bytes:
        """
        Builds a comprehensive, styled 1-to-2 page BTP executive decision sheet.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        
        # Color palette
        navy = colors.HexColor("#0F172A")
        slate = colors.HexColor("#334155")
        amber = colors.HexColor("#D97706")
        emerald = colors.HexColor("#059669")
        rose = colors.HexColor("#E11D48")
        light_bg = colors.HexColor("#F8FAFC")
        border_color = colors.HexColor("#E2E8F0")

        # Custom paragraph styles
        style_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=navy,
        )
        style_subtitle = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=slate,
        )
        style_h2 = ParagraphStyle(
            "H2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=navy,
            spaceAfter=4,
        )
        style_body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=slate,
        )
        style_body_bold = ParagraphStyle(
            "BodyBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=navy,
        )
        style_verdict = ParagraphStyle(
            "Verdict",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
        style_score = ParagraphStyle(
            "Score",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.white,
        )

        elements = []

        # Header bar
        header_text = f"<b>BTP PUBLIC TENDER ANALYZER</b> &nbsp;|&nbsp; Fiche d'Aide à la Décision 60s"
        date_str = f"Réf: {analysis.id} &nbsp;|&nbsp; Émis le: {analysis.analysis_timestamp}"
        header_data = [
            [Paragraph(header_text, style_title), Paragraph(date_str, style_subtitle)]
        ]
        header_table = Table(header_data, colWidths=[120 * mm, 60 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4 * mm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=navy, spaceAfter=8))

        # Verdict Banner
        scoring = analysis.scoring
        if scoring.verdict == "GO":
            bg_color = emerald
            verdict_text = "DÉCISION : GO FRANCO (Dossier Très Favorable)"
        elif scoring.verdict == "GO_AVEC_RESERVES":
            bg_color = amber
            verdict_text = "DÉCISION : GO AVEC RÉSERVES (Précautions Contractuelles)"
        else:
            bg_color = rose
            verdict_text = "DÉCISION : NO-GO DÉCONSEILLÉ (Risques Élevés)"

        verdict_data = [
            [
                Paragraph(verdict_text, style_verdict),
                Paragraph(f"Score Faisabilité<br/><b>{scoring.overall_score} / 100</b>", style_score),
            ]
        ]
        verdict_table = Table(verdict_data, colWidths=[130 * mm, 50 * mm])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(verdict_table)
        elements.append(Spacer(1, 4 * mm))

        # Executive summary
        summary_p = Paragraph(f"<b>Synthèse Stratégique :</b> {scoring.executive_summary}", style_body)
        summary_table = Table([[summary_p]], colWidths=[180 * mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_bg),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 4 * mm))

        # Project Overview Box
        ov = analysis.overview
        lots_str = ", ".join(ov.lots) if ov.lots else "Tous corps d'état"
        ov_data = [
            [Paragraph("<b>Objet du Marché :</b>", style_body_bold), Paragraph(ov.title, style_body)],
            [Paragraph("<b>Maître d'Ouvrage :</b>", style_body_bold), Paragraph(ov.client, style_body)],
            [Paragraph("<b>Lieu du Chantier :</b>", style_body_bold), Paragraph(ov.location, style_body)],
            [Paragraph("<b>Date Limite (DLRO) :</b>", style_body_bold), Paragraph(f"<b>{ov.submission_deadline}</b>", style_body)],
            [Paragraph("<b>Délai d'Exécution :</b>", style_body_bold), Paragraph(ov.estimated_duration, style_body)],
            [Paragraph("<b>Lots Concernés :</b>", style_body_bold), Paragraph(lots_str, style_body)],
        ]
        ov_table = Table(ov_data, colWidths=[45 * mm, 135 * mm])
        ov_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(Paragraph("1. IDENTIFICATION DU MARCHÉ & DÉLAIS", style_h2))
        elements.append(ov_table)
        elements.append(Spacer(1, 4 * mm))

        # Red Flags and Warnings
        rf_text = "<br/>".join([f"• <font color='#E11D48'><b>{rf}</b></font>" for rf in scoring.red_flags]) if scoring.red_flags else "• <i>Aucun point bloquant critique détecté.</i>"
        aw_text = "<br/>".join([f"• {aw}" for aw in scoring.amber_warnings]) if scoring.amber_warnings else "• <i>Conditions contractuelles standard.</i>"
        gl_text = "<br/>".join([f"• <font color='#059669'>{gl}</font>" for gl in scoring.green_lights]) if scoring.green_lights else "• <i>Conforme aux usages du BTP.</i>"

        points_data = [
            [
                Paragraph("<b>🔴 POINTS BLOQUANTS (Red Flags)</b>", style_body_bold),
                Paragraph("<b>🟡 POINTS DE VIGILANCE (Risques)</b>", style_body_bold),
            ],
            [
                Paragraph(rf_text, style_body),
                Paragraph(aw_text, style_body),
            ]
        ]
        points_table = Table(points_data, colWidths=[90 * mm, 90 * mm])
        points_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), light_bg),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(Paragraph("2. MATRICE DE VIGILANCE CONTRACTUELLE", style_h2))
        elements.append(points_table)
        elements.append(Spacer(1, 4 * mm))

        # Financial risks table
        elements.append(Paragraph("3. CLAUSES FINANCIÈRES & PÉNALITÉS CRITIQUES", style_h2))
        risk_rows = [
            [
                Paragraph("<b>Clause & Sévérité</b>", style_body_bold),
                Paragraph("<b>Extrait Contractuel</b>", style_body_bold),
                Paragraph("<b>Conseil Opérationnel</b>", style_body_bold),
            ]
        ]
        for r in analysis.financial_risks[:4]:
            sev_badge = f"<font color='#E11D48'><b>[HAUTE]</b></font>" if r.severity == 'high' else f"<font color='#D97706'>[MOYENNE]</font>"
            risk_rows.append([
                Paragraph(f"{r.type}<br/>{sev_badge}", style_body),
                Paragraph(r.clause_text[:120], style_body),
                Paragraph(r.recommendation, style_body),
            ])

        risk_table = Table(risk_rows, colWidths=[45 * mm, 65 * mm, 70 * mm])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), light_bg),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(risk_table)
        elements.append(Spacer(1, 4 * mm))

        # Norms & Certifications
        elements.append(Paragraph("4. NORMES DTU & QUALIFICATIONS EXIGÉES", style_h2))
        norm_rows = [
            [
                Paragraph("<b>Code & Référence</b>", style_body_bold),
                Paragraph("<b>Intitulé Officiel</b>", style_body_bold),
                Paragraph("<b>Exigence CCTP</b>", style_body_bold),
            ]
        ]
        for n in analysis.technical_norms[:4]:
            norm_rows.append([
                Paragraph(f"<b>{n.code}</b>", style_body),
                Paragraph(n.title, style_body),
                Paragraph(n.description[:110], style_body),
            ])
        norm_table = Table(norm_rows, colWidths=[40 * mm, 65 * mm, 75 * mm])
        norm_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), light_bg),
            ('BOX', (0,0), (-1,-1), 0.5, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(norm_table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def generate_excel(cls, analysis: TenderAnalysis) -> bytes:
        """
        Builds a structured Excel workbook with 4 tabs: Synthèse, Normes, Risques, DPGF Chiffrage.
        """
        wb = openpyxl.Workbook()
        
        # Styles
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        title_font = Font(name="Arial", size=14, bold=True, color="0F172A")
        bold_font = Font(name="Arial", size=10, bold=True)
        regular_font = Font(name="Arial", size=9)
        border_thin = Side(border_style="thin", color="CBD5E1")
        cell_border = Border(top=border_thin, left=border_thin, right=border_thin, bottom=border_thin)

        # Sheet 1: Synthèse
        ws_synth = wb.active
        ws_synth.title = "Synthèse Appel d'Offres"
        ws_synth.views.sheetView[0].showGridLines = True

        ws_synth["A1"] = "ANALYSEUR D'APPELS D'OFFRES BTP - SYNTHÈSE DÉCISION"
        ws_synth["A1"].font = title_font
        ws_synth["A2"] = f"Réf: {analysis.id} | Émis le: {analysis.analysis_timestamp} | Moteur: {analysis.ai_source}"
        ws_synth["A2"].font = regular_font

        ws_synth["A4"] = "DÉCISION & SCORE"
        ws_synth["A4"].font = bold_font
        ws_synth["B4"] = analysis.scoring.verdict
        ws_synth["C4"] = f"{analysis.scoring.overall_score} / 100"
        ws_synth["B4"].font = bold_font

        overview_fields = [
            ("Objet du marché", analysis.overview.title),
            ("Maître d'Ouvrage (Acheteur)", analysis.overview.client),
            ("Maître d'Œuvre (MOE)", analysis.overview.project_manager or "Non spécifié"),
            ("Lieu d'exécution", analysis.overview.location),
            ("Date limite de remise des plis (DLRO)", analysis.overview.submission_deadline),
            ("Durée d'exécution prévisionnelle", analysis.overview.estimated_duration),
            ("Lots concernés", ", ".join(analysis.overview.lots)),
            ("Type de marché", analysis.overview.market_type),
        ]

        row_cursor = 6
        for label, val in overview_fields:
            ws_synth[f"A{row_cursor}"] = label
            ws_synth[f"A{row_cursor}"].font = bold_font
            ws_synth[f"B{row_cursor}"] = val
            ws_synth[f"B{row_cursor}"].font = regular_font
            row_cursor += 1

        row_cursor += 1
        ws_synth[f"A{row_cursor}"] = "Synthèse Opérationnelle"
        ws_synth[f"A{row_cursor}"].font = bold_font
        ws_synth[f"B{row_cursor}"] = analysis.scoring.executive_summary
        ws_synth[f"B{row_cursor}"].font = regular_font

        # Auto width
        ws_synth.column_dimensions["A"].width = 32
        ws_synth.column_dimensions["B"].width = 85
        ws_synth.column_dimensions["C"].width = 18

        # Sheet 2: Normes DTU
        ws_norm = wb.create_sheet(title="Normes DTU & Certifs")
        ws_norm.views.sheetView[0].showGridLines = True
        norm_headers = ["Code Norme / DTU", "Intitulé Officiel", "Lot Concerné", "Exigence", "Description CCTP"]
        ws_norm.append(norm_headers)
        for col_idx in range(1, 6):
            cell = ws_norm.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for n in analysis.technical_norms:
            ws_norm.append([n.code, n.title, n.lot, n.requirement_level, n.description])
        for c in analysis.certifications:
            ws_norm.append([c.name, c.penalty_if_missing, c.category, "Obligatoire", "Certification exigée"])

        for col_idx, width in enumerate([18, 40, 25, 15, 60], start=1):
            ws_norm.column_dimensions[get_column_letter(col_idx)].width = width

        # Sheet 3: Risques Financiers
        ws_risk = wb.create_sheet(title="Clauses CCAP & Risques")
        ws_risk.views.sheetView[0].showGridLines = True
        risk_headers = ["Type de Risque", "Sévérité", "Extrait Clause Contractuelle", "Impact Financier Estimé", "Recommandation Artisan"]
        ws_risk.append(risk_headers)
        for col_idx in range(1, 6):
            cell = ws_risk.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r in analysis.financial_risks:
            ws_risk.append([r.type, r.severity.upper(), r.clause_text, r.impact_estimate, r.recommendation])

        for col_idx, width in enumerate([30, 14, 50, 45, 55], start=1):
            ws_risk.column_dimensions[get_column_letter(col_idx)].width = width

        # Sheet 4: DPGF Chiffrage
        ws_dpgf = wb.create_sheet(title="Grille DPGF Chiffrage")
        ws_dpgf.views.sheetView[0].showGridLines = True
        dpgf_headers = ["N° Poste", "Désignation des Travaux", "Unité", "Quantité", "Prix Unitaire HT (€)", "Total HT (€)", "Lot / Section"]
        ws_dpgf.append(dpgf_headers)
        for col_idx in range(1, 8):
            cell = ws_dpgf.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        start_row = 2
        for item in analysis.dpgf_items:
            pu = item.unit_price or 0.0
            ws_dpgf.append([
                item.item_number,
                item.designation,
                item.unit,
                item.quantity,
                pu,
                f"=D{start_row}*E{start_row}",
                item.lot,
            ])
            # Format numbers
            ws_dpgf[f"D{start_row}"].number_format = "#,##0.00"
            ws_dpgf[f"E{start_row}"].number_format = "#,##0.00 €"
            ws_dpgf[f"F{start_row}"].number_format = "#,##0.00 €"
            start_row += 1

        # Total line
        if len(analysis.dpgf_items) > 0:
            total_row = start_row
            ws_dpgf[f"B{total_row}"] = "TOTAL GÉNÉRAL H.T."
            ws_dpgf[f"B{total_row}"].font = bold_font
            ws_dpgf[f"F{total_row}"] = f"=SUM(F2:F{total_row - 1})"
            ws_dpgf[f"F{total_row}"].font = bold_font
            ws_dpgf[f"F{total_row}"].number_format = "#,##0.00 €"

        for col_idx, width in enumerate([10, 50, 10, 14, 20, 20, 25], start=1):
            ws_dpgf.column_dimensions[get_column_letter(col_idx)].width = width

        # Save to buffer
        out_buffer = io.BytesIO()
        wb.save(out_buffer)
        out_buffer.seek(0)
        return out_buffer.getvalue()

    @classmethod
    def generate_csv(cls, analysis: TenderAnalysis) -> str:
        """
        Builds a clean semicolon-separated CSV of the DPGF items.
        """
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["N_Poste", "Designation", "Unite", "Quantite", "Prix_Unitaire_HT", "Total_HT", "Lot"])

        for item in analysis.dpgf_items:
            pu = f"{item.unit_price:.2f}".replace(".", ",") if item.unit_price else "0,00"
            tot = f"{item.total_price:.2f}".replace(".", ",") if item.total_price else "0,00"
            qty = f"{item.quantity:.2f}".replace(".", ",")
            writer.writerow([item.item_number, item.designation, item.unit, qty, pu, tot, item.lot])

        return output.getvalue()
