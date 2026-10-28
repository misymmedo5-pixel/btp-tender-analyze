/**
 * BTP Public Tender Analyzer - Client Application Logic
 */

// Application State
const AppState = {
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
    checklist: [
        { id: 'dc1', label: 'Lettre de candidature DC1 (ou DUME)', required: true, checked: false },
        { id: 'dc2', label: 'Déclaration du candidat DC2 (chiffre d’affaires 3 ans)', required: true, checked: false },
        { id: 'attri1', label: 'Acte d’engagement ATTRI1 signé', required: true, checked: false },
        { id: 'decennale', label: 'Attestation d’Assurance Décennale & RC Pro valide', required: true, checked: false },
        { id: 'memoire', label: 'Mémoire Technique BTP personnalisé (sécurité, planning, moyens)', required: true, checked: false },
        { id: 'dpgf', label: 'Bordereau DPGF / BPU complété et vérifié', required: true, checked: false },
        { id: 'rib', label: 'Relevé d’Identité Bancaire (RIB) de l’entreprise', required: true, checked: false },
        { id: 'kbis', label: 'Extrait Kbis de moins de 3 mois & régularité fiscale/sociale', required: true, checked: false },
    ]
};

// DOM Initializer
document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initEventListeners();
    checkEngineStatus();
    loadSavedApiKey();
    renderChecklist();
    if (window.lucide) {
        lucide.createIcons();
    }
});

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
    if (btnSample1) btnSample1.addEventListener('click', () => loadSample('1'));
    if (btnSample2) btnSample2.addEventListener('click', () => loadSample('2'));

    // Export Buttons
    const btnExportPdf = document.getElementById('btn-export-pdf');
    const btnExportExcel = document.getElementById('btn-export-excel');
    const btnExportCsv = document.getElementById('btn-export-csv');
    const btnPrint = document.getElementById('btn-print-summary');

    if (btnExportPdf) btnExportPdf.addEventListener('click', exportPdf);
    if (btnExportExcel) btnExportExcel.addEventListener('click', exportExcel);
    if (btnExportCsv) btnExportCsv.addEventListener('click', exportCsv);
    if (btnPrint) btnPrint.addEventListener('click', () => window.print());

    // Navigation Tabs
    const tabButtons = document.querySelectorAll('.nav-tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
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
            updateEngineStatusBadge(val ? 'Gemini AI Connecté' : 'Moteur Expert Local', !!val);
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
        showToast('Exemple BTP chargé', `Le marché "${analysis.overview.title}" est prêt à être examiné.`, 'success');
    } catch (err) {
        showProgressStepper(false);
        showToast('Erreur', err.message, 'error');
    }
}

function showProgressStepper(show) {
    const stepper = document.getElementById('progress-stepper');
    const uploadSec = document.getElementById('upload-section');
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
            el.classList.remove('text-amber-400', 'text-emerald-400', 'font-bold');
            el.classList.add('text-slate-400');
            const icon = el.querySelector('.step-icon');
            if (icon) icon.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-slate-600 inline-block"></span>`;
        }
    }
}

function simulateStepperProgress() {
    const steps = [
        { id: 'step-1', delay: 200, label: 'Extraction textuelle du CCTP & CCAP...' },
        { id: 'step-2', delay: 800, label: 'Détection des DTU & Normes CSTB/AFNOR...' },
        { id: 'step-3', delay: 1400, label: 'Analyse des pénalités & pièges contractuels...' },
        { id: 'step-4', delay: 2000, label: 'Métré et extraction du bordereau DPGF...' },
        { id: 'step-5', delay: 2600, label: 'Calcul du score Go / No-Go 60s...' },
    ];

    steps.forEach(({ id, delay }) => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.remove('text-slate-400');
                el.classList.add('text-amber-400', 'font-bold');
                const icon = el.querySelector('.step-icon');
                if (icon) icon.innerHTML = `<span class="w-3 h-3 rounded-full bg-amber-400 animate-ping inline-block"></span>`;
            }
        }, delay);
    });
}

function finishProgressStepper() {
    for (let i = 1; i <= 5; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            el.classList.remove('text-slate-400', 'text-amber-400');
            el.classList.add('text-emerald-400', 'font-semibold');
            const icon = el.querySelector('.step-icon');
            if (icon) icon.innerHTML = `<svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>`;
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

    // Verdict Hero Card
    const verdictEl = document.getElementById('verdict-badge');
    const scoreValEl = document.getElementById('score-value');
    const summaryTextEl = document.getElementById('executive-summary-text');
    const scoreBarEl = document.getElementById('score-progress-bar');

    if (scoreValEl) scoreValEl.textContent = `${sc.overall_score}/100`;
    if (summaryTextEl) summaryTextEl.textContent = sc.executive_summary;
    if (scoreBarEl) scoreBarEl.style.width = `${sc.overall_score}%`;

    if (verdictEl) {
        verdictEl.className = 'px-4 py-2 rounded-xl font-extrabold text-sm uppercase tracking-wider inline-flex items-center gap-2 shadow-sm';
        if (sc.verdict === 'GO') {
            verdictEl.classList.add('bg-emerald-500/20', 'text-emerald-300', 'border', 'border-emerald-500/40');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span> GO FRANCO - MARCHÉ FAVORABLE`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-1000';
        } else if (sc.verdict === 'GO_AVEC_RESERVES') {
            verdictEl.classList.add('bg-amber-500/20', 'text-amber-300', 'border', 'border-amber-500/40');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span> GO AVEC RÉSERVES - VIGILANCE CONTRACTUELLE`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-gradient-to-r from-amber-500 to-yellow-400 rounded-full transition-all duration-1000';
        } else {
            verdictEl.classList.add('bg-rose-500/20', 'text-rose-300', 'border', 'border-rose-500/40');
            verdictEl.innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-rose-400"></span> NO-GO - RISQUES ÉLEVÉS DÉCONSEILLÉ`;
            if (scoreBarEl) scoreBarEl.className = 'h-full bg-gradient-to-r from-rose-600 to-rose-400 rounded-full transition-all duration-1000';
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
        if (score >= 75) barEl.className = 'h-1.5 bg-emerald-400 rounded-full';
        else if (score >= 50) barEl.className = 'h-1.5 bg-amber-400 rounded-full';
        else barEl.className = 'h-1.5 bg-rose-500 rounded-full';
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
        rose: 'text-rose-200 bg-rose-950/40 border-rose-800/50',
        amber: 'text-amber-200 bg-amber-950/40 border-amber-800/50',
        emerald: 'text-emerald-200 bg-emerald-950/40 border-emerald-800/50',
    }[color] || 'text-slate-300 bg-slate-800/40 border-slate-700';

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
            normsTableBody.innerHTML = analysis.technical_norms.map((norm, idx) => `
                <tr class="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                    <td class="p-3 font-mono font-bold text-amber-400 text-xs whitespace-nowrap">${norm.code}</td>
                    <td class="p-3 text-slate-200 text-xs font-medium">${norm.title}</td>
                    <td class="p-3 text-slate-400 text-xs">${norm.lot}</td>
                    <td class="p-3 text-xs"><span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">${norm.requirement_level}</span></td>
                    <td class="p-3 text-slate-300 text-xs max-w-xs">${norm.description}</td>
                </tr>
            `).join('');
        }
    }

    if (certifsContainer) {
        if (!analysis.certifications || analysis.certifications.length === 0) {
            certifsContainer.innerHTML = `<p class="text-xs text-slate-400 italic">Aucune qualification spécifique exigée.</p>`;
        } else {
            certifsContainer.innerHTML = analysis.certifications.map(c => `
                <div class="p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 flex items-start gap-3">
                    <div class="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                        <i data-lucide="award" class="w-4 h-4"></i>
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <h4 class="text-xs font-bold text-white">${c.name}</h4>
                            <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-semibold">Exigé</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-1">${c.penalty_if_missing}</p>
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
            ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
            : r.severity === 'medium'
            ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';

        const badgeText = isHigh ? 'CRITIQUE (HAUT)' : r.severity === 'medium' ? 'MOYEN' : 'STANDARD';

        return `
            <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-sm font-bold text-white flex items-center gap-2">
                        <i data-lucide="shield-alert" class="w-4 h-4 text-amber-400"></i>
                        ${r.type}
                    </h4>
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeClass}">
                        ${badgeText}
                    </span>
                </div>
                <div class="mb-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    <p class="text-xs text-slate-300 italic">« ${r.clause_text} »</p>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div class="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">Impact Financier :</span>
                        <p class="text-slate-200">${r.impact_estimate}</p>
                    </div>
                    <div class="bg-amber-950/20 p-2.5 rounded-lg border border-amber-800/30">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-amber-400 block mb-1">Conseil / Parade Artisan :</span>
                        <p class="text-amber-200">${r.recommendation}</p>
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

    tbody.innerHTML = filtered.map((item, idx) => {
        const realIdx = items.indexOf(item);
        const pu = item.unit_price || 0;
        const total = pu * item.quantity;
        return `
            <tr class="border-b border-slate-800/80 hover:bg-slate-800/40 transition-colors">
                <td class="p-3 font-mono font-bold text-amber-400 text-xs text-center">${item.item_number}</td>
                <td class="p-3 text-slate-200 text-xs font-medium">
                    <div>${item.designation}</div>
                    <span class="text-[10px] text-slate-500">${item.lot}</span>
                </td>
                <td class="p-3 text-slate-400 text-xs text-center font-mono">${item.unit}</td>
                <td class="p-3 text-slate-300 text-xs text-right font-mono font-semibold">${item.quantity.toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 2 })}</td>
                <td class="p-2 text-right">
                    <input 
                        type="number" 
                        step="0.01" 
                        min="0" 
                        value="${pu > 0 ? pu.toFixed(2) : ''}" 
                        placeholder="0.00" 
                        onchange="updateDpgfPrice(${realIdx}, this.value)"
                        class="w-24 px-2 py-1 text-right bg-slate-950 border border-slate-700 rounded text-xs text-white font-mono focus:border-amber-500 focus:outline-none"
                    />
                </td>
                <td class="p-3 text-emerald-400 text-xs text-right font-mono font-bold">
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

    // Sum total base cost (Déboursé Sec)
    let totalDebourse = 0;
    AppState.currentAnalysis.dpgf_items.forEach(it => {
        const pu = it.unit_price || 0;
        totalDebourse += pu * it.quantity;
    });

    const fgPct = AppState.marginSettings.fraisGenerauxPct / 100;
    const margePct = AppState.marginSettings.margeNettePct / 100;
    const tvaPct = AppState.marginSettings.tvaPct / 100;

    // Standard BTP coefficient formula: Prix Vente HT = Déboursé Sec / (1 - (FG + Marge))
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
}

function renderChecklist() {
    const container = document.getElementById('checklist-items');
    if (!container) return;

    container.innerHTML = AppState.checklist.map((item, idx) => `
        <label class="flex items-center gap-3 p-3 rounded-lg border border-slate-800 bg-slate-900/40 hover:bg-slate-800/40 cursor-pointer transition-colors">
            <input 
                type="checkbox" 
                ${item.checked ? 'checked' : ''} 
                onchange="toggleChecklistItem(${idx})"
                class="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-950"
            />
            <span class="text-xs text-slate-300 font-medium select-none flex-1">${item.label}</span>
            ${item.required ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-semibold">Indispensable</span>' : ''}
        </label>
    `).join('');

    updateChecklistProgress();
}

function toggleChecklistItem(index) {
    if (AppState.checklist[index]) {
        AppState.checklist[index].checked = !AppState.checklist[index].checked;
        updateChecklistProgress();
    }
}

function updateChecklistProgress() {
    const checked = AppState.checklist.filter(i => i.checked).length;
    const total = AppState.checklist.length;
    const pct = Math.round((checked / total) * 100);

    setText('checklist-count', `${checked}/${total} pièces prêtes`);
    const bar = document.getElementById('checklist-bar');
    if (bar) bar.style.width = `${pct}%`;
}

function switchTab(tabId) {
    AppState.activeTab = tabId;
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
    const targetPane = document.getElementById(`tab-content-${tabId}`);
    if (targetPane) targetPane.classList.remove('hidden');

    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
        if (btn.dataset.tab === tabId) {
            btn.classList.add('border-amber-400', 'text-amber-400', 'bg-slate-800/60');
            btn.classList.remove('border-transparent', 'text-slate-400');
        } else {
            btn.classList.remove('border-amber-400', 'text-amber-400', 'bg-slate-800/60');
            btn.classList.add('border-transparent', 'text-slate-400');
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
            updateEngineStatusBadge(isGemini ? 'Gemini AI Connecté' : 'Moteur Expert Local', isGemini);
        }
    } catch {
        updateEngineStatusBadge('Moteur Local Actif', false);
    }
}

function updateEngineStatusBadge(text, isGemini) {
    const badge = document.getElementById('engine-status-badge');
    if (!badge) return;
    badge.textContent = text;
    if (isGemini) {
        badge.className = 'px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 inline-flex items-center gap-1.5';
    } else {
        badge.className = 'px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 inline-flex items-center gap-1.5';
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
        success: 'border-emerald-500/50 bg-slate-900 text-emerald-400',
        warning: 'border-amber-500/50 bg-slate-900 text-amber-400',
        error: 'border-rose-500/50 bg-slate-900 text-rose-400',
        info: 'border-sky-500/50 bg-slate-900 text-sky-400',
    }[type] || 'border-slate-700 bg-slate-900 text-slate-200';

    toast.className = `p-3.5 rounded-xl border shadow-xl flex items-start gap-3 transform transition-all duration-300 ease-out translate-y-2 opacity-0 text-xs ${colorClasses}`;
    toast.innerHTML = `
        <div class="grow">
            <h5 class="font-bold text-white text-xs mb-0.5">${title}</h5>
            <p class="text-slate-300">${message}</p>
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
