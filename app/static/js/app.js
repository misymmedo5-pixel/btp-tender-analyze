/**
 * BTP Public Tender Analyzer - SaaS B2B Application Logic
 */

/**
 * BTP Public Tender Analyzer - SaaS B2B Application Logic
 */

const DEFAULT_HISTORY = [
    {
        id: 'BTP-20261028-01',
        date: '28/10/2026 à 14:30',
        title: 'Rénovation énergétique et mise aux normes électriques - École Pasteur',
        client: 'Mairie de Saint-Germain-en-Laye',
        score: 66,
        verdict: 'GO_AVEC_RESERVES',
        sampleId: '1'
    },
    {
        id: 'BTP-20261028-02',
        date: '28/10/2026 à 11:15',
        title: 'Réhabilitation acoustique et faux-plafonds - Nouvelle Médiathèque',
        client: 'Grand Paris Ouest',
        score: 66,
        verdict: 'GO_AVEC_RESERVES',
        sampleId: '2'
    },
    {
        id: 'BTP-20261028-03',
        date: '28/10/2026 à 09:40',
        title: 'Rénovation plomberie sanitaire, ECS & VMC double flux - Crèche Municipale',
        client: 'Ville de Nanterre',
        score: 72,
        verdict: 'GO_AVEC_RESERVES',
        sampleId: '3'
    }
];

const DEFAULT_CHECKLIST = [
    { id: 'dc1', label: 'Lettre de candidature DC1 (ou DUME acheteur dématérialisé)', category: 'candidature', required: true, checked: true },
    { id: 'dc2', label: 'Déclaration du candidat DC2 (chiffre d’affaires sur les 3 derniers exercices)', category: 'candidature', required: true, checked: true },
    { id: 'kbis', label: 'Extrait Kbis de moins de 3 mois & attestations fiscales / URSSAF', category: 'candidature', required: true, checked: true },
    { id: 'attri1', label: 'Acte d’engagement ATTRI1 signé avec vos coordonnées bancaires', category: 'offre', required: true, checked: false },
    { id: 'dpgf', label: 'Bordereau DPGF / BPU complété, vérifié et sans omission de prix', category: 'offre', required: true, checked: true },
    { id: 'memoire', label: 'Mémoire Technique BTP personnalisé (organisation, moyens, planning prévisionnel)', category: 'offre', required: true, checked: false },
    { id: 'rib', label: 'Relevé d’Identité Bancaire (RIB) officiel de l’entreprise', category: 'offre', required: true, checked: true },
    { id: 'decennale', label: 'Attestation d’Assurance Décennale & Responsabilité Civile Professionnelle valide', category: 'specifique', required: true, checked: true },
    { id: 'hab', label: 'Habilitations électriques (NF C 18-510) & AIPR pour le personnel d’intervention', category: 'specifique', required: true, checked: true },
    { id: 'qualifs', label: 'Certificats de qualifications professionnelles exigées (Qualifelec, Qualibat, RGE)', category: 'specifique', required: true, checked: false },
];

function getStoredJson(key, defaultVal) {
    try {
        const val = localStorage.getItem(key);
        return val ? JSON.parse(val) : defaultVal;
    } catch {
        return defaultVal;
    }
}

// Application State
const AppState = {
    currentView: 'landing', // 'landing' | 'dashboard'
    currentSidebarTab: 'nouvelle-analyse',
    cctpFile: null,
    dpgfFile: null,
    currentAnalysis: null,
    geminiApiKey: localStorage.getItem('btp_gemini_api_key') || '',
    activeTab: 'synthese',
    marginSettings: {
        fraisGenerauxPct: 12.0,
        margeNettePct: 15.0,
        tvaPct: 20.0
    },
    dpgfFilter: '',
    historyFilter: 'ALL',
    historySearch: '',
    checklistFilter: 'all',
    history: getStoredJson('btp_analysis_history', DEFAULT_HISTORY),
    checklist: getStoredJson('btp_submission_checklist', DEFAULT_CHECKLIST),
    companyProfile: getStoredJson('btp_company_profile', {
        company: 'SAS Artisan BTP Travaux',
        siret: '849 123 456 00012',
        trade: 'Électricité générale & CFO/CFA',
        contact: 'Jean Dupont (Gérant)',
        insurance: 'SMABTP (Police N° 987654321 - Valide)',
        qualifs: 'Qualifelec RGE E2-C2, Qualibat 4112'
    })
};

// DOM Initializer
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const hash = window.location.hash;
    const urlParams = new URLSearchParams(window.location.search);

    if (path.includes('/app') || hash === '#app' || urlParams.get('view') === 'app') {
        switchToDashboard();
    } else {
        switchToLanding();
    }

    initDragAndDrop();
    initEventListeners();
    checkEngineStatus();
    loadSavedApiKey();
    loadSavedCompanyProfile();
    renderChecklist();
    renderHistoryTable();
    calculateRoi();
    calculateQuickMargin();

    if (window.lucide) {
        lucide.createIcons();
    }
});

// View Switching Functions
function switchToDashboard() {
    AppState.currentView = 'dashboard';
    const landing = document.getElementById('landing-page-view');
    const dash = document.getElementById('dashboard-view');
    if (landing) landing.classList.add('hidden');
    if (dash) dash.classList.remove('hidden');

    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (window.lucide) {
        lucide.createIcons();
    }
}

function switchToLanding() {
    AppState.currentView = 'landing';
    const landing = document.getElementById('landing-page-view');
    const dash = document.getElementById('dashboard-view');
    if (landing) landing.classList.remove('hidden');
    if (dash) dash.classList.add('hidden');

    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (window.lucide) {
        lucide.createIcons();
    }
}

function switchToDashboardAndLoadSample(sampleId) {
    switchToDashboard();
    switchSidebarTab('nouvelle-analyse');
    loadSample(sampleId);
}

// Sidebar Navigation
function switchSidebarTab(tabName) {
    AppState.currentSidebarTab = tabName;
    const subviews = ['nouvelle-analyse', 'historique', 'simulateur', 'checklist', 'compte'];

    subviews.forEach(v => {
        const el = document.getElementById(`subview-${v}`);
        const btn = document.getElementById(`nav-btn-${v}`);
        if (el) {
            if (v === tabName) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        }
        if (btn) {
            if (v === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });

    const titleMap = {
        'nouvelle-analyse': 'Nouvelle Analyse de Marché',
        'historique': 'Historique de vos Dossiers',
        'simulateur': 'Simulateur de Marges & Déboursé Sec',
        'checklist': 'Checklist Candidature Marchés Publics',
        'compte': 'Mon Compte & Formule Pro (300 € / an)'
    };

    const titleEl = document.getElementById('workspace-title');
    if (titleEl && titleMap[tabName]) {
        titleEl.textContent = titleMap[tabName];
    }

    if (tabName === 'simulateur') {
        renderSimulatorSubView();
    } else if (tabName === 'checklist') {
        renderChecklist();
    } else if (tabName === 'compte') {
        loadSavedCompanyProfile();
    } else if (tabName === 'historique') {
        renderHistoryTable();
    }

    if (window.lucide) {
        lucide.createIcons();
    }
}

function initEventListeners() {
    // File inputs
    const cctpInput = document.getElementById('cctp-file-input');
    const dpgfInput = document.getElementById('dpgf-file-input');
    
    if (cctpInput) {
        cctpInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleCctpFile(e.target.files[0]);
            }
        });
    }

    if (dpgfInput) {
        dpgfInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                handleDpgfFile(e.target.files[0]);
            }
        });
    }

    // Launch Analysis Button
    const btnLaunch = document.getElementById('btn-launch-analysis');
    if (btnLaunch) {
        btnLaunch.addEventListener('click', launchAnalysis);
    }

    // Sample Loaders
    const btnSample1 = document.getElementById('btn-sample-1');
    const btnSample2 = document.getElementById('btn-sample-2');
    const btnSample3 = document.getElementById('btn-sample-3');
    if (btnSample1) btnSample1.addEventListener('click', () => loadSample('1'));
    if (btnSample2) btnSample2.addEventListener('click', () => loadSample('2'));
    if (btnSample3) btnSample3.addEventListener('click', () => loadSample('3'));

    // Landing Page ROI Sliders
    const sliderAo = document.getElementById('roi-slider-ao');
    const sliderHours = document.getElementById('roi-slider-hours');
    const sliderRate = document.getElementById('roi-slider-rate');
    if (sliderAo) sliderAo.addEventListener('input', calculateRoi);
    if (sliderHours) sliderHours.addEventListener('input', calculateRoi);
    if (sliderRate) sliderRate.addEventListener('input', calculateRoi);

    // History Search Input
    const inputHistorySearch = document.getElementById('history-search-input');
    if (inputHistorySearch) {
        inputHistorySearch.addEventListener('input', (e) => {
            AppState.historySearch = e.target.value.toLowerCase().trim();
            renderHistoryTable();
        });
    }

    // Export Buttons
    const btnExportPdf = document.getElementById('btn-export-pdf');
    const btnExportExcel = document.getElementById('btn-export-excel');
    const btnExportCsv = document.getElementById('btn-export-csv');
    const btnPrint = document.getElementById('btn-print-summary');

    if (btnExportPdf) btnExportPdf.addEventListener('click', exportPdf);
    if (btnExportExcel) btnExportExcel.addEventListener('click', exportExcel);
    if (btnExportCsv) btnExportCsv.addEventListener('click', exportCsv);
    if (btnPrint) btnPrint.addEventListener('click', () => window.print());

    // Navigation Tabs in Results Section
    const tabButtons = document.querySelectorAll('.nav-tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            switchTab(target);
        });
    });

    // DPGF Margin Calculator Inputs
    const inputFg = document.getElementById('calc-fg');
    const inputMarge = document.getElementById('calc-marge');
    const selectTva = document.getElementById('calc-tva');
    const inputSearchDpgf = document.getElementById('dpgf-search-input');

    if (inputFg) {
        inputFg.addEventListener('input', (e) => {
            AppState.marginSettings.fraisGenerauxPct = parseFloat(e.target.value) || 0;
            recalculateMargins();
        });
    }
    if (inputMarge) {
        inputMarge.addEventListener('input', (e) => {
            AppState.marginSettings.margeNettePct = parseFloat(e.target.value) || 0;
            recalculateMargins();
        });
    }
    if (selectTva) {
        selectTva.addEventListener('change', (e) => {
            AppState.marginSettings.tvaPct = parseFloat(e.target.value) || 20;
            recalculateMargins();
        });
    }
    if (inputSearchDpgf) {
        inputSearchDpgf.addEventListener('input', (e) => {
            AppState.dpgfFilter = e.target.value.toLowerCase().trim();
            renderDpgfTable();
        });
    }

    // API Key Modal
    const btnOpenApiKey = document.getElementById('btn-open-api-modal');
    const btnCloseApiKey = document.getElementById('btn-close-api-modal');
    const btnSaveApiKey = document.getElementById('btn-save-api-key');
    const modalApiKey = document.getElementById('api-key-modal');

    if (btnOpenApiKey && modalApiKey) {
        btnOpenApiKey.addEventListener('click', () => {
            modalApiKey.classList.remove('hidden');
            const keyInput = document.getElementById('api-key-input');
            if (keyInput) keyInput.value = AppState.geminiApiKey;
        });
    }
    if (btnCloseApiKey && modalApiKey) {
        btnCloseApiKey.addEventListener('click', () => {
            modalApiKey.classList.add('hidden');
        });
    }
    if (btnSaveApiKey && modalApiKey) {
        btnSaveApiKey.addEventListener('click', () => {
            const keyInput = document.getElementById('api-key-input');
            const val = keyInput ? keyInput.value.trim() : '';
            AppState.geminiApiKey = val;
            localStorage.setItem('btp_gemini_api_key', val);
            modalApiKey.classList.add('hidden');
            updateEngineStatusBadge(val ? 'Gemini AI Connecté' : 'Moteur Expert BTP Actif', !!val);
            showToast('Clé enregistrée', 'La configuration de l’API a été mise à jour.', 'success');
        });
    }
}

function initDragAndDrop() {
    const cctpDropzone = document.getElementById('cctp-dropzone');
    const dpgfDropzone = document.getElementById('dpgf-dropzone');

    setupDropTarget(cctpDropzone, (file) => handleCctpFile(file));
    setupDropTarget(dpgfDropzone, (file) => handleDpgfFile(file));
}

function setupDropTarget(element, fileHandler) {
    if (!element) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        element.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            element.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        element.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            element.classList.remove('dropzone-active');
        }, false);
    });

    element.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            fileHandler(files[0]);
        }
    });
}

function handleCctpFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf') && !file.name.toLowerCase().endsWith('.txt')) {
        showToast('Format non supporté', 'Veuillez déposer un fichier CCTP ou CCAP au format PDF ou TXT.', 'warning');
        return;
    }
    AppState.cctpFile = file;
    
    const label = document.getElementById('cctp-file-label');
    const preview = document.getElementById('cctp-file-preview');
    const nameEl = document.getElementById('cctp-file-name');
    const sizeEl = document.getElementById('cctp-file-size');

    if (label) label.classList.add('hidden');
    if (preview) preview.classList.remove('hidden');
    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = formatFileSize(file.size);

    updateLaunchButtonState();
}

function removeCctpFile(e) {
    if (e) e.stopPropagation();
    AppState.cctpFile = null;
    const label = document.getElementById('cctp-file-label');
    const preview = document.getElementById('cctp-file-preview');
    if (label) label.classList.remove('hidden');
    if (preview) preview.classList.add('hidden');
    const input = document.getElementById('cctp-file-input');
    if (input) input.value = '';
    updateLaunchButtonState();
}

function handleDpgfFile(file) {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.xlsx', '.xls', '.csv'].includes(ext)) {
        showToast('Format non supporté', 'Veuillez déposer une grille DPGF au format Excel (.xlsx/.xls) ou CSV.', 'warning');
        return;
    }
    AppState.dpgfFile = file;

    const label = document.getElementById('dpgf-file-label');
    const preview = document.getElementById('dpgf-file-preview');
    const nameEl = document.getElementById('dpgf-file-name');
    const sizeEl = document.getElementById('dpgf-file-size');

    if (label) label.classList.add('hidden');
    if (preview) preview.classList.remove('hidden');
    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = formatFileSize(file.size);
}

function removeDpgfFile(e) {
    if (e) e.stopPropagation();
    AppState.dpgfFile = null;
    const label = document.getElementById('dpgf-file-label');
    const preview = document.getElementById('dpgf-file-preview');
    if (label) label.classList.remove('hidden');
    if (preview) preview.classList.add('hidden');
    const input = document.getElementById('dpgf-file-input');
    if (input) input.value = '';
}

function updateLaunchButtonState() {
    const btn = document.getElementById('btn-launch-analysis');
    if (!btn) return;
    if (AppState.cctpFile) {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
    } else {
        btn.disabled = true;
        btn.classList.add('opacity-50', 'cursor-not-allowed');
    }
}

async function launchAnalysis() {
    if (!AppState.cctpFile) {
        showToast('Fichier manquant', 'Veuillez d’abord sélectionner un CCTP (PDF).', 'warning');
        return;
    }

    showProgressStepper(true);

    const formData = new FormData();
    formData.append('cctp_file', AppState.cctpFile);
    if (AppState.dpgfFile) {
        formData.append('dpgf_file', AppState.dpgfFile);
    }
    if (AppState.geminiApiKey) {
        formData.append('gemini_api_key', AppState.geminiApiKey);
    }

    try {
        simulateStepperProgress();
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Erreur lors du traitement du dossier.');
        }

        const analysis = await response.json();
        AppState.currentAnalysis = analysis;
        finishProgressStepper();
        renderAnalysisResults(analysis);
        addToHistory(analysis, sampleId);
        showToast('Analyse réussie', 'Le dossier d’appel d’offres a été analysé avec succès.', 'success');
    } catch (err) {
        showProgressStepper(false);
        showToast('Erreur d’analyse', err.message, 'error');
    }
}

async function loadSample(sampleId) {
    showProgressStepper(true);
    simulateStepperProgress();

    try {
        const response = await fetch('/api/load-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sample_id: sampleId,
                gemini_api_key: AppState.geminiApiKey || null
            }),
        });

        if (!response.ok) {
            throw new Error('Impossible de charger le dossier d’exemple.');
        }

        const analysis = await response.json();
        AppState.currentAnalysis = analysis;
        finishProgressStepper();
        renderAnalysisResults(analysis);
        addToHistory(analysis, sampleId);
        showToast('Exemple BTP chargé', `Le marché "${analysis.overview.title}" est prêt à être examiné.`, 'success');
    } catch (err) {
        showProgressStepper(false);
        showToast('Erreur', err.message, 'error');
    }
}

function addToHistory(analysis, sampleId = null) {
    const exists = AppState.history.find(h => h.id === analysis.id);
    if (!exists) {
        AppState.history.unshift({
            id: analysis.id,
            date: analysis.analysis_timestamp,
            title: analysis.overview.title,
            client: analysis.overview.client,
            score: analysis.scoring.overall_score,
            verdict: analysis.scoring.verdict,
            sampleId: sampleId,
            cachedData: analysis
        });
        try {
            localStorage.setItem('btp_analysis_history', JSON.stringify(AppState.history));
        } catch (e) {
            console.warn('Storage limit reached:', e);
        }
        renderHistoryTable();
    }
}

function filterHistory(verdict) {
    AppState.historyFilter = verdict;
    ['all', 'go', 'reserve', 'nogo'].forEach(k => {
        const btn = document.getElementById(`filter-btn-${k}`);
        if (btn) {
            btn.className = 'history-filter-btn px-2.5 py-1 rounded text-[11px] font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200';
        }
    });

    const activeMap = {
        'ALL': 'filter-btn-all',
        'GO': 'filter-btn-go',
        'GO_AVEC_RESERVES': 'filter-btn-reserve',
        'NO_GO': 'filter-btn-nogo'
    };
    const activeBtn = document.getElementById(activeMap[verdict]);
    if (activeBtn) {
        activeBtn.className = 'history-filter-btn px-2.5 py-1 rounded text-[11px] font-bold bg-[#1E3A8A] text-white';
    }

    renderHistoryTable();
}

function renderHistoryTable() {
    const tbody = document.getElementById('history-table-body');
    const badge = document.getElementById('history-badge');
    if (badge) badge.textContent = AppState.history.length;
    if (!tbody) return;

    let items = AppState.history;

    if (AppState.historyFilter && AppState.historyFilter !== 'ALL') {
        items = items.filter(i => i.verdict === AppState.historyFilter);
    }

    if (AppState.historySearch) {
        const q = AppState.historySearch.toLowerCase();
        items = items.filter(i => 
            (i.title && i.title.toLowerCase().includes(q)) || 
            (i.client && i.client.toLowerCase().includes(q)) ||
            (i.id && i.id.toLowerCase().includes(q))
        );
    }

    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-400 text-xs">Aucun dossier correspondant dans votre historique.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(item => {
        const isGo = item.verdict === 'GO';
        const isReserve = item.verdict === 'GO_AVEC_RESERVES';
        const badgeClass = isGo 
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
            : isReserve 
            ? 'bg-amber-50 text-amber-700 border-amber-200' 
            : 'bg-rose-50 text-rose-700 border-rose-200';

        const label = isGo ? 'GO (Favorable)' : isReserve ? 'GO AVEC RÉSERVES' : 'NO-GO (Risqué)';

        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="p-3">
                    <div class="font-mono font-bold text-slate-800 text-xs">${item.id}</div>
                    <div class="text-[10px] text-slate-400 mt-0.5">${item.date}</div>
                </td>
                <td class="p-3 font-semibold text-slate-900 max-w-xs">
                    <div class="truncate text-xs">${item.title}</div>
                </td>
                <td class="p-3 text-slate-600 text-xs">${item.client}</td>
                <td class="p-3 text-center">
                    <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badgeClass}">
                        ${item.score}/100 • ${label}
                    </span>
                </td>
                <td class="p-3 text-right">
                    <div class="inline-flex items-center gap-1.5">
                        <button onclick="loadFromHistory('${item.id}', '${item.sampleId || ''}')" class="px-2.5 py-1 rounded bg-blue-50 hover:bg-blue-100 text-[#1E3A8A] font-bold text-[11px] border border-blue-200 transition-colors" title="Afficher l’analyse complète">
                            Consulter
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide) {
        lucide.createIcons();
    }
}

function loadFromHistory(id, sampleId) {
    if (sampleId && ['1', '2', '3'].includes(sampleId)) {
        switchToDashboardAndLoadSample(sampleId);
        return;
    }

    const item = AppState.history.find(h => h.id === id);
    if (item && item.cachedData) {
        AppState.currentAnalysis = item.cachedData;
        switchToDashboard();
        switchSidebarTab('nouvelle-analyse');
        renderAnalysisResults(item.cachedData);
        showToast('Dossier restauré', `L'analyse "${item.title}" a été chargée.`, 'success');
    } else {
        switchToDashboard();
        switchSidebarTab('nouvelle-analyse');
        showToast('Info', 'Veuillez sélectionner un marché ou déposer un nouveau CCTP.', 'info');
    }
}

function clearHistory() {
    if (confirm('Voulez-vous réinitialiser l’historique des dossiers ?')) {
        AppState.history = [...DEFAULT_HISTORY];
        localStorage.setItem('btp_analysis_history', JSON.stringify(AppState.history));
        renderHistoryTable();
        showToast('Historique réinitialisé', 'La liste de vos analyses a été remise à zéro.', 'info');
    }
}

function showProgressStepper(show) {
    const stepper = document.getElementById('progress-stepper');
    if (stepper) {
        if (show) {
            stepper.classList.remove('hidden');
            resetStepperSteps();
        } else {
            stepper.classList.add('hidden');
        }
    }
}

function resetStepperSteps() {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            el.className = 'p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center gap-2.5 text-xs text-slate-500';
            const icon = el.querySelector('.step-icon');
            if (icon) icon.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block"></span>`;
        }
    }
}

function simulateStepperProgress() {
    const steps = [
        { id: 'step-1', delay: 200 },
        { id: 'step-2', delay: 700 },
        { id: 'step-3', delay: 1300 },
        { id: 'step-4', delay: 1900 },
        { id: 'step-5', delay: 2500 },
    ];

    steps.forEach(({ id, delay }) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                el.className = 'p-3 rounded-lg bg-orange-50 border border-orange-200 flex items-center gap-2.5 text-xs font-bold text-[#EA580C]';
                const icon = el.querySelector('.step-icon');
                if (icon) icon.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-[#EA580C] animate-ping inline-block"></span>`;
            }
        }, delay);
    });
}

function finishProgressStepper() {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            el.className = 'p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center gap-2.5 text-xs font-semibold text-emerald-800';
            const icon = el.querySelector('.step-icon');
            if (icon) icon.innerHTML = `<svg class="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>`;
        }
    }
    setTimeout(() => {
        const stepper = document.getElementById('progress-stepper');
        if (stepper) stepper.classList.add('hidden');
    }, 600);
}

function renderAnalysisResults(analysis) {
    const resultsSec = document.getElementById('results-section');
    if (resultsSec) {
        resultsSec.classList.remove('hidden');
        resultsSec.scrollIntoView({ behavior: 'smooth' });
    }

    renderSyntheseTab(analysis);
    renderNormesTab(analysis);
    renderRisquesTab(analysis);
    renderDpgfTable();
    switchTab('synthese');

    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderSyntheseTab(analysis) {
    const sc = analysis.scoring;
    const ov = analysis.overview;

    // Verdict Hero Badge (Light Mode)
    const verdictEl = document.getElementById('verdict-badge');
    const scoreValEl = document.getElementById('score-value');
    const summaryTextEl = document.getElementById('executive-summary-text');
    const scoreBarEl = document.getElementById('score-progress-bar');

    if (scoreValEl) scoreValEl.textContent = `${sc.overall_score}/100`;
    if (summaryTextEl) summaryTextEl.textContent = sc.executive_summary;
    if (scoreBarEl) scoreBarEl.style.width = `${sc.overall_score}%`;

    if (verdictEl) {
        verdictEl.className = 'px-4 py-2 rounded-lg font-extrabold text-sm uppercase tracking-wider inline-flex items-center gap-2 border';
        if (sc.verdict === 'GO') {
            verdictEl.classList.add('bg-emerald-50', 'text-emerald-800', 'border-emerald-300');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-600"></span> GO FRANCO - MARCHÉ FAVORABLE`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-emerald-600 rounded-full transition-all duration-1000';
        } else if (sc.verdict === 'GO_AVEC_RESERVES') {
            verdictEl.classList.add('bg-amber-50', 'text-amber-800', 'border-amber-300');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> GO AVEC RÉSERVES - VIGILANCE REQUISE`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-[#EA580C] rounded-full transition-all duration-1000';
        } else {
            verdictEl.classList.add('bg-rose-50', 'text-rose-800', 'border-rose-300');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-rose-600"></span> NO-GO - RISQUES ÉLEVÉS DÉCONSEILLÉ`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-rose-600 rounded-full transition-all duration-1000';
        }
    }

    // Dimensions
    setDimensionScore('dim-delay', sc.delay_score);
    setDimensionScore('dim-finance', sc.financial_risk_score);
    setDimensionScore('dim-norms', sc.technical_norm_score);
    setDimensionScore('dim-admin', sc.admin_feasibility_score);

    // Overview fields
    setText('ov-title', ov.title);
    setText('ov-client', ov.client);
    setText('ov-location', ov.location);
    setText('ov-deadline', ov.submission_deadline);
    setText('ov-duration', ov.estimated_duration);
    setText('ov-lots', ov.lots && ov.lots.length > 0 ? ov.lots.join(' • ') : "Tous corps d'état");
    setText('meta-engine', analysis.ai_source);
    setText('meta-id', analysis.id);

    // 3 Columns: Red flags, Warnings, Green lights
    renderInsightList('list-red-flags', sc.red_flags, 'rose');
    renderInsightList('list-warnings', sc.amber_warnings, 'amber');
    renderInsightList('list-green-lights', sc.green_lights, 'emerald');
}

function setDimensionScore(idPrefix, score) {
    const textEl = document.getElementById(`${idPrefix}-val`);
    const barEl = document.getElementById(`${idPrefix}-bar`);
    if (textEl) textEl.textContent = `${score}%`;
    if (barEl) {
        barEl.style.width = `${score}%`;
        if (score >= 75) barEl.className = 'h-1.5 bg-emerald-600 rounded-full';
        else if (score >= 50) barEl.className = 'h-1.5 bg-[#EA580C] rounded-full';
        else barEl.className = 'h-1.5 bg-rose-600 rounded-full';
    }
}

function renderInsightList(containerId, items, color) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = `<li class="text-xs text-slate-400 italic">Aucun élément signalé.</li>`;
        return;
    }
    const colorClasses = {
        rose: 'text-rose-900 bg-rose-50/80 border-rose-200',
        amber: 'text-amber-900 bg-amber-50/80 border-amber-200',
        emerald: 'text-emerald-900 bg-emerald-50/80 border-emerald-200',
    }[color] || 'text-slate-700 bg-slate-50 border-slate-200';

    container.innerHTML = items.map(item => `
        <li class="p-2.5 rounded-lg border text-xs leading-relaxed ${colorClasses}">
            ${item}
        </li>
    `).join('');
}

function renderNormesTab(analysis) {
    const normsTableBody = document.getElementById('norms-table-body');
    const certifsContainer = document.getElementById('certifs-container');

    if (normsTableBody) {
        if (!analysis.technical_norms || analysis.technical_norms.length === 0) {
            normsTableBody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-400 text-xs">Aucune norme spécifique détectée dans ce CCTP.</td></tr>`;
        } else {
            normsTableBody.innerHTML = analysis.technical_norms.map(norm => `
                <tr class="hover:bg-slate-50/80 transition-colors">
                    <td class="p-3 font-mono font-bold text-[#1E3A8A] text-xs whitespace-nowrap">${norm.code}</td>
                    <td class="p-3 text-slate-800 text-xs font-semibold">${norm.title}</td>
                    <td class="p-3 text-slate-600 text-xs">${norm.lot}</td>
                    <td class="p-3 text-xs"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">${norm.requirement_level}</span></td>
                    <td class="p-3 text-slate-600 text-xs max-w-xs">${norm.description}</td>
                </tr>
            `).join('');
        }
    }

    if (certifsContainer) {
        if (!analysis.certifications || analysis.certifications.length === 0) {
            certifsContainer.innerHTML = `<p class="text-xs text-slate-400 italic">Aucune qualification spécifique exigée.</p>`;
        } else {
            certifsContainer.innerHTML = analysis.certifications.map(c => `
                <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50 flex items-start gap-3">
                    <div class="w-8 h-8 rounded bg-orange-100 text-[#EA580C] flex items-center justify-center shrink-0">
                        <i data-lucide="award" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h4 class="text-xs font-bold text-slate-900">${c.name}</h4>
                            <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-semibold">Exigé</span>
                        </div>
                        <p class="text-[11px] text-slate-500 mt-1">${c.penalty_if_missing}</p>
                    </div>
                </div>
            `).join('');
        }
    }
}

function renderRisquesTab(analysis) {
    const container = document.getElementById('financial-risks-container');
    if (!container) return;

    if (!analysis.financial_risks || analysis.financial_risks.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-400 italic">Aucune clause financière atypique détectée.</p>`;
        return;
    }

    container.innerHTML = analysis.financial_risks.map(r => {
        const isHigh = r.severity === 'high';
        const badgeClass = isHigh
            ? 'bg-rose-50 text-rose-800 border-rose-300'
            : r.severity === 'medium'
            ? 'bg-amber-50 text-amber-800 border-amber-300'
            : 'bg-emerald-50 text-emerald-800 border-emerald-300';

        const badgeText = isHigh ? 'CRITIQUE (HAUTE)' : r.severity === 'medium' ? 'VIGILANCE' : 'STANDARD';

        return `
            <div class="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                        <i data-lucide="shield-alert" class="w-4 h-4 text-[#EA580C]"></i>
                        ${r.type}
                    </h4>
                    <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeClass}">
                        ${badgeText}
                    </span>
                </div>
                <div class="mb-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <p class="text-xs text-slate-700 italic">« ${r.clause_text} »</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">Impact Financier :</span>
                        <p class="text-slate-800">${r.impact_estimate}</p>
                    </div>
                    <div class="bg-orange-50/60 p-3 rounded-lg border border-orange-200">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-[#EA580C] block mb-1">Conseil / Parade Artisan :</span>
                        <p class="text-orange-950 font-medium">${r.recommendation}</p>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderDpgfTable() {
    const tbody = document.getElementById('dpgf-table-body');
    const countBadge = document.getElementById('dpgf-item-count');
    if (!tbody) return;

    if (!AppState.currentAnalysis || !AppState.currentAnalysis.dpgf_items || AppState.currentAnalysis.dpgf_items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-400 text-xs">Aucune ligne de bordereau DPGF/BPU chargée pour ce dossier.<br/><span class="text-slate-500">Déposez un fichier Excel (.xlsx) ou CSV pour activer le métré interactif.</span></td></tr>`;
        if (countBadge) countBadge.textContent = '0 poste';
        recalculateMargins();
        return;
    }

    const items = AppState.currentAnalysis.dpgf_items;
    const filter = AppState.dpgfFilter;
    const filtered = filter ? items.filter(it => it.designation.toLowerCase().includes(filter) || it.item_number.toLowerCase().includes(filter)) : items;

    if (countBadge) countBadge.textContent = `${items.length} postes métrés`;

    tbody.innerHTML = filtered.map(item => {
        const realIdx = items.indexOf(item);
        const pu = item.unit_price || 0;
        const total = pu * item.quantity;
        return `
            <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="p-3 font-mono font-bold text-[#1E3A8A] text-xs text-center">${item.item_number}</td>
                <td class="p-3 text-slate-900 text-xs font-semibold">
                    <div>${item.designation}</div>
                    <span class="text-[10px] text-slate-500 font-normal">${item.lot}</span>
                </td>
                <td class="p-3 text-slate-600 text-xs text-center font-mono">${item.unit}</td>
                <td class="p-3 text-slate-800 text-xs text-right font-mono font-bold">${item.quantity.toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</td>
                <td class="p-2 text-right">
                    <input 
                        type="number" 
                        step="0.01" 
                        min="0" 
                        value="${pu > 0 ? pu.toFixed(2) : ''}" 
                        placeholder="0.00" 
                        onchange="updateDpgfPrice(${realIdx}, this.value)"
                        class="w-24 px-2 py-1 text-right bg-white border border-slate-300 rounded text-xs text-slate-900 font-mono focus:border-[#EA580C] focus:outline-none"
                    />
                </td>
                <td class="p-3 text-emerald-700 text-xs text-right font-mono font-bold">
                    ${total > 0 ? total.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' }) : '0,00 €'}
                </td>
            </tr>
        `;
    }).join('');

    recalculateMargins();
}

function updateDpgfPrice(index, value) {
    if (!AppState.currentAnalysis || !AppState.currentAnalysis.dpgf_items[index]) return;
    const num = parseFloat(value) || 0;
    AppState.currentAnalysis.dpgf_items[index].unit_price = num;
    AppState.currentAnalysis.dpgf_items[index].total_price = num * AppState.currentAnalysis.dpgf_items[index].quantity;
    renderDpgfTable();
}

function recalculateMargins() {
    if (!AppState.currentAnalysis || !AppState.currentAnalysis.dpgf_items) {
        updateSimulatorDisplays(0, 0, 0, 0, 0);
        return;
    }

    let totalDebourse = 0;
    AppState.currentAnalysis.dpgf_items.forEach(it => {
        const pu = it.unit_price || 0;
        totalDebourse += pu * it.quantity;
    });

    const fgPct = AppState.marginSettings.fraisGenerauxPct / 100;
    const margePct = AppState.marginSettings.margeNettePct / 100;
    const tvaPct = AppState.marginSettings.tvaPct / 100;

    const totalDeductions = fgPct + margePct;
    let prixVenteHt = totalDebourse;
    if (totalDeductions < 0.95 && totalDebourse > 0) {
        prixVenteHt = totalDebourse / (1 - totalDeductions);
    } else if (totalDebourse > 0) {
        prixVenteHt = totalDebourse * (1 + totalDeductions);
    }

    const margeMontant = prixVenteHt * margePct;
    const montantTva = prixVenteHt * tvaPct;
    const totalTtc = prixVenteHt + montantTva;

    updateSimulatorDisplays(totalDebourse, prixVenteHt, margeMontant, montantTva, totalTtc);
}

function updateSimulatorDisplays(debourse, venteHt, marge, tva, ttc) {
    setText('sim-debourse', formatCurrency(debourse));
    setText('sim-vente-ht', formatCurrency(venteHt));
    setText('sim-marge-montant', formatCurrency(marge));
    setText('sim-tva', formatCurrency(tva));
    setText('sim-total-ttc', formatCurrency(ttc));

    // Mirror displays in subview-simulateur
    setText('sim-debourse-mirror', formatCurrency(debourse));
    setText('sim-vente-ht-mirror', formatCurrency(venteHt));
    setText('sim-marge-montant-mirror', formatCurrency(marge));
    setText('sim-tva-mirror', formatCurrency(tva));
    setText('sim-total-ttc-mirror', formatCurrency(ttc));
}

function renderChecklist() {
    // 1. Render in Results section tab (if active)
    const container = document.getElementById('checklist-items');
    if (container) {
        container.innerHTML = AppState.checklist.map((item, idx) => `
            <label class="flex items-center gap-3 p-3.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer transition-colors shadow-sm">
                <input 
                    type="checkbox" 
                    ${item.checked ? 'checked' : ''} 
                    onchange="toggleChecklistItem(${idx})"
                    class="w-4 h-4 rounded border-slate-300 text-[#EA580C] focus:ring-[#EA580C]"
                />
                <span class="text-xs text-slate-800 font-medium select-none flex-1">${item.label}</span>
                ${item.required ? '<span class="text-[10px] px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-semibold border border-rose-200">Indispensable</span>' : ''}
            </label>
        `).join('');
    }

    // 2. Render in dedicated Subview Checklist
    const subContainer = document.getElementById('subview-checklist-items');
    if (subContainer) {
        let items = AppState.checklist;
        if (AppState.checklistFilter && AppState.checklistFilter !== 'all') {
            items = items.filter(i => i.category === AppState.checklistFilter);
        }

        subContainer.innerHTML = items.map((item) => {
            const realIdx = AppState.checklist.indexOf(item);
            const catBadge = item.category === 'candidature' 
                ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">Candidature</span>'
                : item.category === 'offre'
                ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">Offre</span>'
                : '<span class="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-semibold">Habilitation</span>';

            return `
                <div class="flex items-start gap-3 p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 shadow-sm transition-all ${item.checked ? 'bg-slate-50/60' : ''}">
                    <input 
                        type="checkbox" 
                        ${item.checked ? 'checked' : ''} 
                        onchange="toggleChecklistItem(${realIdx})"
                        class="w-4 h-4 rounded border-slate-300 text-[#EA580C] focus:ring-[#EA580C] mt-0.5 cursor-pointer"
                    />
                    <div class="grow select-none cursor-pointer" onclick="toggleChecklistItem(${realIdx})">
                        <div class="flex items-center gap-2 mb-1">
                            ${catBadge}
                            ${item.required ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 font-semibold border border-rose-200">Obligatoire</span>' : '<span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-medium">Recommandé</span>'}
                        </div>
                        <p class="text-xs font-semibold ${item.checked ? 'line-through text-slate-400' : 'text-slate-800'} leading-relaxed">${item.label}</p>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateChecklistProgress();
    if (window.lucide) lucide.createIcons();
}

function filterChecklist(cat) {
    AppState.checklistFilter = cat;
    ['all', 'candidature', 'offre', 'specifique'].forEach(k => {
        const btn = document.getElementById(`chk-tab-${k}`);
        if (btn) {
            btn.className = 'chk-filter-btn px-3 py-1 rounded text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200';
        }
    });

    const activeBtn = document.getElementById(`chk-tab-${cat}`);
    if (activeBtn) {
        activeBtn.className = 'chk-filter-btn px-3 py-1 rounded text-xs font-bold bg-[#1E3A8A] text-white';
    }

    renderChecklist();
}

function addCustomChecklistItem() {
    const input = document.getElementById('new-checklist-input');
    if (!input) return;
    const val = input.value.trim();
    if (!val) {
        showToast('Champ requis', 'Veuillez saisir le nom de la pièce à ajouter.', 'warning');
        return;
    }

    AppState.checklist.push({
        id: 'custom-' + Date.now(),
        label: val,
        category: AppState.checklistFilter !== 'all' ? AppState.checklistFilter : 'candidature',
        required: false,
        checked: false
    });

    try {
        localStorage.setItem('btp_submission_checklist', JSON.stringify(AppState.checklist));
    } catch {}

    input.value = '';
    renderChecklist();
    showToast('Pièce ajoutée', `"${val}" a été ajoutée à votre checklist.`, 'success');
}

function toggleChecklistItem(index) {
    if (AppState.checklist[index]) {
        AppState.checklist[index].checked = !AppState.checklist[index].checked;
        try {
            localStorage.setItem('btp_submission_checklist', JSON.stringify(AppState.checklist));
        } catch {}
        renderChecklist();
    }
}

function updateChecklistProgress() {
    const checked = AppState.checklist.filter(i => i.checked).length;
    const total = AppState.checklist.length;
    const pct = total > 0 ? Math.round((checked / total) * 100) : 0;

    setText('checklist-count', `${checked}/${total} pièces prêtes`);
    setText('subview-checklist-count', `${checked}/${total} pièces prêtes (${pct}%)`);

    const bar = document.getElementById('checklist-bar');
    if (bar) bar.style.width = `${pct}%`;

    const subBar = document.getElementById('subview-checklist-bar');
    if (subBar) subBar.style.width = `${pct}%`;
}

// Standalone & Active Simulator Logic
function renderSimulatorSubView() {
    const banner = document.getElementById('sim-no-analysis-banner');
    const activeCont = document.getElementById('sim-active-container');

    if (AppState.currentAnalysis && AppState.currentAnalysis.dpgf_items && AppState.currentAnalysis.dpgf_items.length > 0) {
        if (banner) banner.classList.add('hidden');
        if (activeCont) {
            activeCont.classList.remove('hidden');
            activeCont.innerHTML = `
                <div class="saas-card p-6 bg-white space-y-4 border-2 border-slate-200">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                        <div class="flex items-center gap-2">
                            <i data-lucide="calculator" class="w-5 h-5 text-[#EA580C]"></i>
                            <div>
                                <h3 class="text-sm font-bold text-slate-900">${AppState.currentAnalysis.overview.title}</h3>
                                <p class="text-xs text-slate-500">${AppState.currentAnalysis.overview.client} • Réf: ${AppState.currentAnalysis.id}</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <button onclick="exportPdf()" class="px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-rose-700 border border-red-200 text-xs font-bold flex items-center gap-1.5 transition-colors">
                                <i data-lucide="file-down" class="w-3.5 h-3.5"></i>
                                <span>PDF</span>
                            </button>
                            <button onclick="exportExcel()" class="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold flex items-center gap-1.5 transition-colors">
                                <i data-lucide="sheet" class="w-3.5 h-3.5"></i>
                                <span>Excel</span>
                            </button>
                        </div>
                    </div>

                    <!-- Simulator Controls -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                            <label class="block text-xs font-bold text-slate-700 mb-1">Frais Généraux (%) :</label>
                            <input type="number" value="${AppState.marginSettings.fraisGenerauxPct}" step="0.5" min="0" max="40" oninput="AppState.marginSettings.fraisGenerauxPct = parseFloat(this.value)||0; recalculateMargins();" class="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-mono focus:border-[#EA580C] focus:outline-none">
                            <span class="text-[10px] text-slate-500 mt-1 block">Charges de structure, amortissements</span>
                        </div>
                        <div class="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                            <label class="block text-xs font-bold text-slate-700 mb-1">Marge Nette Ciblée (%) :</label>
                            <input type="number" value="${AppState.marginSettings.margeNettePct}" step="0.5" min="0" max="50" oninput="AppState.marginSettings.margeNettePct = parseFloat(this.value)||0; recalculateMargins();" class="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-mono focus:border-[#EA580C] focus:outline-none">
                            <span class="text-[10px] text-slate-500 mt-1 block">Bénéfice net artisan après impôts</span>
                        </div>
                        <div class="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                            <label class="block text-xs font-bold text-slate-700 mb-1">Taux de TVA :</label>
                            <select onchange="AppState.marginSettings.tvaPct = parseFloat(this.value)||20; recalculateMargins();" class="w-full bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-900 font-mono focus:border-[#EA580C] focus:outline-none">
                                <option value="20" ${AppState.marginSettings.tvaPct === 20 ? 'selected' : ''}>20.0% (Standard / Neuf)</option>
                                <option value="10" ${AppState.marginSettings.tvaPct === 10 ? 'selected' : ''}>10.0% (Rénovation > 2 ans)</option>
                                <option value="5.5" ${AppState.marginSettings.tvaPct === 5.5 ? 'selected' : ''}>5.5% (Énergétique RGE)</option>
                            </select>
                            <span class="text-[10px] text-slate-500 mt-1 block">TVA applicable aux travaux</span>
                        </div>
                    </div>

                    <!-- Simulator Result KPI Badges -->
                    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 pt-2">
                        <div class="p-3 rounded-lg bg-slate-50 border border-slate-200">
                            <span class="text-[10px] font-bold text-slate-500 uppercase block">1. Déboursé Sec</span>
                            <div id="sim-debourse-mirror" class="text-sm font-bold font-mono text-slate-900 mt-1">0,00 €</div>
                            <span class="text-[9px] text-slate-500">Fournitures + MO</span>
                        </div>
                        <div class="p-3 rounded-lg bg-orange-50 border border-orange-200">
                            <span class="text-[10px] font-bold text-[#EA580C] uppercase block">2. Marge Nette (€)</span>
                            <div id="sim-marge-montant-mirror" class="text-sm font-bold font-mono text-[#EA580C] mt-1">0,00 €</div>
                            <span class="text-[9px] text-orange-700">Bénéfice estimé</span>
                        </div>
                        <div class="p-3 rounded-lg bg-blue-50 border border-blue-200">
                            <span class="text-[10px] font-bold text-[#1E3A8A] uppercase block">3. Prix Vente HT</span>
                            <div id="sim-vente-ht-mirror" class="text-sm font-bold font-mono text-[#1E3A8A] mt-1">0,00 €</div>
                            <span class="text-[9px] text-blue-700">Soumission HT</span>
                        </div>
                        <div class="p-3 rounded-lg bg-slate-50 border border-slate-200">
                            <span class="text-[10px] font-bold text-slate-500 uppercase block">4. Montant TVA</span>
                            <div id="sim-tva-mirror" class="text-sm font-bold font-mono text-slate-700 mt-1">0,00 €</div>
                            <span class="text-[9px] text-slate-500">TVA collectée</span>
                        </div>
                        <div class="p-3 rounded-lg bg-emerald-50 border border-emerald-300">
                            <span class="text-[10px] font-bold text-emerald-800 uppercase block">5. TOTAL TTC</span>
                            <div id="sim-total-ttc-mirror" class="text-sm font-black font-mono text-emerald-800 mt-1">0,00 €</div>
                            <span class="text-[9px] text-emerald-700">Prix client final</span>
                        </div>
                    </div>
                </div>

                <!-- Table Preview -->
                <div class="saas-card p-6 bg-white space-y-4">
                    <div class="flex items-center justify-between">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-700">Postes DPGF du Marché (${AppState.currentAnalysis.dpgf_items.length} postes)</h4>
                        <button onclick="promptAddDpgfLine()" class="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs font-bold flex items-center gap-1">
                            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                            <span>Ajouter un poste</span>
                        </button>
                    </div>
                    <div class="overflow-x-auto rounded-lg border border-slate-200 max-h-[400px] overflow-y-auto">
                        <table class="w-full text-left text-xs">
                            <thead class="bg-slate-50 text-slate-700 font-bold uppercase text-[10px] tracking-wider border-b border-slate-200 sticky top-0 z-10">
                                <tr>
                                    <th class="p-3 text-center w-14">N°</th>
                                    <th class="p-3">Désignation</th>
                                    <th class="p-3 text-center w-16">Unité</th>
                                    <th class="p-3 text-right w-24">Quantité</th>
                                    <th class="p-3 text-right w-32">P.U. H.T. (€)</th>
                                    <th class="p-3 text-right w-36">Total H.T. (€)</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 bg-white">
                                ${AppState.currentAnalysis.dpgf_items.map((item, idx) => `
                                    <tr class="hover:bg-slate-50 transition-colors">
                                        <td class="p-2.5 text-center font-mono font-bold text-blue-900">${item.item_number}</td>
                                        <td class="p-2.5 font-semibold text-slate-900">${item.designation}</td>
                                        <td class="p-2.5 text-center text-slate-500 font-mono">${item.unit}</td>
                                        <td class="p-2.5 text-right font-mono font-bold text-slate-700">${item.quantity}</td>
                                        <td class="p-2 text-right">
                                            <input type="number" step="0.01" value="${item.unit_price || ''}" onchange="updateDpgfPrice(${idx}, this.value)" class="w-24 px-2 py-1 text-right bg-white border border-slate-300 rounded text-xs text-slate-900 font-mono focus:border-[#EA580C] focus:outline-none">
                                        </td>
                                        <td class="p-2.5 text-right font-mono font-bold text-emerald-700">${formatCurrency((item.unit_price || 0) * item.quantity)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            recalculateMargins();
            if (window.lucide) lucide.createIcons();
        }
    } else {
        if (banner) banner.classList.remove('hidden');
        if (activeCont) activeCont.classList.add('hidden');
        calculateQuickMargin();
    }
}

// Rapid Standalone Margin Calculator
function calculateQuickMargin() {
    const mat = parseFloat(document.getElementById('quick-mat')?.value) || 0;
    const heures = parseFloat(document.getElementById('quick-heures')?.value) || 0;
    const tauxMo = parseFloat(document.getElementById('quick-taux-mo')?.value) || 0;
    const sub = parseFloat(document.getElementById('quick-sub')?.value) || 0;

    const fgPct = parseFloat(document.getElementById('quick-fg-slider')?.value) || 12;
    const margePct = parseFloat(document.getElementById('quick-marge-slider')?.value) || 15;
    const tvaPct = parseFloat(document.getElementById('quick-tva-select')?.value) || 20;

    setText('quick-fg-val', `${fgPct} %`);
    setText('quick-marge-val', `${margePct} %`);

    const totalMo = heures * tauxMo;
    setText('quick-total-mo', formatCurrency(totalMo));

    const debourseSec = mat + totalMo + sub;
    const totalDeduction = (fgPct + margePct) / 100;
    
    let prixVenteHt = debourseSec;
    if (totalDeduction < 0.95 && debourseSec > 0) {
        prixVenteHt = debourseSec / (1 - totalDeduction);
    } else if (debourseSec > 0) {
        prixVenteHt = debourseSec * (1 + totalDeduction);
    }

    const montantFg = prixVenteHt * (fgPct / 100);
    const montantMarge = prixVenteHt * (margePct / 100);
    const montantTva = prixVenteHt * (tvaPct / 100);
    const prixVenteTtc = prixVenteHt + montantTva;
    const coeffK = debourseSec > 0 ? (prixVenteHt / debourseSec).toFixed(2) : '1.00';

    setText('quick-res-ds', formatCurrency(debourseSec));
    setText('quick-res-fg', formatCurrency(montantFg));
    setText('quick-res-marge', formatCurrency(montantMarge));
    setText('quick-res-pvht', formatCurrency(prixVenteHt));
    setText('quick-res-pvttc', formatCurrency(prixVenteTtc));
    setText('quick-coeff-k', `Coeff de vente K : ${coeffK}`);

    // Update Segmented Bar
    if (prixVenteHt > 0) {
        const matPct = Math.round((mat / prixVenteHt) * 100);
        const moPct = Math.round((totalMo / prixVenteHt) * 100);
        const barMat = document.getElementById('bar-segment-mat');
        const barMo = document.getElementById('bar-segment-mo');
        const barFg = document.getElementById('bar-segment-fg');
        const barMarge = document.getElementById('bar-segment-marge');

        if (barMat) barMat.style.width = `${matPct}%`;
        if (barMo) barMo.style.width = `${moPct}%`;
        if (barFg) barFg.style.width = `${fgPct}%`;
        if (barMarge) barMarge.style.width = `${margePct}%`;
    }
}

// Landing Page Interactive ROI Calculator
function calculateRoi() {
    const sliderAo = document.getElementById('roi-slider-ao');
    const sliderHours = document.getElementById('roi-slider-hours');
    const sliderRate = document.getElementById('roi-slider-rate');

    if (!sliderAo || !sliderHours || !sliderRate) return;

    const aoMonth = parseInt(sliderAo.value) || 4;
    const hoursPerCctp = parseFloat(sliderHours.value) || 3;
    const hourlyRate = parseInt(sliderRate.value) || 65;

    setText('roi-ao-display', `${aoMonth} dossier${aoMonth > 1 ? 's' : ''}`);
    setText('roi-hours-display', `${hoursPerCctp} heure${hoursPerCctp > 1 ? 's' : ''}`);
    setText('roi-rate-display', `${hourlyRate} € / h`);

    const dossiersYear = aoMonth * 12;
    const hoursSavedPerDossier = Math.max(0.5, hoursPerCctp - 0.25);
    const totalHoursSavedYear = Math.round(dossiersYear * hoursSavedPerDossier);
    const financialSavingsYear = Math.round(totalHoursSavedYear * hourlyRate);
    const subscriptionCost = 300;
    const roiPercentage = Math.round(((financialSavingsYear - subscriptionCost) / subscriptionCost) * 100);

    setText('roi-result-hours', `${totalHoursSavedYear} h / an`);
    setText('roi-result-money', `${financialSavingsYear.toLocaleString('fr-FR')} € / an`);
    setText('roi-result-percent', `+${roiPercentage.toLocaleString('fr-FR')} %`);
}

// Landing Page FAQ Accordion
function toggleFaq(item) {
    if (!item) return;
    const isActive = item.classList.contains('active');
    document.querySelectorAll('.faq-item').forEach(el => {
        el.classList.remove('active', 'border-slate-300', 'shadow-sm');
    });

    if (!isActive) {
        item.classList.add('active', 'border-slate-300', 'shadow-sm');
    }
}

// Company Profile Management
function saveCompanyProfile(e) {
    if (e) e.preventDefault();
    const prof = {
        company: document.getElementById('prof-company')?.value.trim() || 'SAS Artisan BTP Travaux',
        siret: document.getElementById('prof-siret')?.value.trim() || '',
        trade: document.getElementById('prof-trade')?.value || 'Électricité générale & CFO/CFA',
        contact: document.getElementById('prof-contact')?.value.trim() || '',
        insurance: document.getElementById('prof-insurance')?.value.trim() || '',
        qualifs: document.getElementById('prof-qualifs')?.value.trim() || ''
    };

    AppState.companyProfile = prof;
    try {
        localStorage.setItem('btp_company_profile', JSON.stringify(prof));
    } catch {}

    const sidebarComp = document.querySelector('#sidebar-container .text-slate-900');
    if (sidebarComp) sidebarComp.textContent = prof.company;

    showToast('Profil enregistré', 'Les coordonnées de votre entreprise ont été mises à jour.', 'success');
}

function loadSavedCompanyProfile() {
    const prof = AppState.companyProfile;
    if (!prof) return;

    if (document.getElementById('prof-company')) document.getElementById('prof-company').value = prof.company || '';
    if (document.getElementById('prof-siret')) document.getElementById('prof-siret').value = prof.siret || '';
    if (document.getElementById('prof-trade')) document.getElementById('prof-trade').value = prof.trade || '';
    if (document.getElementById('prof-contact')) document.getElementById('prof-contact').value = prof.contact || '';
    if (document.getElementById('prof-insurance')) document.getElementById('prof-insurance').value = prof.insurance || '';
    if (document.getElementById('prof-qualifs')) document.getElementById('prof-qualifs').value = prof.qualifs || '';

    const sidebarComp = document.querySelector('#sidebar-container .text-slate-900');
    if (sidebarComp && prof.company) sidebarComp.textContent = prof.company;
}

function downloadSampleInvoice() {
    const prof = AppState.companyProfile || {};
    const invoiceContent = `===============================================================
FACTURE D'ABONNEMENT SAAS BTP - REÇU DE PAIEMENT
===============================================================
ÉMETTEUR :
BTP Public Tender Analyzer SAS
12, Rue de la Commande Publique - 75008 Paris
SIRET : 912 345 678 00019 • TVA : FR88912345678

CLIENT :
${prof.company || 'SAS Artisan BTP Travaux'}
SIRET : ${prof.siret || '849 123 456 00012'}
Activité : ${prof.trade || 'BTP Second Œuvre'}

RÉFÉRENCE FACTURE : FAC-2026-1028
DATE D'ÉMISSION   : 28/10/2026
DATE DE RÈGLEMENT : 28/10/2026 (Carte Bancaire Stripe - Réf: ch_982xAbc)
STATUT            : ACQUITTÉE / PAYÉE

---------------------------------------------------------------
DÉSIGNATION DES PRESTATIONS                     MONTANT HT
---------------------------------------------------------------
Abonnement Annuel Pro Artisans & PME BTP         300,00 €
- Accès illimité à l'analyse CCTP / CCAP (PDF)
- Parsing automatique des grilles DPGF / BPU
- Simulateur de marges et déboursé sec
- Exports PDF, Excel et CSV sans quota
- Support prioritaire 24/7 & Mises à jour CSTB
---------------------------------------------------------------
TOTAL H.T.                                      300,00 €
TVA (20.0%)                                      60,00 €
---------------------------------------------------------------
TOTAL T.T.C. RÉGLÉ                              360,00 €
===============================================================
Facture acquittée le 28/10/2026. Merci pour votre confiance !
`;

    const blob = new Blob([invoiceContent], { type: 'text/plain;charset=utf-8' });
    downloadBlob(blob, `Facture_FAC-2026-1028_BTP_Analyzer.txt`);
    showToast('Reçu téléchargé', 'Votre reçu officiel de facturation a été téléchargé.', 'success');
}

function promptAddDpgfLine() {
    if (!AppState.currentAnalysis || !AppState.currentAnalysis.dpgf_items) {
        showToast('Aucun dossier actif', 'Veuillez d’abord charger un marché.', 'warning');
        return;
    }

    const desig = prompt('Désignation du nouveau poste :', 'Fourniture et pose complémentaire...');
    if (!desig) return;

    const qte = parseFloat(prompt('Quantité métrée :', '1')) || 1;
    const pu = parseFloat(prompt('Prix Unitaire HT (€) :', '150')) || 0;
    const nextNum = (AppState.currentAnalysis.dpgf_items.length + 1) + '.01';

    AppState.currentAnalysis.dpgf_items.push({
        item_number: nextNum,
        designation: desig,
        unit: 'u',
        quantity: qte,
        unit_price: pu,
        total_price: pu * qte,
        lot: 'Poste Complémentaire'
    });

    renderDpgfTable();
    if (AppState.currentSidebarTab === 'simulateur') {
        renderSimulatorSubView();
    }
    showToast('Poste ajouté', `Le poste ${nextNum} a été ajouté au métré.`, 'success');
}

function switchTab(tabId) {
    AppState.activeTab = tabId;
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
    const targetPane = document.getElementById(`tab-content-${tabId}`);
    if (targetPane) targetPane.classList.remove('hidden');

    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        if (btn.dataset.tab === tabId) {
            btn.className = 'nav-tab-btn px-3.5 py-2 rounded-lg text-xs font-bold bg-blue-50 text-[#1E3A8A] border border-blue-200 flex items-center gap-2 transition-all';
        } else {
            btn.className = 'nav-tab-btn px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center gap-2 transition-all';
        }
    });

    if (window.lucide) {
        lucide.createIcons();
    }
}

async function exportPdf() {
    if (!AppState.currentAnalysis) {
        showToast('Aucun dossier actif', 'Veuillez lancer une analyse avant d’exporter.', 'warning');
        return;
    }
    showToast('Génération PDF...', 'Création de la fiche de synthèse décisionnelle en cours.', 'info');

    try {
        const response = await fetch('/api/export/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis: AppState.currentAnalysis }),
        });

        if (!response.ok) throw new Error('Échec de la génération du PDF.');

        const blob = await response.blob();
        downloadBlob(blob, `Synthese_AO_${AppState.currentAnalysis.id}.pdf`);
        showToast('Téléchargement terminé', 'La fiche de décision PDF a été téléchargée.', 'success');
    } catch (err) {
        showToast('Erreur export PDF', err.message, 'error');
    }
}

async function exportExcel() {
    if (!AppState.currentAnalysis) {
        showToast('Aucun dossier actif', 'Veuillez lancer une analyse avant d’exporter.', 'warning');
        return;
    }
    showToast('Génération Excel...', 'Génération du classeur DPGF chiffré en cours.', 'info');

    try {
        const response = await fetch('/api/export/excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis: AppState.currentAnalysis }),
        });

        if (!response.ok) throw new Error('Échec de la génération du fichier Excel.');

        const blob = await response.blob();
        downloadBlob(blob, `Chiffrage_DPGF_${AppState.currentAnalysis.id}.xlsx`);
        showToast('Téléchargement terminé', 'Le classeur Excel DPGF a été téléchargé.', 'success');
    } catch (err) {
        showToast('Erreur export Excel', err.message, 'error');
    }
}

async function exportCsv() {
    if (!AppState.currentAnalysis) {
        showToast('Aucun dossier actif', 'Veuillez d’abord lancer une analyse.', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis: AppState.currentAnalysis }),
        });

        if (!response.ok) throw new Error('Échec de la génération du CSV.');

        const blob = await response.blob();
        downloadBlob(blob, `DPGF_${AppState.currentAnalysis.id}.csv`);
        showToast('Téléchargement terminé', 'Le fichier CSV a été téléchargé.', 'success');
    } catch (err) {
        showToast('Erreur CSV', err.message, 'error');
    }
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}

async function checkEngineStatus() {
    try {
        const res = await fetch('/api/status');
        if (res.ok) {
            const data = await res.json();
            const isGemini = data.gemini_api_configured || !!AppState.geminiApiKey;
            updateEngineStatusBadge(isGemini ? 'Gemini AI Connecté' : 'Moteur Expert BTP Actif', isGemini);
        }
    } catch {
        updateEngineStatusBadge('Moteur Expert BTP Actif', false);
    }
}

function updateEngineStatusBadge(text, isGemini) {
    const badge = document.getElementById('engine-status-badge');
    if (!badge) return;
    badge.textContent = text;
    if (isGemini) {
        badge.className = 'px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-50 text-[#1E3A8A] border border-blue-200 inline-flex items-center gap-1.5';
    } else {
        badge.className = 'px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1.5';
    }
}

function loadSavedApiKey() {
    const key = localStorage.getItem('btp_gemini_api_key');
    if (key) {
        AppState.geminiApiKey = key;
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function formatCurrency(val) {
    return (val || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'Ko', 'Mo', 'Go'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    const colorClasses = {
        success: 'border-emerald-200 bg-white text-emerald-800 shadow-sm',
        warning: 'border-amber-200 bg-white text-amber-800 shadow-sm',
        error: 'border-rose-200 bg-white text-rose-800 shadow-sm',
        info: 'border-blue-200 bg-white text-[#1E3A8A] shadow-sm',
    }[type] || 'border-slate-200 bg-white text-slate-800 shadow-sm';

    toast.className = `p-3.5 rounded-xl border flex items-start gap-3 transform transition-all duration-300 ease-out translate-y-2 opacity-0 text-xs ${colorClasses}`;
    toast.innerHTML = `
        <div class="grow">
            <h5 class="font-bold text-slate-900 text-xs mb-0.5">${title}</h5>
            <p class="text-slate-600">${message}</p>
        </div>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}
