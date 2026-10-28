# 🏗️ BTP Public Tender Analyzer (Analyseur d'Appels d'Offres BTP)

Application web de pointe conçue spécifiquement pour les **artisans, PME du bâtiment, électriciens, plombiers, plâtriers et entreprises de travaux publics** en France.

Elle permet d'analyser en **60 secondes chrono** n'importe quel dossier d'appel d'offres public (CCTP, CCAP, RC) et son bordereau de prix (DPGF / BPU) pour rendre un verdict d'opportunité immédiat (**GO / GO AVEC RÉSERVES / NO-GO**), détecter les pièges contractuels cachés et estimer la rentabilité financière.

---

## ✨ Fonctionnalités Clés

1. **Tableau de bord de dépôt drag-and-drop** :
   - Zone de glisser-déposer pour les CCTP / CCAP (au format PDF ou TXT).
   - Zone dédiée pour la grille tarifaire DPGF / BPU (Excel `.xlsx`, `.xls` ou `.csv`).
   - Deux dossiers d'exemples BTP réels intégrés en 1 clic (*Rénovation Électrique Groupe Scolaire* et *Plâtrerie / Acoustique Médiathèque*).

2. **Moteur d'Analyse Réglementaire BTP & IA Gemini** :
   - **Mode Autonome Zéro Frais** : Moteur expert local basé sur les règles de l'art du bâtiment (AFNOR, CSTB, DTU, CCAG Travaux 2026, Code de la commande publique).
   - **Mode IA Gemini** : Compatible avec le nouveau SDK officiel `google-genai` (modèle `gemini-2.5-flash`) dès qu'une clé API est configurée.
   - Extraction ciblée :
     - *Identification & Délais* : Objet, Maître d'ouvrage, Maître d'œuvre, Lieu, Date limite (DLRO), Durée d'exécution, Lots.
     - *Normes DTU & Réglementations* : NF C 15-100, NF C 14-100, NF EN 12464-1, DTU 25.41, DTU 58.1, DTU 20.1, DTU 40.x, DTU 43.1, DTU 60.1, etc.
     - *Certifications requises* : Qualifelec, Qualibat, RGE, AIPR, CACES, Habilitations électriques, SS4, Assurance décennale.
     - *Clauses financières & pénalités cachées* : Pénalités de retard journalières, retenue de garantie (5%), compte prorata (1.5%-2.5%), délais de paiement Chorus Pro (30j), révision des prix (Index BT).

3. **Fiche Décisionnelle 60s & Synthèse Stratégique** :
   - Verdict immédiat : **GO FRANCO**, **GO AVEC RÉSERVES**, **NO-GO**.
   - Score global de faisabilité sur 100 et décomposition en 4 dimensions (Planning, Risque Financier, Normes DTU, Dossier Administratif).
   - 3 colonnes d'aide à la décision : 🔴 Points Bloquants (Red Flags), 🟡 Vigilance & Risques, 🟢 Points Forts.

4. **Grille DPGF & Simulateur de Marges BTP** :
   - Métré interactif des postes avec modification en direct des prix unitaires.
   - Simulateur de marge : calcul automatique du Déboursé Sec, Frais Généraux (%), Marge Nette (%), Prix de Vente HT conseillé, TVA et Total TTC.

5. **Exports Autonomes & Checklist Dépôt** :
   - **Export PDF Officiel** : Génération server-side via `ReportLab` d'une fiche décisionnelle prête pour les réunions de chiffrage.
   - **Export Excel Chiffrage** : Génération via `openpyxl` d'un classeur à 4 onglets avec formules de calculs automatiques.
   - **Export CSV** : Compatible avec vos logiciels de devis/facturation BTP (Batappli, Obat, ProDevis, Sage, etc.).
   - **Checklist Dépôt** : Suivi des 8 pièces administratives obligatoires (DC1, DC2, DUME, Décennale, Mémoire technique, DPGF).

---

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.10 ou supérieur

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancement du serveur
```bash
python run.py
```
ou directement :
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Accès à l'application
Ouvrez votre navigateur sur : **`http://localhost:8000`**

Documentation interactive OpenAPI / Swagger : **`http://localhost:8000/docs`**

---

## 📁 Structure du Projet

```text
btp-tender-analyzer/
├── README.md                      # Documentation complète
├── requirements.txt               # Dépendances Python
├── run.py                         # Script de démarrage direct
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application FastAPI & configuration CORS/static
│   ├── config.py                  # Chemins, extensions autorisées, constantes
│   ├── models/
│   │   ├── __init__.py
│   │   └── tender.py              # Schémas Pydantic (ProjectOverview, Risks, DPGF...)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py          # Extraction PDF via PyMuPDF (fitz)
│   │   ├── dpgf_parser.py         # Parsing grilles Excel/CSV via openpyxl & pandas
│   │   ├── analyzer.py            # Moteur Expert BTP Local + Intégration Gemini 2.5 Flash
│   │   ├── exporter.py            # Générateur ReportLab PDF & openpyxl Excel
│   │   └── sample_data.py         # Données d'exemples réalistes (École & Médiathèque)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # Endpoints REST (/upload, /load-sample, /export/...)
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css         # Styles sur-mesure & règles d'impression @media print
│   │   ├── js/
│   │   │   └── app.js             # Logique frontend, drag&drop, simulateur de marge
│   │   └── samples/               # Fichiers PDF et Excel de démonstration
│   └── templates/
│       └── index.html             # Interface responsive Tailwind CSS haute lisibilité
```

---

## 🔑 Configuration Optionnelle de l'API Google Gemini

L'application fonctionne **100% hors-ligne et sans clé d'API** grâce à son moteur d'extraction expert BTP.

Si vous souhaitez activer l'IA multimodale générative Google Gemini 2.5 Flash :
1. Définissez la variable d'environnement :
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="votre_clé_api"
   
   # Linux / macOS
   export GEMINI_API_KEY="votre_clé_api"
   ```
2. Ou saisissez directement votre clé dans l'interface via le bouton **"Clé Gemini (Optionnelle)"** en haut à droite.

---

## 📄 Licence
Ce projet est développé pour assister les entreprises du secteur du bâtiment dans l'analyse de leurs marchés publics et privés.
