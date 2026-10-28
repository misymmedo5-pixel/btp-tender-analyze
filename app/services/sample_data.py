from pathlib import Path
from typing import Dict, Any, List
import openpyxl
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.tender import DPGFItem

SAMPLE_1_CCTP_TEXT = """
RÉPUBLIQUE FRANÇAISE - DÉPARTEMENT DES YVELINES
VILLE DE SAINT-GERMAIN-EN-LAYE - DIRECTION DE LA COMMANDE PUBLIQUE

MARCHÉ PUBLIC DE TRAVAUX - PROCÉDURE ADAPTÉE (MAPA)
CAHIER DES CLAUSES TECHNIQUES PARTICULIÈRES (CCTP) & CCAP VALANT DOCUMENT UNIQUE

OBJET DU MARCHÉ :
Rénovation énergétique et mise aux normes des installations électriques du Groupe Scolaire Pasteur
Chantier situé : 14, Rue Pasteur - 78100 Saint-Germain-en-Laye

MAÎTRE D'OUVRAGE :
Commune de Saint-Germain-en-Laye (Hôtel de Ville, BP 1011)

MAÎTRISE D'ŒUVRE :
Cabinet Ingénierie & Bâtiment Consultants (78000 Versailles)

LOT CONCERNÉ :
Lot n° 02 – Électricité Courants Forts / Courants Faibles / Éclairage LED & SSI

1. CALENDRIER ET DÉLAIS D'EXÉCUTION :
- Date limite de remise des offres (DLRO) : 18/11/2026 à 12h00 précises sur le profil d'acheteur AWS.
- Délai global d'exécution : 3 mois (dont 3 semaines de période de préparation de chantier).
- Les travaux en milieu scolaire devront impérativement être calés sur les périodes de congés et sans perturbation des cours.

2. NORMES ET RÉGLEMENTATIONS APPLICABLES :
L'entrepreneur devra se conformer strictement aux normes et textes suivants :
- NF C 15-100 : Installations électriques à basse tension (amendement 5 inclus).
- NF C 14-100 : Branchements et comptage Enedis.
- NF EN 12464-1 : Éclairage des lieux de travail intérieur (exigence UGR < 19 dans les salles de classe).
- NF S 61-936 : Systèmes de Sécurité Incendie - Équipement d'Alarme de type 4.
- Décret n° 88-1056 du 14 novembre 1988 sur la protection des travailleurs.
- L'attestation de conformité visée par le CONSUEL est exigée avant toute mise sous tension définitive.

3. QUALIFICATIONS PROFESSIONNELLES ET CERTIFICATIONS EXIGÉES :
Les candidats devront justifier au minimum des qualifications suivantes :
- Qualification Qualifelec RGE E2-C2 (Mention Logement Tertiaire).
- Personnel habilité selon la norme NF C 18-510 (habilitations B1V, B2V, BR, BC obligatoires).
- Autorisation d'Intervention à Proximité des Réseaux (AIPR) pour le chef de chantier.
- Attestation d'Assurance Décennale et Responsabilité Civile Professionnelle en cours de validité.

4. CLAUSES FINANCIÈRES, PÉNALITÉS ET RISQUES CONTRACTUELS :
- Pénalités de retard : Par dérogation au CCAG Travaux, en cas de retard sur le calendrier contractuel, il sera appliqué de plein droit et sans mise en demeure préalable une pénalité forfaitaire de 350 € par jour calendaire de retard.
- Retenue de garantie : Une retenue de garantie de 5% sera opérée sur chaque acompte mensuel. Elle pourra être remplacée par une caution bancaire personnelle et solidaire.
- Compte prorata : Les dépenses d'intérêt commun et de fonctionnement du chantier feront l'objet d'un compte prorata conventionnel estimé à 1.8% du montant du marché HT.
- Délais de paiement : Le délai global de paiement est fixé à 30 jours conformément au Code de la commande publique. Facturation obligatoire sur la plateforme Chorus Pro.
- Modalités des prix : Prix fermes non révisables pour la durée initiale du marché.
"""

SAMPLE_1_DPGF_ITEMS = [
    DPGFItem(item_number="1.1", designation="Installation de chantier, balisage sécurisé et raccordement provisoire", unit="forfait", quantity=1.0, unit_price=1200.0, total_price=1200.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="1.2", designation="Dépose soignée de l'ancien TGBT et recyclage filière DEEE certifiée", unit="ens", quantity=1.0, unit_price=850.0, total_price=850.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="2.1", designation="Fourniture et pose Armoire TGBT métallique IP55 400A avec inverseur de source", unit="u", quantity=1.0, unit_price=8400.0, total_price=8400.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="2.2", designation="Tableau divisionnaire modulaire 72 modules pour aile élémentaire", unit="u", quantity=2.0, unit_price=2100.0, total_price=4200.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="2.3", designation="Disjoncteurs différentiels tétrapolaires 40A 30mA Type A", unit="u", quantity=8.0, unit_price=145.0, total_price=1160.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="3.1", designation="Chemin de câbles en tôle perforée largeur 200mm sous faux-plafond", unit="ml", quantity=180.0, unit_price=38.0, total_price=6840.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="3.2", designation="Câble cuivre U1000 R2V 3G2.5 mm² sous conduit ICTA", unit="ml", quantity=650.0, unit_price=4.8, total_price=3120.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="4.1", designation="Pavé LED 600x600 36W 4000K basse luminance UGR<19 avec driver DALI", unit="u", quantity=94.0, unit_price=115.0, total_price=10810.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="4.2", designation="Détecteur de présence et luminosité 360° pour extinction automatique", unit="u", quantity=18.0, unit_price=85.0, total_price=1530.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="4.3", designation="Bloc Autonome d'Éclairage de Sécurité (BAES) étanche technologie SATI", unit="u", quantity=24.0, unit_price=92.0, total_price=2208.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="5.1", designation="Prise RJ45 Catégorie 6A STP blindée en goulotte appareillable", unit="u", quantity=42.0, unit_price=68.0, total_price=2856.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="5.2", designation="Baie de brassage 19 pouces 24U équipée de bandeaux et passe-fils", unit="u", quantity=1.0, unit_price=1650.0, total_price=1650.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="6.1", designation="Équipement d'Alarme Incendie Type 4 autonome avec déclencheurs manuels", unit="ens", quantity=1.0, unit_price=1950.0, total_price=1950.0, lot="Lot 02 - Électricité"),
    DPGFItem(item_number="7.1", designation="Essais, autocontrôles d'isolement, plans de récolement DOE et passage CONSUEL", unit="forfait", quantity=1.0, unit_price=1800.0, total_price=1800.0, lot="Lot 02 - Électricité"),
]

SAMPLE_2_CCTP_TEXT = """
RÉPUBLIQUE FRANÇAISE - COMMUNAUTÉ D'AGGLOMÉRATION
DIRECTION DU PATRIMOINE BÂTI ET DES GRANDS TRAVAUX

MARCHÉ PUBLIC DE TRAVAUX - APPEL D'OFFRES OUVERT (AOO)
CAHIER DES CLAUSES TECHNIQUES PARTICULIÈRES (CCTP)

OBJET DE LA CONSULTATION :
Réhabilitation acoustique et aménagement intérieur de la Nouvelle Médiathèque Municipale
Lieu des travaux : Avenue des Arts - 92100 Boulogne-Billancourt

MAÎTRE D'OUVRAGE :
Communauté d'Agglomération du Grand Paris Ouest

MAÎTRISE D'ŒUVRE :
Atelier d'Architecture & Acoustique Contemporaine

LOT CONCERNÉ :
Lot n° 04 – Plâtrerie / Doublages / Cloisons Acoustiques / Faux-Plafonds Démontables

1. DÉLAIS ET PLANNING CHANTIER :
- Date limite de dépôt des plis : 24/11/2026 à 16h00 sur la plateforme Maximilien.
- Durée prévisionnelle d'exécution : 4 mois y compris période de préparation de 4 semaines.
- Planning strict avec intervention par phases successives sans interruption du rez-de-chaussée.

2. NORMES ET TEXTES DE RÉFÉRENCE CSTB :
- DTU 25.41 : Ouvrages en plaques de plâtre à faces cartonnées (Placostil).
- DTU 25.42 : Ouvrages de doublage et d'isolation des parois intérieures.
- DTU 58.1 : Plafonds suspendus démontables.
- Classement au feu : Matériaux incombustibles A2-s1,d0 (ancien M0).
- Performances acoustiques : Isolement Rw+C >= 48 dB entre salles de lecture et espaces publics.

3. QUALIFICATIONS PROFESSIONNELLES :
- Qualification Qualibat 4112 (Plâtrerie) et Qualibat 4132 (Plafonds suspendus) exigées.
- Formation Amiante Sous-Section 4 (SS4) pour le personnel d'intervention.
- Attestation d'Assurance Décennale et Responsabilité Civile Professionnelle obligatoires.

4. DISPOSITIONS FINANCIÈRES ET PÉNALITÉS :
- Pénalités journalières de retard : 500 € HT par jour calendaire de retard, non plafonnées et sans mise en demeure préalable.
- Retenue de garantie : 5% prélevée sur chaque acompte, avec possibilité de substitution par une garantie à première demande.
- Compte prorata : 2.2% prélevé par l'entreprise générale gestionnaire de chantier.
- Prix ferme non révisable.
"""

SAMPLE_2_DPGF_ITEMS = [
    DPGFItem(item_number="1.01", designation="Installation de chantier, protections de sols et bennes de tri des déchets", unit="forfait", quantity=1.0, unit_price=950.0, total_price=950.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="2.01", designation="Cloison de distribution Placostil SAD 180 (Rw=58 dB) pour auditorium", unit="m²", quantity=220.0, unit_price=78.0, total_price=17160.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="2.02", designation="Cloison coupe-feu EI60 Placostil 98/48 avec 2 plaques BA13 coupe-feu par face", unit="m²", quantity=145.0, unit_price=64.0, total_price=9280.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="2.03", designation="Doublage thermo-acoustique sur ossature Stil F530 avec laine minérale 120mm", unit="m²", quantity=310.0, unit_price=48.0, total_price=14880.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="3.01", designation="Plafond acoustique démontable en dalles Gyptone perforées 600x600 sur ossature T24", unit="m²", quantity=280.0, unit_price=62.0, total_price=17360.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="3.02", designation="Plafond suspendu continu en plaques Placoplatre BA13 avec trappes de visite étanches", unit="m²", quantity=95.0, unit_price=52.0, total_price=4940.0, lot="Lot 04 - Plâtrerie"),
    DPGFItem(item_number="4.01", designation="Jointoiement soigné 3 passes, ponçage fin et récolement des surfaces pour finition Q3", unit="m²", quantity=970.0, unit_price=6.5, total_price=6305.0, lot="Lot 04 - Plâtrerie"),
]

SAMPLE_3_CCTP_TEXT = """
RÉPUBLIQUE FRANÇAISE - VILLE DE NANTERRE
DIRECTION DU PATRIMOINE BÂTI ET DE LA TRANSITION ÉNERGÉTIQUE

MARCHÉ PUBLIC DE TRAVAUX - PROCÉDURE ADAPTÉE (MAPA)
CAHIER DES CLAUSES TECHNIQUES PARTICULIÈRES (CCTP) & CCAP

OBJET DU MARCHÉ :
Rénovation des installations de plomberie sanitaire, production ECS et ventilation de la Crèche Municipale
Chantier : 28, Rue des Écoles - 92000 Nanterre

MAÎTRE D'OUVRAGE :
Ville de Nanterre (Hôtel de Ville)

LOT CONCERNÉ :
Lot n° 03 – Plomberie Sanitaire / Production Eau Chaude Solaire & Thermodynamique / VMC Double Flux

1. CALENDRIER ET DÉLAIS D'EXÉCUTION :
- Date limite de remise des offres : 02/12/2026 à 12h00 sur la plateforme Maximilien.
- Délai d'exécution : 2,5 mois durant la période de fermeture estivale.
- Aucune interruption de fourniture d'eau durant les périodes d'accueil du public.

2. NORMES ET RÉGLEMENTATIONS APPLICABLES :
- DTU 60.1 : Plomberie sanitaire pour bâtiments (canalisations cuivre et multicouche).
- DTU 68.3 : Installations de ventilation mécanique contrôlée (VMC double flux haut rendement).
- Arrêté du 30 novembre 2005 relatif aux installations fixes destinées au chauffage et à l'alimentation en eau chaude sanitaire (prévention légionellose : température minimale 55°C aux points de puisage).
- Robinetteries thermostatiques spéciales petite enfance limitées à 38°C anti-brûlure.

3. QUALIFICATIONS PROFESSIONNELLES EXIGÉES :
- Qualification Qualibat 5112 (Plomberie sanitaire) ou Qualibat 5312 (Installations thermiques).
- Mention RGE (Reconnu Garant de l'Environnement).
- Attestation d'Assurance Décennale et RC Pro en cours de validité.

4. CLAUSES FINANCIÈRES ET PÉNALITÉS CONTRACTUELLES :
- Pénalités de retard : 400 € HT par jour calendaire de retard, applicables de plein droit et sans mise en demeure.
- Retenue de garantie : 5% prélevée sur chaque situation d'acompte.
- Compte prorata : Forfaitisé à 1.5% du montant HT des travaux.
- Délais de paiement : 30 jours via mandat administratif Chorus Pro.
"""

SAMPLE_3_DPGF_ITEMS = [
    DPGFItem(item_number="1.01", designation="Installation de chantier, raccordements provisoires et protections antipoussière", unit="forfait", quantity=1.0, unit_price=1100.0, total_price=1100.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="2.01", designation="Dépose des anciens ballons électriques et recyclage des métaux", unit="ens", quantity=1.0, unit_price=750.0, total_price=750.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="3.01", designation="Chauffe-eau thermodynamique 300L COP>3.1 avec boucle d'eau chaude sanitaire", unit="u", quantity=2.0, unit_price=3200.0, total_price=6400.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="3.02", designation="Distribution cuivre et multicouche isolé calorifugé anti-déperdition", unit="ml", quantity=160.0, unit_price=32.0, total_price=5120.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="4.01", designation="Lavabo collectif maternelle avec mitigeurs temporisés anti-brûlure 38°C", unit="u", quantity=6.0, unit_price=420.0, total_price=2520.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="4.02", designation="Cuvette WC suspendue taille enfant avec bâti-support autoportant Geberit", unit="u", quantity=8.0, unit_price=380.0, total_price=3040.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="5.01", designation="Centrale de Traitement d'Air (CTA) double flux 1200 m³/h avec récupération 85%", unit="u", quantity=1.0, unit_price=7800.0, total_price=7800.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="5.02", designation="Réseau aéraulique en acier galvanisé rigide avec bouches d'insufflation silencieuses", unit="ml", quantity=95.0, unit_price=45.0, total_price=4275.0, lot="Lot 03 - Plomberie/CVC"),
    DPGFItem(item_number="6.01", designation="Équilibrage aéraulique, mise en service, désinfection des réseaux et DOE complet", unit="forfait", quantity=1.0, unit_price=1650.0, total_price=1650.0, lot="Lot 03 - Plomberie/CVC"),
]

def generate_sample_files_if_needed(target_dir: Path):
    """
    Generates realistic CCTP PDF and DPGF Excel sample files on disk for instant user testing.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf1_path = target_dir / "CCTP_Electricite_Ecole_Pasteur.pdf"
    xlsx1_path = target_dir / "DPGF_Electricite_Ecole_Pasteur.xlsx"
    pdf2_path = target_dir / "CCTP_Platrerie_Mediatheque.pdf"
    xlsx2_path = target_dir / "DPGF_Platrerie_Mediatheque.xlsx"
    pdf3_path = target_dir / "CCTP_CVC_Plomberie_Creche.pdf"
    xlsx3_path = target_dir / "DPGF_Lot03_CVC_Plomberie.xlsx"

    # Generate PDF 1
    if not pdf1_path.exists():
        _create_simple_pdf(pdf1_path, "CCTP - RÉNOVATION ÉLECTRIQUE GROUPE SCOLAIRE", SAMPLE_1_CCTP_TEXT)

    # Generate XLSX 1
    if not xlsx1_path.exists():
        _create_simple_excel(xlsx1_path, "DPGF Lot 02 - Électricité", SAMPLE_1_DPGF_ITEMS)

    # Generate PDF 2
    if not pdf2_path.exists():
        _create_simple_pdf(pdf2_path, "CCTP - PLÂTRERIE & ACOUSTIQUE MÉDIATHÈQUE", SAMPLE_2_CCTP_TEXT)

    # Generate XLSX 2
    if not xlsx2_path.exists():
        _create_simple_excel(xlsx2_path, "DPGF Lot 04 - Plâtrerie", SAMPLE_2_DPGF_ITEMS)

    # Generate PDF 3
    if not pdf3_path.exists():
        _create_simple_pdf(pdf3_path, "CCTP - PLOMBERIE SANITAIRE & CVC CRÈCHE", SAMPLE_3_CCTP_TEXT)

    # Generate XLSX 3
    if not xlsx3_path.exists():
        _create_simple_excel(xlsx3_path, "DPGF Lot 03 - Plomberie CVC", SAMPLE_3_DPGF_ITEMS)

def _create_simple_pdf(path: Path, title: str, content: str):
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('SampleTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'), spaceAfter=12)
    body_style = ParagraphStyle('SampleBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#1E293B'))

    story = [Paragraph(title, title_style), Spacer(1, 4*mm)]
    for line in content.strip().split("\n"):
        clean = line.strip()
        if not clean:
            story.append(Spacer(1, 2*mm))
        elif clean.startswith("-") or clean.startswith("•"):
            story.append(Paragraph(f"&nbsp;&nbsp;{clean}", body_style))
        elif any(clean.startswith(prefix) for prefix in ["1.", "2.", "3.", "4.", "OBJET", "MAÎTRE", "LOT"]):
            bold_style = ParagraphStyle('SampleH', parent=body_style, fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=2)
            story.append(Paragraph(clean, bold_style))
        else:
            story.append(Paragraph(clean, body_style))

    doc.build(story)

def _create_simple_excel(path: Path, sheet_title: str, items: List[DPGFItem]):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DPGF Chiffrage"
    ws.views.sheetView[0].showGridLines = True

    # Title
    ws["A1"] = sheet_title.upper()
    ws["A1"].font = openpyxl.styles.Font(name="Arial", size=12, bold=True)
    ws["A2"] = "Bordereau des Prix Unitaires & Décomposition du Prix Global (DPGF)"

    # Headers
    headers = ["N°", "Désignation des Prestations", "Unité", "Quantité", "P.U. H.T. (€)", "Montant H.T. (€)", "Lot"]
    ws.append([]) # Row 3 empty
    ws.append(headers) # Row 4 headers

    header_fill = openpyxl.styles.PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = openpyxl.styles.Font(name="Arial", size=10, bold=True, color="FFFFFF")
    for col in range(1, 8):
        c = ws.cell(row=4, column=col)
        c.fill = header_fill
        c.font = header_font
        c.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

    curr_row = 5
    for item in items:
        pu = item.unit_price or 0.0
        ws.append([
            item.item_number,
            item.designation,
            item.unit,
            item.quantity,
            pu,
            f"=D{curr_row}*E{curr_row}",
            item.lot
        ])
        ws[f"D{curr_row}"].number_format = "#,##0.00"
        ws[f"E{curr_row}"].number_format = "#,##0.00 €"
        ws[f"F{curr_row}"].number_format = "#,##0.00 €"
        curr_row += 1

    # Total row
    ws[f"B{curr_row}"] = "TOTAL GÉNÉRAL H.T."
    ws[f"B{curr_row}"].font = openpyxl.styles.Font(name="Arial", bold=True)
    ws[f"F{curr_row}"] = f"=SUM(F5:F{curr_row - 1})"
    ws[f"F{curr_row}"].font = openpyxl.styles.Font(name="Arial", bold=True)
    ws[f"F{curr_row}"].number_format = "#,##0.00 €"

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 20
    ws.column_dimensions["G"].width = 24

    wb.save(path)
