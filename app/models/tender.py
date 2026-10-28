from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectOverview(BaseModel):
    title: str = Field(description="Intitulé officiel du marché ou de la consultation")
    client: str = Field(description="Maître d'Ouvrage (Acheteur public / collectivité)")
    project_manager: Optional[str] = Field(default=None, description="Maître d'Œuvre (Architecte / Bureau d'études)")
    location: str = Field(description="Lieu d'exécution des travaux (adresse et code postal)")
    submission_deadline: str = Field(description="Date et heure limites de remise des plis (DLRO)")
    estimated_duration: str = Field(description="Durée ou délai d'exécution prévisionnel")
    lots: List[str] = Field(default_factory=list, description="Lots concernés par la consultation")
    market_type: str = Field(default="Marché Public de Travaux (MAPA / Appel d'Offres Ouvert)", description="Forme du marché")
    estimated_budget: Optional[str] = Field(default="Non communiqué / À chiffrer selon DPGF", description="Budget prévisionnel ou enveloppe")

class TechnicalNorm(BaseModel):
    code: str = Field(description="Référence de la norme ou du DTU (ex: NF C 15-100, DTU 40.21)")
    title: str = Field(description="Intitulé officiel de la norme")
    lot: str = Field(default="Tous corps d'état", description="Corps d'état ou lot concerné")
    requirement_level: str = Field(default="Obligatoire", description="Niveau d'exigence (Obligatoire, Recommandé, Contrôle)")
    description: str = Field(description="Description synthétique de l'exigence dans le CCTP")
    compliance_status: str = Field(default="a_verifier", description="Statut de conformité: conforme, a_verifier, non_conforme")

class CertificationRequired(BaseModel):
    name: str = Field(description="Nom de la qualification ou certification (ex: Qualifelec RGE, Qualibat 5112)")
    category: str = Field(description="Catégorie: Qualification professionnelle, Sécurité, Assurance, Environnement")
    is_mandatory: bool = Field(default=True, description="Indispensable sous peine d'élimination")
    penalty_if_missing: str = Field(default="Offre déclarée irrecevable ou rejetée", description="Conséquence de l'absence")

class FinancialRisk(BaseModel):
    type: str = Field(description="Type de clause (Pénalités, Retenue de garantie, Compte prorata, Résiliation, Révision des prix)")
    severity: str = Field(description="Niveau de criticité: high, medium, low")
    clause_text: str = Field(description="Citation ou résumé fidèle de la clause contractuelle")
    impact_estimate: str = Field(description="Impact financier chiffré ou opérationnel concret")
    recommendation: str = Field(description="Conseil tactique et parade opérationnelle pour l'artisan")

class GoNoGoScore(BaseModel):
    verdict: str = Field(description="Décision: GO, GO_AVEC_RESERVES, NO_GO")
    overall_score: int = Field(ge=0, le=100, description="Score global de faisabilité sur 100")
    delay_score: int = Field(ge=0, le=100, description="Score faisabilité planning / délais")
    financial_risk_score: int = Field(ge=0, le=100, description="Score sécurité financière / pénalités")
    technical_norm_score: int = Field(ge=0, le=100, description="Score accessibilité technique et normes")
    admin_feasibility_score: int = Field(ge=0, le=100, description="Score accessibilité administrative")
    executive_summary: str = Field(description="Synthèse stratégique d'aide à la décision en 3-4 phrases")
    red_flags: List[str] = Field(default_factory=list, description="Points de blocage critiques (causes de No-Go immédiat)")
    amber_warnings: List[str] = Field(default_factory=list, description="Points de vigilance contractuelle et risques mesurés")
    green_lights: List[str] = Field(default_factory=list, description="Atouts et points favorables du dossier")

class DPGFItem(BaseModel):
    item_number: str = Field(default="", description="Numéro de ligne ou code prestation (ex: 1.1, 2.3)")
    designation: str = Field(description="Description de l'ouvrage ou fourniture")
    unit: str = Field(default="u", description="Unité de mesure (m², ml, u, ens, forfait, h)")
    quantity: float = Field(default=1.0, description="Quantité métrée")
    unit_price: Optional[float] = Field(default=0.0, description="Prix unitaire HT estimé ou proposé")
    total_price: Optional[float] = Field(default=0.0, description="Total HT de la ligne")
    lot: str = Field(default="Principal", description="Lot ou section du bordereau")

class TenderAnalysis(BaseModel):
    id: str = Field(description="Identifiant unique de l'analyse")
    filename_cctp: str = Field(description="Nom du fichier CCTP / CCAP analysé")
    filename_dpgf: Optional[str] = Field(default=None, description="Nom du fichier DPGF / BPU analysé")
    analysis_timestamp: str = Field(description="Horodatage de l'analyse")
    overview: ProjectOverview
    technical_norms: List[TechnicalNorm] = Field(default_factory=list)
    certifications: List[CertificationRequired] = Field(default_factory=list)
    financial_risks: List[FinancialRisk] = Field(default_factory=list)
    scoring: GoNoGoScore
    dpgf_items: List[DPGFItem] = Field(default_factory=list)
    ai_source: str = Field(default="Moteur Expert BTP Local (AFNOR/CSTB/Code Marchés)", description="Moteur d'analyse utilisé")
