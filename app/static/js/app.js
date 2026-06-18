// Global State
let matchesData = [];
let appSettings = {};
let activeTab = "matches";
let pollInterval = null;

// DOM Elements
const menuMatches = document.getElementById("menu-matches");
const menuWeights = document.getElementById("menu-weights");
const menuScrapers = document.getElementById("menu-scrapers");
const menuSimulator = document.getElementById("menu-simulator");

const viewMatches = document.getElementById("view-matches");
const viewWeights = document.getElementById("view-weights");
const viewScrapers = document.getElementById("view-scrapers");
const viewSimulator = document.getElementById("view-simulator");

const pageHeading = document.getElementById("page-heading");
const pageSubheading = document.getElementById("page-subheading");

// Initial Load
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initSettings();
    initMatches();
    initSimulator();
    initScraperPanel();
});

// 1. Navigation & Tab Switching
function initNavigation() {
    const tabs = [
        { btn: menuMatches, view: viewMatches, title: "Previsões Matemáticas", subtitle: "Probabilidades consolidadas por Inteligência Estatística" },
        { btn: menuWeights, view: viewWeights, title: "Painel de Pesos", subtitle: "Ajuste a relevância de cada modelo estatístico" },
        { btn: menuScrapers, view: viewScrapers, title: "Central de Robôs", subtitle: "Gerenciador de Scrapers de dados esportivos" },
        { btn: menuSimulator, view: viewSimulator, title: "Simulador de Confrontos", subtitle: "Simule probabilidades de placares via distribuição de Poisson" }
    ];

    tabs.forEach(tab => {
        tab.btn.addEventListener("click", (e) => {
            e.preventDefault();
            
            // Update active link styles
            tabs.forEach(t => t.btn.classList.remove("active"));
            tab.btn.classList.add("active");

            // Update active views
            tabs.forEach(t => t.view.classList.remove("active"));
            tab.view.classList.add("active");

            // Update header text
            pageHeading.textContent = tab.title;
            pageSubheading.textContent = tab.subtitle;

            // Trigger view specific logic
            const hash = tab.btn.getAttribute("href").substring(1);
            activeTab = hash;
            if (hash === "matches") {
                loadMatches();
            } else if (hash === "scrapers") {
                loadScraperStatuses();
            }
        });
    });
}

// 2. Settings & Weight Tuning
function initSettings() {
    // Slider event listeners
    const sliders = ["understat", "sofascore", "odds", "whoscored", "opta"];
    sliders.forEach(src => {
        const slider = document.getElementById(`slider-${src}`);
        const pctLabel = document.getElementById(`pct-${src}`);
        
        slider.addEventListener("input", () => {
            pctLabel.textContent = `${slider.value}%`;
            
            // Dynamically update global settings state
            appSettings[`weight_${src}`] = parseFloat(slider.value) / 100;
            
            // Recalculate and update UI in real-time
            recalculateConsensusUI();
            
            // Debounce settings save to DB
            debounceSaveSettings();
        });
    });

    document.getElementById("btn-save-settings").addEventListener("click", () => {
        saveSettingsToDB();
    });

    fetchSettings();
}

async function fetchSettings() {
    try {
        const res = await fetch("/api/settings");
        if (res.ok) {
            appSettings = await res.json();
            
            // Set slider values
            const sliders = ["understat", "sofascore", "odds", "whoscored", "opta"];
            sliders.forEach(src => {
                const val = parseFloat(appSettings[`weight_${src}`] || 0.2) * 100;
                document.getElementById(`slider-${src}`).value = val;
                document.getElementById(`pct-${src}`).textContent = `${Math.round(val)}%`;
            });
            
            document.getElementById("input-odds-api-key").value = appSettings["odds_api_key"] || "";
        }
    } catch (e) {
        console.error("Failed to load settings:", e);
    }
}

let saveTimeout = null;
function debounceSaveSettings() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveSettingsToDB, 1500);
}

async function saveSettingsToDB() {
    const keyInput = document.getElementById("input-odds-api-key").value.strip ? 
                     document.getElementById("input-odds-api-key").value.trim() : 
                     document.getElementById("input-odds-api-key").value;
                     
    const payload = {
        weight_sofascore: parseFloat(document.getElementById("slider-sofascore").value) / 100,
        weight_understat: parseFloat(document.getElementById("slider-understat").value) / 100,
        weight_odds: parseFloat(document.getElementById("slider-odds").value) / 100,
        weight_whoscored: parseFloat(document.getElementById("slider-whoscored").value) / 100,
        weight_opta: parseFloat(document.getElementById("slider-opta").value) / 100,
        odds_api_key: keyInput
    };
    
    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            loggerInfo("Configurações salvas no servidor.");
        }
    } catch (e) {
        console.error("Failed to save settings:", e);
    }
}

// 3. Matches & Consensus Calculations
function initMatches() {
    // Quick filter triggers
    document.getElementById("filter-league").addEventListener("change", loadMatches);
    document.getElementById("filter-status").addEventListener("change", loadMatches);
    document.getElementById("search-teams").addEventListener("input", loadMatches);
    
    // Quick reload
    document.getElementById("btn-trigger-all-scrape").addEventListener("click", async () => {
        const btn = document.getElementById("btn-trigger-all-scrape");
        btn.disabled = true;
        btn.querySelector("i").classList.add("fa-spin");
        
        try {
            const res = await fetch("/api/scrape?scraper=all", { method: "POST" });
            if (res.ok) {
                alert("Robôs de scraping iniciados em background! As partidas serão atualizadas em breve.");
            }
        } catch (e) {
            console.error(e);
        } finally {
            btn.disabled = false;
            btn.querySelector("i").classList.remove("fa-spin");
        }
    });

    // Modal Events
    document.getElementById("btn-close-modal").addEventListener("click", closeModal);
    document.getElementById("btn-cancel-modal").addEventListener("click", closeModal);
    document.getElementById("btn-save-prediction").addEventListener("click", saveManualPrediction);

    loadMatches();
}

async function loadMatches() {
    const container = document.getElementById("match-cards-container");
    const leagueFilter = document.getElementById("filter-league").value;
    const statusFilter = document.getElementById("filter-status").value;
    const searchVal = document.getElementById("search-teams").value.toLowerCase();

    try {
        let url = "/api/matches";
        if (leagueFilter !== "all") {
            url += `?league=${leagueFilter}`;
        }
        
        const res = await fetch(url);
        if (res.ok) {
            matchesData = await res.json();
            
            // Update Header Stats
            document.getElementById("stat-matches-count").textContent = matchesData.length;
            const uniqueLeagues = new Set(matchesData.map(m => m.league));
            document.getElementById("stat-leagues-count").textContent = uniqueLeagues.size;
            
            let totalPreds = 0;
            matchesData.forEach(m => totalPreds += m.predictions.length);
            document.getElementById("stat-preds-count").textContent = totalPreds;

            // Apply Client Side Filters (Status and Search text)
            let filteredMatches = matchesData.filter(m => {
                const matchesStatus = (statusFilter === "all" || m.status === statusFilter);
                const matchesSearch = (!searchVal || 
                                       m.home_team.toLowerCase().includes(searchVal) || 
                                       m.away_team.toLowerCase().includes(searchVal));
                return matchesStatus && matchesSearch;
            });
            
            // Render
            renderMatchCards(filteredMatches);
        }
    } catch (e) {
        container.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-triangle-exclamation"></i><p>Erro ao carregar partidas: ${e.message}</p></div>`;
    }
}

function renderMatchCards(matches) {
    const container = document.getElementById("match-cards-container");
    if (matches.length === 0) {
        container.innerHTML = `<div class="loading-spinner"><i class="fa-solid fa-folder-open"></i><p>Nenhuma partida encontrada para os filtros atuais.</p></div>`;
        return;
    }

    container.innerHTML = "";
    
    // Sort matches: Agendados first, sorted by date ASC
    matches.sort((a, b) => {
        if (a.status !== b.status) {
            return a.status === "SCHEDULED" ? -1 : 1;
        }
        return new Date(a.match_date) - new Date(b.match_date);
    });

    matches.forEach(match => {
        const card = document.createElement("div");
        card.className = "match-card glass";
        card.id = `match-card-${match.id}`;
        card.setAttribute("data-match-id", match.id);
        
        // Calculate W/D/L probabilities and optimal score
        const consensus = computeConsensusPredictionLocal(match.predictions);
        
        const dateStr = formatDate(match.match_date);
        const homeScore = match.home_score !== null ? match.home_score : "";
        const awayScore = match.away_score !== null ? match.away_score : "";
        
        card.innerHTML = `
            <div class="match-card-header">
                <span class="league-badge">${match.league}</span>
                <span class="match-status-text ${match.status.toLowerCase()}">${match.status === 'FINISHED' ? 'Finalizado' : dateStr}</span>
            </div>
            
            <div class="match-card-teams">
                <div class="team-row">
                    <span class="team-name">${match.home_team}</span>
                    <span class="team-score">${homeScore}</span>
                </div>
                <div class="team-row">
                    <span class="team-name">${match.away_team}</span>
                    <span class="team-score">${awayScore}</span>
                </div>
            </div>
            
            <div class="probability-bar-container" title="Casa: ${pct(consensus.home)} | Empate: ${pct(consensus.draw)} | Fora: ${pct(consensus.away)}">
                <div class="prob-segment home" style="width: ${consensus.home * 100}%"></div>
                <div class="prob-segment draw" style="width: ${consensus.draw * 100}%"></div>
                <div class="prob-segment away" style="width: ${consensus.away * 100}%"></div>
            </div>
            
            <div class="prediction-summary">
                <div class="consensus-badge">
                    <span class="badge-label">Tendência</span>
                    <span class="badge-val text-outcome">${getOutcomeLabel(consensus)}</span>
                </div>
                <div class="optimal-score-badge">
                    <span class="badge-label">Placar Ideal (Bolão)</span>
                    <span class="badge-val text-score">${consensus.optimal_guess[0]} - ${consensus.optimal_guess[1]}</span>
                </div>
            </div>
            
            <!-- Drawer details (hidden by default) -->
            <div class="match-card-details">
                <div class="ep-calculator-box">
                    <div class="ep-title">Top 3 Placares mais Prováveis</div>
                    <div class="ep-guesses-grid">
                        ${consensus.score_probabilities.slice(0, 3).map((sp, idx) => `
                            <div class="ep-guess-item ${idx === 0 ? 'optimal' : ''}">
                                <div class="ep-guess-score">${sp.score}</div>
                                <div class="ep-guess-val">${(sp.prob * 100).toFixed(1)}%</div>
                            </div>
                        `).join("")}
                    </div>
                </div>
                
                <table class="prediction-table">
                    <thead>
                        <tr>
                            <th>Fonte</th>
                            <th>Casa</th>
                            <th>Empate</th>
                            <th>Fora</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${match.predictions.map(p => `
                            <tr>
                                <td class="table-source-name">
                                    <i class="fa-solid ${getSourceIcon(p.source)} source-icon color-${p.source}"></i>
                                    ${p.source}
                                </td>
                                <td>${(p.home_win_prob * 100).toFixed(0)}%</td>
                                <td>${(p.draw_prob * 100).toFixed(0)}%</td>
                                <td>${(p.away_win_prob * 100).toFixed(0)}%</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
                
                <button class="btn btn-outline btn-add-manual" style="width:100%; margin-top:0.5rem;" onclick="openManualModal(event, ${match.id})">
                    <i class="fa-solid fa-edit"></i> Personalizar / Adicionar Previsão
                </button>
            </div>
        `;
        
        // Expand/Collapse Details Card on click (but ignore if clicked manual button)
        card.addEventListener("click", (e) => {
            if (e.target.closest(".btn-add-manual")) return;
            card.classList.toggle("expanded");
        });
        
        container.appendChild(card);
    });
}

function recalculateConsensusUI() {
    const cards = document.querySelectorAll(".match-card");
    cards.forEach(card => {
        const matchId = parseInt(card.getAttribute("data-match-id"));
        const match = matchesData.find(m => m.id === matchId);
        if (match) {
            const consensus = computeConsensusPredictionLocal(match.predictions);
            
            // Update prob bar widths
            const homeBar = card.querySelector(".prob-segment.home");
            const drawBar = card.querySelector(".prob-segment.draw");
            const awayBar = card.querySelector(".prob-segment.away");
            
            homeBar.style.width = `${consensus.home * 100}%`;
            drawBar.style.width = `${consensus.draw * 100}%`;
            awayBar.style.width = `${consensus.away * 100}%`;
            
            card.querySelector(".probability-bar-container").title = `Casa: ${pct(consensus.home)} | Empate: ${pct(consensus.draw)} | Fora: ${pct(consensus.away)}`;
            
            // Update outcome text & score text
            card.querySelector(".text-outcome").textContent = getOutcomeLabel(consensus);
            card.querySelector(".text-score").textContent = `${consensus.optimal_guess[0]} - ${consensus.optimal_guess[1]}`;
            
            // Update Top 3 placares
            const epContainer = card.querySelector(".ep-guesses-grid");
            if (epContainer) {
                epContainer.innerHTML = consensus.score_probabilities.slice(0, 3).map((sp, idx) => `
                    <div class="ep-guess-item ${idx === 0 ? 'optimal' : ''}">
                        <div class="ep-guess-score">${sp.score}</div>
                        <div class="ep-guess-val">${(sp.prob * 100).toFixed(1)}%</div>
                    </div>
                `).join("");
            }
        }
    });
}

// 4. Mathematical Consensus Calculations - Local implementation for snappy UI
function computeConsensusPredictionLocal(predictions) {
    let active = [];
    predictions.forEach(p => {
        const source = p.source;
        const weight = appSettings[`weight_${source}`] !== undefined ? appSettings[`weight_${source}`] : 0.2;
        if (p.home_win_prob !== null && weight > 0) {
            active.push({
                weight: weight,
                home: p.home_win_prob,
                draw: p.draw_prob,
                away: p.away_win_prob
            });
        }
    });

    if (active.length === 0) {
        return { home: 0.40, draw: 0.30, away: 0.30, optimal_guess: [1, 1], score_probabilities: [{score:"1-1", prob: 0.15}] };
    }

    let totalWeight = active.reduce((sum, item) => sum + item.weight, 0);
    let avgHome = active.reduce((sum, item) => sum + item.home * item.weight, 0) / totalWeight;
    let avgDraw = active.reduce((sum, item) => sum + item.draw * item.weight, 0) / totalWeight;
    let avgAway = active.reduce((sum, item) => sum + item.away * item.weight, 0) / totalWeight;

    // Normalise
    const sum = avgHome + avgDraw + avgAway;
    avgHome /= sum;
    avgDraw /= sum;
    avgAway /= sum;

    // Estimate lambda / mu (Poisson expected goals)
    const homeShare = avgHome + 0.5 * avgDraw;
    const lambdaH = 2.6 * homeShare;
    const lambdaA = 2.6 * (1.0 - homeShare);

    // Compute score probabilities matrix
    let scoreProbs = [];
    let sumProb = 0.0;
    for (let h = 0; h <= 5; h++) {
        for (let a = 0; a <= 5; a++) {
            const pH = poissonProbability(h, lambdaH);
            const pA = poissonProbability(a, lambdaA);
            const p = pH * pA;
            scoreProbs.push({ score: `${h}-${a}`, h: h, a: a, prob: p });
            sumProb += p;
        }
    }
    
    // Normalize
    scoreProbs.forEach(sp => sp.prob /= sumProb);
    scoreProbs.sort((a, b) => b.prob - a.prob);

    // Expected points optimizer
    let bestGuess = [1, 1];
    let maxEP = -1;
    for (let gh = 0; gh <= 3; gh++) {
        for (let ga = 0; ga <= 3; ga++) {
            let ep = 0;
            const guessOutcome = getOutcome(gh, ga);
            scoreProbs.forEach(sp => {
                let pts = 0;
                if (gh === sp.h && ga === sp.a) pts = 3;
                else if (guessOutcome === getOutcome(sp.h, sp.a)) pts = 1;
                ep += pts * sp.prob;
            });
            
            if (ep > maxEP) {
                maxEP = ep;
                bestGuess = [gh, ga];
            }
        }
    }

    return {
        home: avgHome,
        draw: avgDraw,
        away: avgAway,
        optimal_guess: bestGuess,
        score_probabilities: scoreProbs
    };
}

function getOutcome(h, a) {
    if (h > a) return "HOME";
    if (h < a) return "AWAY";
    return "DRAW";
}

function poissonProbability(k, lamb) {
    if (lamb <= 0) return k === 0 ? 1 : 0;
    return (Math.pow(lamb, k) * Math.exp(-lamb)) / factorial(k);
}

function factorial(n) {
    let res = 1;
    for (let i = 2; i <= n; i++) res *= i;
    return res;
}

// 5. Manual Input Modal Operations
function openManualModal(event, matchId) {
    event.stopPropagation(); // Stop card expanding
    const match = matchesData.find(m => m.id === matchId);
    if (!match) return;

    document.getElementById("modal-match-id").value = matchId;
    document.getElementById("modal-match-description").textContent = `${match.home_team} vs ${match.away_team}`;
    
    // Reset inputs
    document.getElementById("modal-p-home").value = 45;
    document.getElementById("modal-p-draw").value = 28;
    document.getElementById("modal-p-away").value = 27;
    document.getElementById("modal-goals-home").value = "";
    document.getElementById("modal-goals-away").value = "";
    document.getElementById("modal-source").value = "manual";

    document.getElementById("manual-pred-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("manual-pred-modal").classList.remove("active");
}

async function saveManualPrediction() {
    const matchId = document.getElementById("modal-match-id").value;
    const source = document.getElementById("modal-source").value;
    
    const pHome = parseFloat(document.getElementById("modal-p-home").value) / 100;
    const pDraw = parseFloat(document.getElementById("modal-p-draw").value) / 100;
    const pAway = parseFloat(document.getElementById("modal-p-away").value) / 100;
    
    const goalsHomeVal = document.getElementById("modal-goals-home").value;
    const goalsAwayVal = document.getElementById("modal-goals-away").value;
    const goalsHome = goalsHomeVal !== "" ? parseFloat(goalsHomeVal) : null;
    const goalsAway = goalsAwayVal !== "" ? parseFloat(goalsAwayVal) : null;

    if (isNaN(pHome) || isNaN(pDraw) || isNaN(pAway)) {
        alert("Preencha as probabilidades corretamente.");
        return;
    }

    const payload = {
        source,
        home_win_prob: pHome,
        draw_prob: pDraw,
        away_win_prob: pAway,
        home_score: goalsHome,
        away_score: goalsAway
    };

    try {
        const res = await fetch(`/api/matches/${matchId}/manual`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeModal();
            loadMatches();
        } else {
            const data = await res.json();
            alert(`Erro ao salvar: ${data.detail}`);
        }
    } catch (e) {
        console.error(e);
        alert("Erro de conexão ao salvar palpite.");
    }
}

// 6. Background Scrapers Panel
function initScraperPanel() {
    const scrapers = ["understat", "sofascore", "odds"];
    scrapers.forEach(name => {
        document.getElementById(`btn-run-${name}`).addEventListener("click", () => {
            triggerScraper(name);
        });
    });

    loadScraperStatuses();
    // Poll statuses every 5 seconds
    setInterval(loadScraperStatuses, 5000);
}

async function loadScraperStatuses() {
    try {
        const res = await fetch("/api/stats");
        if (res.ok) {
            const data = await res.json();
            const scrapers = ["understat", "sofascore", "odds"];
            scrapers.forEach(name => {
                const status = data.scrapers[name] || "idle";
                const badge = document.getElementById(`status-${name}-badge`);
                badge.className = `status-badge ${status}`;
                badge.textContent = status.toUpperCase();
                
                const btn = document.getElementById(`btn-run-${name}`);
                if (status === "running") {
                    btn.disabled = true;
                    btn.textContent = "Rodando...";
                } else {
                    btn.disabled = false;
                    btn.textContent = "Rodar Scraper";
                }
            });
        }
    } catch (e) {
        console.error("Failed to load scraper statuses:", e);
    }
}

async function triggerScraper(name) {
    try {
        const res = await fetch(`/api/scrape?scraper=${name}`, { method: "POST" });
        if (res.ok) {
            loadScraperStatuses();
        }
    } catch (e) {
        console.error(e);
    }
}

// 7. Poisson Simulator View
function initSimulator() {
    document.getElementById("btn-run-simulation").addEventListener("click", runSimulation);
}

function runSimulation() {
    const homeXG = parseFloat(document.getElementById("sim-home-xg").value);
    const awayXG = parseFloat(document.getElementById("sim-away-xg").value);
    
    if (isNaN(homeXG) || isNaN(awayXG) || homeXG < 0 || awayXG < 0) {
        alert("Insira valores de xG válidos.");
        return;
    }

    // Compute probabilities matrix
    let scoreProbs = [];
    let sumProb = 0.0;
    for (let h = 0; h <= 5; h++) {
        for (let a = 0; a <= 5; a++) {
            const pH = poissonProbability(h, homeXG);
            const pA = poissonProbability(a, awayXG);
            const p = pH * pA;
            scoreProbs.push({ score: `${h}-${a}`, h: h, a: a, prob: p });
            sumProb += p;
        }
    }
    
    // Normalize
    scoreProbs.forEach(sp => sp.prob /= sumProb);

    // Sum outcomes
    let wHome = 0, wDraw = 0, wAway = 0;
    scoreProbs.forEach(sp => {
        if (sp.h > sp.a) wHome += sp.prob;
        else if (sp.h < sp.a) wAway += sp.prob;
        else wDraw += sp.prob;
    });

    scoreProbs.sort((a, b) => b.prob - a.prob);

    // Update UI
    document.getElementById("sim-prob-home").textContent = `${(wHome * 100).toFixed(1)}%`;
    document.getElementById("sim-prob-draw").textContent = `${(wDraw * 100).toFixed(1)}%`;
    document.getElementById("sim-prob-away").textContent = `${(wAway * 100).toFixed(1)}%`;

    const scoresList = document.getElementById("sim-scores-list");
    scoresList.innerHTML = scoreProbs.slice(0, 6).map(sp => `
        <div class="sim-score-item">
            <span>Placar: ${sp.score}</span>
            <span class="sim-score-val">${(sp.prob * 100).toFixed(1)}%</span>
        </div>
    `).join("");

    document.getElementById("sim-results").style.display = "block";
}

// Helpers
function formatDate(dateStr) {
    // ISO Format: YYYY-MM-DD HH:MM
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${day}/${month} às ${hours}:${minutes}`;
}

function pct(val) {
    return `${Math.round(val * 100)}%`;
}

function getOutcomeLabel(consensus) {
    if (consensus.home > consensus.away && consensus.home > consensus.draw) {
        return `Casa (${pct(consensus.home)})`;
    } else if (consensus.away > consensus.home && consensus.away > consensus.draw) {
        return `Fora (${pct(consensus.away)})`;
    } else {
        return `Empate (${pct(consensus.draw)})`;
    }
}

function getSourceIcon(source) {
    switch(source) {
        case "understat": return "fa-chart-line";
        case "sofascore": return "fa-users";
        case "odds": return "fa-coins";
        case "whoscored": return "fa-award";
        case "opta": return "fa-robot";
        case "manual": return "fa-edit";
        default: return "fa-database";
    }
}

function loggerInfo(msg) {
    console.log(`[Bolão Expert] ${msg}`);
}
