import re
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.models.tender import (
    ProjectOverview,
    TechnicalNorm,
    CertificationRequired,
    FinancialRisk,
    GoNoGoScore,
    DPGFItem,
    TenderAnalysis,
)

logger = logging.getLogger("btp.analyzer")

# Comprehensive Knowledge Base for French BTP Norms and Standards
BTP_NORM_DATABASE = {
    # Électricité & Réseaux
    "NF C 15-100": {
        "title": "Installations électriques à basse tension (logements, tertiaire et ERP)",
        "lot": "Électricité / Courants Forts",
        "level": "Obligatoire (Consuel)",
        "desc": "Conformité obligatoire du schéma unifilaire, calibres disjoncteurs, DDR 30mA, section des conducteurs et prises de terre.",
    },
    "NF C 14-100": {
        "title": "Installations de branchement à basse tension (Enedis / raccordement réseau)",
        "lot": "Électricité / VRD",
        "level": "Obligatoire",
        "desc": "Règles de raccordement du point de livraison au coupe-circuit principal.",
    },
    "NF EN 12464-1": {
        "title": "Éclairage des lieux de travail intérieur (Confort visuel et UGR)",
        "lot": "Électricité / Éclairage",
        "level": "Recommandé / Exigé en ERP",
        "desc": "Niveaux d'éclairement minimum en Lux et maîtrise de l'éblouissement pour bureaux et salles de classe.",
    },
    "NF S 61-936": {
        "title": "Systèmes de Sécurité Incendie (SSI) - Équipements d'alarme type 4 et type 1",
        "lot": "Électricité / SSI / Sécurité",
        "level": "Obligatoire ERP",
        "desc": "Diffusion sonore de l'alarme générale et asservissements de désenfumage.",
    },
    # Plâtrerie, Isolation, Faux-plafonds
    "DTU 25.41": {
        "title": "Ouvrages en plaques de plâtre à faces cartonnées (Placostil / cloisons)",
        "lot": "Plâtrerie / Isolation",
        "level": "Obligatoire",
        "desc": "Mise en œuvre des ossatures métalliques, entraxes de 60 ou 40 cm, joints et fixations mécaniques.",
    },
    "DTU 25.42": {
        "title": "Ouvrages de doublage et d'isolation des parois intérieures",
        "lot": "Plâtrerie / Doublage",
        "level": "Obligatoire",
        "desc": "Règles de collage et fixation mécanique des complexes isolants polystyrène ou laine de roche.",
    },
    "DTU 58.1": {
        "title": "Plafonds suspendus démontables (dalles minérales et métalliques)",
        "lot": "Faux-Plafonds",
        "level": "Obligatoire",
        "desc": "Tolérances de planéité, espacement des suspentes et respect des charges de luminaires.",
    },
    # Maçonnerie, Gros Œuvre, Façade
    "DTU 20.1": {
        "title": "Ouvrages en maçonnerie de petits éléments (parpaings, briques, chaînages)",
        "lot": "Maçonnerie / Gros Œuvre",
        "level": "Obligatoire",
        "desc": "Prescriptions pour les mortiers, armatures de chaînage horizontal et vertical et coupures de capillarité.",
    },
    "DTU 21": {
        "title": "Exécution des ouvrages en béton armé",
        "lot": "Gros Œuvre / Béton",
        "level": "Obligatoire",
        "desc": "Règles d'enrobage des aciers, formulation du béton et délais de décoffrage.",
    },
    # Plomberie, Chauffage, VMC
    "DTU 60.1": {
        "title": "Plomberie sanitaire pour bâtiments (canalisations cuivre, multicouche, PVC)",
        "lot": "Plomberie / Sanitaire",
        "level": "Obligatoire",
        "desc": "Pentes d'évacuation, diamètres nominaux, essais de mise en pression et fixations isophoniques.",
    },
    "DTU 65.10": {
        "title": "Canalisations d'eau chaude ou froide sous pression et distribution chauffage",
        "lot": "CVC / Chauffage",
        "level": "Obligatoire",
        "desc": "Calorifugeage des réseaux, vases d'expansion et soupapes de sécurité.",
    },
    "DTU 68.3": {
        "title": "Installations de ventilation mécanique contrôlée (VMC simple et double flux)",
        "lot": "Ventilation / Génie Climatique",
        "level": "Obligatoire",
        "desc": "Débits d'extraction réglementaires, étanchéité à l'air des conduits et pièges à son.",
    },
    # Couverture, Étanchéité
    "DTU 40.21": {
        "title": "Couverture en tuiles de terre cuite à emboîtement ou à glissement",
        "lot": "Couverture / Zinguerie",
        "level": "Obligatoire",
        "desc": "Fixation des tuiles selon zone de vent et pose de l'écran sous-toiture HPV.",
    },
    "DTU 43.1": {
        "title": "Étanchéité des toitures-terrasses et toitures inclinées avec éléments porteurs",
        "lot": "Étanchéité",
        "level": "Obligatoire",
        "desc": "Relevés d'étanchéité de 15 cm minimum, évacuation d'eaux pluviales (trop-pleins) et isolant thermique.",
    },
    # Menuiserie & Serrurerie
    "DTU 36.5": {
        "title": "Mise en œuvre des fenêtres et portes extérieures (Alu, PVC, Bois)",
        "lot": "Menuiserie Extérieure",
        "level": "Obligatoire",
        "desc": "Étanchéité à l'air et à l'eau AEV, fixation en rénovation ou en applique et rupture de pont thermique.",
    },
}

class TenderAnalyzerEngine:
    """Core analysis engine for French BTP public tenders with dual mode: Local Expert Engine and Gemini AI."""

    @classmethod
    def analyze(
        cls,
        cctp_text: str,
        dpgf_items: List[DPGFItem],
        filename_cctp: str = "document_cctp.pdf",
        filename_dpgf: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ) -> TenderAnalysis:
        """
        Executes complete analysis of tender documents.
        Uses Gemini 2.5 Flash if API key is provided and functional, otherwise executes the high-precision Local Expert Engine.
        """
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()

        # Try Gemini API if key is present
        if api_key:
            try:
                analysis = cls._analyze_with_gemini(cctp_text, dpgf_items, filename_cctp, filename_dpgf, api_key)
                if analysis:
                    return analysis
            except Exception as e:
                logger.warning(f"Erreur avec l'API Gemini, basculement vers le moteur expert local: {e}")

        # Local deterministic BTP expert engine
        return cls._analyze_local_expert(cctp_text, dpgf_items, filename_cctp, filename_dpgf)

    @classmethod
    def _analyze_local_expert(
        cls,
        text: str,
        dpgf_items: List[DPGFItem],
        filename_cctp: str,
        filename_dpgf: Optional[str],
    ) -> TenderAnalysis:
        """High-precision local heuristic & NLP extractor for French BTP public contracts."""
        overview = cls._extract_overview(text)
        technical_norms = cls._extract_norms(text)
        certifications = cls._extract_certifications(text)
        financial_risks = cls._extract_financial_risks(text)
        scoring = cls._calculate_go_no_go(overview, financial_risks, technical_norms, certifications, dpgf_items)

        return TenderAnalysis(
            id=f"BTP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            filename_cctp=filename_cctp,
            filename_dpgf=filename_dpgf,
            analysis_timestamp=datetime.now().strftime("%d/%m/%Y à %H:%M"),
            overview=overview,
            technical_norms=technical_norms,
            certifications=certifications,
            financial_risks=financial_risks,
            scoring=scoring,
            dpgf_items=dpgf_items,
            ai_source="Moteur Expert BTP Local (AFNOR / CSTB / CCAG Travaux)",
        )

    @classmethod
    def _extract_overview(cls, text: str) -> ProjectOverview:
        # Title extraction
        title = "Marché Public de Travaux BTP"
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for i, clean in enumerate(lines[:50]):
            if re.match(r"^(?:objet du marché|objet de la consultation|objet)\s*[:\-]?$", clean, re.IGNORECASE):
                if i + 1 < len(lines):
                    title = lines[i + 1].strip()
                    break
            elif re.search(r"^(?:objet du marché|objet de la consultation|objet)\s*[:\-]\s*(.+)$", clean, re.IGNORECASE):
                m = re.search(r"^(?:objet du marché|objet de la consultation|objet)\s*[:\-]\s*(.+)$", clean, re.IGNORECASE)
                cand = m.group(1).strip()
                if len(cand) > 5:
                    title = cand
                    break
            elif any(k in clean.lower() for k in ["travaux de", "rénovation énergétique", "mise aux normes", "réhabilitation acoustique", "construction de"]) and len(clean) > 20:
                title = clean
                break

        # Client (Maître d'Ouvrage)
        client = "Acheteur Public / Collectivité"
        for i, clean in enumerate(lines[:50]):
            if re.match(r"^(?:ma[îi]tre d['’]ouvrage|pouvoir adjudicateur|acheteur public)\s*[:\-]?$", clean, re.IGNORECASE):
                if i + 1 < len(lines):
                    client = lines[i + 1].strip()
                    break
        if client == "Acheteur Public / Collectivité":
            client_match = re.search(r"(?:ma[îi]tre d['’]ouvrage|pouvoir adjudicateur|acheteur public|commune de|mairie de|d[ée]partement de|région)\s*[:\-]?\s*([^\n\r,\.]{4,60})", text, re.IGNORECASE)
            if client_match:
                client = client_match.group(0).strip()
                if ":" in client:
                    client = client.split(":", 1)[1].strip()

        # Project manager (Maître d'Œuvre)
        moe = None
        for i, clean in enumerate(lines[:50]):
            if re.match(r"^(?:ma[îi]trise d['’][œo]uvre|architecte|bureau d['’][ée]tudes|moe)\s*[:\-]?$", clean, re.IGNORECASE):
                if i + 1 < len(lines):
                    moe = lines[i + 1].strip()
                    break
        if not moe:
            moe_match = re.search(r"(?:ma[îi]trise d['’][œo]uvre|architecte|bureau d['’][ée]tudes|moe)\s*[:\-]?\s*([^\n\r,\.]{4,60})", text, re.IGNORECASE)
            if moe_match:
                moe = moe_match.group(0).strip()
                if ":" in moe:
                    moe = moe.split(":", 1)[1].strip()

        # Location
        location = "Lieu d'exécution non spécifié"
        for i, clean in enumerate(lines[:50]):
            if re.match(r"^(?:lieu d['’]ex[ée]cution|adresse du chantier|site des travaux|chantier situ[ée]|lieu des travaux)\s*[:\-]?$", clean, re.IGNORECASE):
                if i + 1 < len(lines):
                    location = lines[i + 1].strip()
                    break
            elif re.search(r"^(?:lieu d['’]ex[ée]cution|adresse du chantier|site des travaux|chantier situ[ée]|lieu des travaux)\s*[:\-]\s*(.+)$", clean, re.IGNORECASE):
                m = re.search(r"^(?:lieu d['’]ex[ée]cution|adresse du chantier|site des travaux|chantier situ[ée]|lieu des travaux)\s*[:\-]\s*(.+)$", clean, re.IGNORECASE)
                cand = m.group(1).strip()
                if len(cand) > 5:
                    location = cand
                    break

        if location == "Lieu d'exécution non spécifié":
            # Look for postal code + city
            cp_match = re.search(r"\b(75\d{3}|77\d{3}|78\d{3}|91\d{3}|92\d{3}|93\d{3}|94\d{3}|95\d{3}|\d{5})\s+([A-ZÀ-ÿ\s\-]{3,30})", text)
            if cp_match:
                location = f"{cp_match.group(1)} {cp_match.group(2).strip()}"

        # Deadline (DLRO)
        deadline = "À vérifier sur le Règlement de Consultation (RC)"
        dlro_match = re.search(r"(?:date limite|remise des offres|remise des plis|dépôt des plis|au plus tard le)[^\n\r\d]{0,40}([0-3]?\d[\/\.\-][0-1]?\d[\/\.\-]202\d(?:\s*(?:[àa]|–)\s*\d{1,2}h(?:[0-5]\d)?)?)", text, re.IGNORECASE)
        if dlro_match:
            deadline = dlro_match.group(1).strip()

        # Duration
        duration = "Délai à préciser selon planning"
        dur_match = re.search(r"(?:d[ée]lai d['’]ex[ée]cution|dur[ée]e des travaux|p[ée]riode d['’]ex[ée]cution)\s*[:\-]?\s*([^\n\r\.]{4,60})", text, re.IGNORECASE)
        if dur_match:
            duration = dur_match.group(1).strip()
        else:
            m_months = re.search(r"\b(\d{1,2})\s*(?:mois|semaines|jours)\b", text, re.IGNORECASE)
            if m_months:
                duration = f"{m_months.group(0)} d'exécution prévisionnelle"

        # Lots
        lots = []
        lot_matches = re.findall(r"(?:Lot\s*(?:n°|no)?\s*\d{1,2}\s*[\-–:]\s*[^\n\r]{4,50})", text, re.IGNORECASE)
        if lot_matches:
            # Dedup and keep top 6
            seen = set()
            for l in lot_matches:
                cl = re.sub(r"\s+", " ", l).strip()
                if cl.lower() not in seen:
                    seen.add(cl.lower())
                    lots.append(cl)
                if len(lots) >= 6:
                    break
        if not lots:
            lots = ["Lot Unique / Tous Corps d'État (TCE)"]

        return ProjectOverview(
            title=title,
            client=client,
            project_manager=moe,
            location=location,
            submission_deadline=deadline,
            estimated_duration=duration,
            lots=lots,
            market_type="Marché Public de Travaux (MAPA / AOO)",
            estimated_budget="Selon décomposition DPGF",
        )

    @classmethod
    def _extract_norms(cls, text: str) -> List[TechnicalNorm]:
        found_norms: List[TechnicalNorm] = []
        detected_codes = set()

        # Search from knowledge base
        for code, info in BTP_NORM_DATABASE.items():
            pattern = re.escape(code)
            if re.search(r"\b" + pattern + r"\b", text, re.IGNORECASE):
                detected_codes.add(code)
                found_norms.append(
                    TechnicalNorm(
                        code=code,
                        title=info["title"],
                        lot=info["lot"],
                        requirement_level=info["level"],
                        description=info["desc"],
                        compliance_status="a_verifier",
                    )
                )

        # Catch additional DTU mentions not in primary dictionary
        generic_dtu = re.findall(r"\b(DTU\s*\d{1,2}(?:\.\d{1,2})?)\b", text, re.IGNORECASE)
        for g in generic_dtu:
            clean_g = re.sub(r"\s+", " ", g).upper()
            if clean_g not in detected_codes:
                detected_codes.add(clean_g)
                found_norms.append(
                    TechnicalNorm(
                        code=clean_g,
                        title=f"Document Technique Unifié BTP ({clean_g})",
                        lot="Bâtiment / Second Œuvre",
                        requirement_level="Obligatoire",
                        description="Règles de l'art et prescriptions techniques CSTB applicables à la mise en œuvre.",
                        compliance_status="a_verifier",
                    )
                )

        # Default fallback if text doesn't explicitly mention norms
        if not found_norms:
            found_norms.append(
                TechnicalNorm(
                    code="NF C 15-100 & DTU Métier",
                    title="Normes françaises et DTU applicables aux corps d'état du marché",
                    lot="Tous corps d'état",
                    requirement_level="Obligatoire",
                    description="Respect impératif des règles de l'art, du CCAG Travaux et des normes AFNOR en vigueur.",
                    compliance_status="conforme",
                )
            )

        return found_norms

    @classmethod
    def _extract_certifications(cls, text: str) -> List[CertificationRequired]:
        certifs = []
        checks = [
            ("Qualifelec", "Qualification professionnelle", "Exigé pour les travaux électriques d'envergure", "Qualifelec RGE / Logement Tertiaire"),
            ("Qualibat", "Qualification professionnelle", "Critère de sélection technique des compétences", "Qualibat (selon corps d'état)"),
            ("RGE", "Environnement / Énergie", "Indispensable pour l'éligibilité aux subventions énergétiques", "Mention RGE valide"),
            ("AIPR", "Sécurité réseaux", "Obligatoire pour les interventions à proximité des réseaux aériens et enterrés", "Attestation AIPR Opérateur/Encadrant"),
            ("CACES", "Sécurité manutention", "Requis pour la conduite de PEMP (nacelles) et engins de chantier", "CACES R486 / R482"),
            ("Habilitation", "Sécurité électrique", "Obligatoire selon la norme NF C 18-510 pour travaux d'électricité", "Habilitation B1V / B2V / BR / BC"),
            ("Sous-section 4", "Santé / Sécurité", "Obligatoire si intervention sur matériaux susceptibles de contenir de l'amiante", "Attestation compétence Amiante SS4"),
            ("Décennale", "Assurance légale", "Assurance décennale et RC Pro obligatoires dès la signature de l'acte d'engagement", "Attestation d'assurance décennale en cours de validité"),
        ]

        text_lower = text.lower()
        for kw, cat, desc, label in checks:
            if kw.lower() in text_lower:
                certifs.append(
                    CertificationRequired(
                        name=label,
                        category=cat,
                        is_mandatory=True,
                        penalty_if_missing="Rejet de la candidature pour non-conformité administrative",
                    )
                )

        # Always include Decennale assurance if none found
        if not any(c.category == "Assurance légale" for c in certifs):
            certifs.append(
                CertificationRequired(
                    name="Attestation d'Assurance Décennale et RC Pro",
                    category="Assurance légale",
                    is_mandatory=True,
                    penalty_if_missing="Offre irrecevable",
                )
            )

        return certifs

    @classmethod
    def _extract_financial_risks(cls, text: str) -> List[FinancialRisk]:
        risks = []
        # 1. Pénalités de retard
        pen_match = re.search(r"p[ée]nalit[ée]s?\s+de\s+retard[^\n\r\.]{0,100}(?:(\d+[\s\xa0]*€|\d+[\s\xa0]*euros|1\/\d+00|1\/1000|1\/2000|1\/3000)[^\n\r\.]*)", text, re.IGNORECASE)
        if pen_match:
            pen_clause = pen_match.group(0).strip()
            # Determine daily amount or fraction
            severity = "high" if any(k in pen_clause for k in ["500", "600", "700", "800", "1000", "sans mise en demeure"]) else "medium"
            risks.append(
                FinancialRisk(
                    type="Pénalité de retard journalière",
                    severity=severity,
                    clause_text=pen_clause,
                    impact_estimate="Pénalités appliquées de plein droit par jour de retard calendaire, déduites sur les situations mensuelles.",
                    recommendation="Verrouiller le planning d'approvisionnement des fournitures à long délai et notifier immédiatement par écrit tout retard imputable à d'autres lots.",
                )
            )
        else:
            risks.append(
                FinancialRisk(
                    type="Pénalité de retard contractuelle (CCAG Travaux)",
                    severity="medium",
                    clause_text="Application du barème standard CCAG Travaux (1/1000e du montant du marché par jour calendaire de retard).",
                    impact_estimate="Déduction financière directe sur le décompte général définitif (DGD).",
                    recommendation="Vérifier la date exacte de démarrage du délai (OS - Ordre de Service prescrivant le commencement des travaux).",
                )
            )

        # 2. Retenue de garantie (5%)
        rg_match = re.search(r"retenue\s+de\s+garantie[^\n\r\.]{0,80}(?:5\s*%|cinq\s*pour\s*cent)?", text, re.IGNORECASE)
        rg_text = rg_match.group(0).strip() if rg_match else "Retenue de garantie légale de 5% prélevée sur chaque acompte mensuel."
        risks.append(
            FinancialRisk(
                type="Retenue de garantie (5%)",
                severity="low",
                clause_text=rg_text,
                impact_estimate="5% du montant HT des situations de travaux bloqués pendant 1 an (délai de parfait achèvement).",
                recommendation="Substituer dès la notification une caution bancaire personnelle et solidaire (GAPD) pour préserver 100% de votre trésorerie courante.",
            )
        )

        # 3. Compte prorata / Dépenses communes
        if any(k in text.lower() for k in ["compte prorata", "prorata", "dépenses d'intérêt commun", "dépenses communes"]):
            prorata_match = re.search(r"compte\s+prorata[^\n\r\.]{0,100}", text, re.IGNORECASE)
            prorata_text = prorata_match.group(0).strip() if prorata_match else "Compte prorata géré par le lot gros œuvre (estimation 1.5% à 2.5% du montant du lot)."
            risks.append(
                FinancialRisk(
                    type="Compte prorata de chantier",
                    severity="medium",
                    clause_text=prorata_text,
                    impact_estimate="Prélèvement de 1.5% à 2.5% sur le montant global du marché pour charges communes (eau, électricité provisoire, bennes).",
                    recommendation="Exiger les comptes-rendus de la commission de contrôle prorata et contester toute charge d'énergie disproportionnée.",
                )
            )

        # 4. Délais de paiement & Intérêts moratoires
        risks.append(
            FinancialRisk(
                type="Délai de paiement administratif (30 jours)",
                severity="low",
                clause_text="Paiement par virement administratif dans le délai réglementaire de 30 jours à compter de la réception de la demande d'acompte (Chorus Pro).",
                impact_estimate="Décalage de trésorerie de 45 à 60 jours réels entre l'achat des fournitures et le virement du Trésor Public.",
                recommendation="Déposer sans faute le projet de décompte mensuel avant le 25 de chaque mois sur Chorus Pro avec le numéro d'engagement juridique (EJ).",
            )
        )

        # 5. Formule de révision des prix
        if "prix ferme" in text.lower():
            risks.append(
                FinancialRisk(
                    type="Prix ferme non révisable",
                    severity="high",
                    clause_text="Les prix du présent marché sont réputés fermes et non actualisables pour toute la durée des travaux.",
                    impact_estimate="Risque d'érosion de marge en cas de hausse imprévue des cours des métaux (cuivre, acier) ou matériaux.",
                    recommendation="Intégrer une provision de sécurité de 3% à 5% dans le prix unitaire des fournitures sensibles.",
                )
            )
        else:
            risks.append(
                FinancialRisk(
                    type="Clause de révision de prix (Index BT)",
                    severity="low",
                    clause_text="Prix révisables mensuellement selon l'indexation officielle du bâtiment (Index BT applicable au corps d'état).",
                    impact_estimate="Protection relative contre l'inflation des coûts de main d'œuvre et des matériaux.",
                    recommendation="Mentionner l'index BT01 ou BT spécifique sur l'acte d'engagement pour faire valoir les coefficients de révision.",
                )
            )

        return risks

    @classmethod
    def _calculate_go_no_go(
        cls,
        overview: ProjectOverview,
        risks: List[FinancialRisk],
        norms: List[TechnicalNorm],
        certifs: List[CertificationRequired],
        dpgf: List[DPGFItem],
    ) -> GoNoGoScore:
        """Computes risk factor scores and produces an immediate 60-second Go / No-Go verdict."""
        # Baseline scores
        delay_score = 75
        financial_score = 80
        technical_score = 85
        admin_score = 80

        red_flags: List[str] = []
        amber_warnings: List[str] = []
        green_lights: List[str] = []

        # Analyze risks
        for r in risks:
            if r.severity == "high":
                financial_score -= 20
                if "pénalité" in r.type.lower():
                    red_flags.append(f"Pénalité de retard élevée : {r.clause_text[:90]}")
                elif "prix ferme" in r.type.lower():
                    amber_warnings.append("Prix ferme sans révision : attention à la volatilité des coûts matériaux.")
            elif r.severity == "medium":
                financial_score -= 10
                if "compte prorata" in r.type.lower():
                    amber_warnings.append("Compte prorata actif : anticiper une retenue inter-entreprises de 1.5% à 2.5%.")

        # Analyze deadlines
        dur_lower = overview.estimated_duration.lower()
        if any(k in dur_lower for k in ["1 mois", "2 mois", "3 semaines", "4 semaines", "très court", "urgent"]):
            delay_score -= 25
            amber_warnings.append("Planning d'intervention serré : risque d'embouteillage avec les autres corps d'état.")
        else:
            delay_score += 10
            green_lights.append("Délai de réalisation standard : planning jugé réaliste pour un artisan ou une PME.")

        # Analyze norms & certifs
        if len(certifs) > 3:
            admin_score -= 10
            amber_warnings.append(f"{len(certifs)} qualifications et attestations exigées : vérifier la validité de vos dossiers.")
        else:
            green_lights.append("Exigences administratives accessibles sans certification exotique.")

        if any("rge" in c.name.lower() for c in certifs):
            green_lights.append("Marché éligible aux aides à la rénovation énergétique.")

        # Analyze DPGF grid
        if dpgf and len(dpgf) > 0:
            green_lights.append(f"Bordereau de prix structuré fourni ({len(dpgf)} postes métrés identifiés).")
        else:
            amber_warnings.append("DPGF non fournie ou non analysée : métrés à calculer entièrement à partir des plans.")

        # Clamp scores 0-100
        delay_score = max(20, min(100, delay_score))
        financial_score = max(20, min(100, financial_score))
        technical_score = max(20, min(100, technical_score))
        admin_score = max(20, min(100, admin_score))

        # Overall weighted score
        overall = int(round(delay_score * 0.25 + financial_score * 0.35 + technical_score * 0.20 + admin_score * 0.20))

        # Verdict
        if len(red_flags) >= 2 or overall < 55:
            verdict = "NO_GO"
            summary = (
                f"VERDICT NO-GO ({overall}/100) : Ce dossier présente des contraintes financières ou pénales disproportionnées. "
                f"Les pénalités de retard et les clauses contractuelles exposent l'artisan à un risque d'érosion complète de la marge "
                f"en cas de dérive de planning. Candidature déconseillée sauf négociation écrite préalable."
            )
        elif overall < 80:
            verdict = "GO_AVEC_RESERVES"
            summary = (
                f"VERDICT GO AVEC RÉSERVES ({overall}/100) : Marché opportun et techniquement accessible pour votre corps d'état, "
                f"sous réserve de sécuriser l'approvisionnement des fournitures et de substituer la retenue de garantie de 5% "
                f"par une caution bancaire pour préserver votre trésorerie."
            )
        else:
            verdict = "GO"
            summary = (
                f"VERDICT GO FRANCO ({overall}/100) : Excellent dossier de consultation public. Délais d'exécution équilibrés, "
                f"clauses financières standards conformes au CCAG Travaux et volumétrie de travaux adaptée. Candidature vivement recommandée."
            )

        return GoNoGoScore(
            verdict=verdict,
            overall_score=overall,
            delay_score=delay_score,
            financial_risk_score=financial_score,
            technical_norm_score=technical_score,
            admin_feasibility_score=admin_score,
            executive_summary=summary,
            red_flags=red_flags,
            amber_warnings=amber_warnings,
            green_lights=green_lights,
        )

    @classmethod
    def _analyze_with_gemini(
        cls,
        text: str,
        dpgf_items: List[DPGFItem],
        filename_cctp: str,
        filename_dpgf: Optional[str],
        api_key: str,
    ) -> Optional[TenderAnalysis]:
        """Calls official Gemini API using the modern google-genai Client."""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Limit text length to avoid overflow while keeping rich content
            truncated_text = text[:35000]

            prompt = f"""Tu es un métreur et juriste spécialisé en marchés publics de travaux BTP en France.
Analyse le document suivant (CCTP / CCAP) pour un artisan ou une entreprise du bâtiment (PME).
Extrais avec la plus grande rigueur les informations techniques, juridiques et financières.

Retourne UNIQUEMENT un objet JSON valide respectant rigoureusement ce schéma :
{{
  "overview": {{
    "title": "Intitulé du marché",
    "client": "Maître d'Ouvrage",
    "project_manager": "Maître d'Œuvre ou null",
    "location": "Lieu d'exécution",
    "submission_deadline": "Date limite de remise des offres",
    "estimated_duration": "Durée prévisionnelle",
    "lots": ["Lot 1...", "Lot 2..."],
    "market_type": "MAPA / Appel d'offres",
    "estimated_budget": "Montant ou Non communiqué"
  }},
  "technical_norms": [
    {{
      "code": "NF C 15-100",
      "title": "Titre",
      "lot": "Lot",
      "requirement_level": "Obligatoire",
      "description": "Prescription extraite",
      "compliance_status": "a_verifier"
    }}
  ],
  "certifications": [
    {{
      "name": "Qualifelec / Qualibat / RGE",
      "category": "Qualification pro / Sécurité",
      "is_mandatory": true,
      "penalty_if_missing": "Rejet"
    }}
  ],
  "financial_risks": [
    {{
      "type": "Pénalité de retard / Retenue de garantie / Compte prorata",
      "severity": "high/medium/low",
      "clause_text": "Texte exact de la clause",
      "impact_estimate": "Impact chiffré",
      "recommendation": "Conseil opérationnel pour l'artisan"
    }}
  ],
  "scoring": {{
    "verdict": "GO ou GO_AVEC_RESERVES ou NO_GO",
    "overall_score": 75,
    "delay_score": 70,
    "financial_risk_score": 80,
    "technical_norm_score": 85,
    "admin_feasibility_score": 75,
    "executive_summary": "Synthèse de 3 phrases pour l'artisan",
    "red_flags": ["point bloquant 1"],
    "amber_warnings": ["point vigilance 1"],
    "green_lights": ["atout 1"]
  }}
}}

TEXTE DU CCTP/CCAP :
{truncated_text}
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            if response.text:
                data = json.loads(response.text)
                return TenderAnalysis(
                    id=f"BTP-AI-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    filename_cctp=filename_cctp,
                    filename_dpgf=filename_dpgf,
                    analysis_timestamp=datetime.now().strftime("%d/%m/%Y à %H:%M"),
                    overview=ProjectOverview(**data["overview"]),
                    technical_norms=[TechnicalNorm(**n) for n in data.get("technical_norms", [])],
                    certifications=[CertificationRequired(**c) for c in data.get("certifications", [])],
                    financial_risks=[FinancialRisk(**r) for r in data.get("financial_risks", [])],
                    scoring=GoNoGoScore(**data["scoring"]),
                    dpgf_items=dpgf_items,
                    ai_source="Google Gemini 2.5 Flash AI + Règles BTP",
                )
        except Exception as e:
            logger.error(f"Gemini API execution error: {e}")
            return None
        return None
