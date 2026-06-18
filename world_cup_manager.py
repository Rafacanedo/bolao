import os
import csv
import json
import math
import sys
import argparse
from datetime import datetime
from app.scorepick_client import ScorePickClient

CSV_PATH = "/home/rafa/Projects/bolao/world_cup_2026.csv"
SETTINGS_PATH = "/home/rafa/Projects/bolao/settings.json"

# Pre-compiled match data for World Cup 2026 (June 15, 16, 17)
DEFAULT_WORLD_CUP_MATCHES = [
    {
        "id": "WC26-01",
        "date": "2026-06-15 15:00",
        "home_team": "Espanha",
        "away_team": "Cabo Verde",
        "home_emoji": "🇪🇸",
        "away_emoji": "🇨🇻",
        "stage": "Fase de Grupos - Grupo H",
        "venue": "Atlanta Stadium (Atlanta, EUA)",
        "weather": "Calor intenso, umidade moderada.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.80, "draw": 0.14, "away": 0.06},
        "prob_sofascore": {"home": 0.76, "draw": 0.16, "away": 0.08},
        "odds": {"home": 1.22, "draw": 5.80, "away": 13.00},
        "tactical_analysis": (
            "A Espanha deve dominar completamente a posse de bola no seu clássico estilo de controle posicional, "
            "com Lamine Yamal e Nico Williams explorando os lados do campo. Cabo Verde tentará se fechar em bloco "
            "baixo e contra-atacar em velocidade."
        ),
        "key_factors": "Espanha completa com Rodri no meio-campo. Cabo Verde tem boa solidez física, mas desfalques na criação criativa.",
        "pro_opinion": (
            "Tiago Leifert destaca o favoritismo absoluto da Espanha, prevendo que o time espanhol deve controlar "
            "as ações por completo. Arnaldo Ribeiro alerta para a forte retranca de Cabo Verde, sugerindo que se a "
            "Espanha não marcar cedo, a partida pode ganhar contornos dramáticos."
        ),
        "cheeky_prediction": "3 - 0. A Espanha vai atropelar taticamente, com Yamal e Nico brilhando pelas pontas sob forte calor em Atlanta."
    },
    {
        "id": "WC26-02",
        "date": "2026-06-15 18:00",
        "home_team": "Bélgica",
        "away_team": "Egito",
        "home_emoji": "🇧🇪",
        "away_emoji": "🇪🇬",
        "stage": "Fase de Grupos - Grupo G",
        "venue": "BC Place (Vancouver, Canadá)",
        "weather": "Temperatura agradável (estádio fechado/teto retrátil).",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.58, "draw": 0.24, "away": 0.18},
        "prob_sofascore": {"home": 0.54, "draw": 0.26, "away": 0.20},
        "odds": {"home": 1.70, "draw": 3.65, "away": 4.80},
        "tactical_analysis": (
            "Bélgica entra em fase de transição, mas ainda conta com a genialidade de Kevin De Bruyne na criação. "
            "O Egito joga sob um esquema compacto e foca em transições rápidas para acionar Mohamed Salah pela direita."
        ),
        "key_factors": "Bélgica com dúvidas na zaga (Vertonghen aposentado/lesionado). Egito completo e extremamente motivado.",
        "pro_opinion": (
            "Casimiro (CazéTV) comenta que o Egito é uma seleção muito chata de enfrentar e que Salah sempre tira um "
            "coelho da cartola. Thiago Asmar indica que a zaga da Bélgica em transição é o calcanhar de aquiles que "
            "o Egito tentará explorar."
        ),
        "cheeky_prediction": "1 - 1. O palpite ousado é um empate com Salah marcando no contra-ataque contra a lenta zaga belga."
    },
    {
        "id": "WC26-03",
        "date": "2026-06-15 21:00",
        "home_team": "Arábia Saudita",
        "away_team": "Uruguai",
        "home_emoji": "🇸🇦",
        "away_emoji": "🇺🇾",
        "stage": "Fase de Grupos - Grupo H",
        "venue": "Miami Stadium (Miami, EUA)",
        "weather": "Clima abafado típico da Flórida.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.12, "draw": 0.22, "away": 0.66},
        "prob_sofascore": {"home": 0.14, "draw": 0.24, "away": 0.62},
        "odds": {"home": 7.00, "draw": 4.20, "away": 1.45},
        "tactical_analysis": (
            "O Uruguai de Marcelo Bielsa vai pressionar alto e imprimir um ritmo de jogo extremamente intenso "
            "com Fede Valverde no meio e Darwin Núñez no ataque. A Arábia Saudita tentará cadenciar o ritmo com posse "
            "curta, mas sofre fisicamente contra times sul-americanos intensos."
        ),
        "key_factors": "Uruguai conta com força máxima e forte apoio da torcida latina em Miami. Arábia desfalcada de seu principal zagueiro.",
        "pro_opinion": (
            "Arnaldo Ribeiro espera uma pressão sufocante do Uruguai de Bielsa logo nos primeiros minutos. "
            "Tiago Leifert aponta que o Uruguai tem intensidade demais para a Arábia aguentar física e taticamente."
        ),
        "cheeky_prediction": "0 - 3. O Uruguai de Bielsa não vai tirar o pé do acelerador, empurrado pela torcida latina em Miami."
    },
    {
        "id": "WC26-04",
        "date": "2026-06-15 23:30",
        "home_team": "Irã",
        "away_team": "Nova Zelândia",
        "home_emoji": "🇮🇷",
        "away_emoji": "🇳🇿",
        "stage": "Fase de Grupos - Grupo G",
        "venue": "Los Angeles Stadium (Los Angeles, EUA)",
        "weather": "Clima agradável.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.51, "draw": 0.28, "away": 0.21},
        "prob_sofascore": {"home": 0.48, "draw": 0.29, "away": 0.23},
        "odds": {"home": 1.95, "draw": 3.30, "away": 3.90},
        "tactical_analysis": (
            "Espera-se a partida mais travada e física do dia. O Irã de Carlos Queiroz/escola defensiva se fechará "
            "e buscará transições longas para Mehdi Taremi resolver individualmente. A Nova Zelândia usará a força física "
            "e jogará no erro adversário, cruzando bolas na área para o pivô de Chris Wood."
        ),
        "key_factors": "Ambas as seleções chegam completas. O Irã tem mais bagagem internacional e jogadores acostumados com a pressão de Copas do Mundo. A Nova Zelândia joga com forte dedicação física, mas tem sérios problemas de criatividade no meio-campo.",
        "pro_opinion": (
            "Arnaldo Ribeiro indica que jogos com este perfil de equilíbrio técnico baixo e muita força física "
            "tendem a ter pouquíssimos gols na estreia. Tiago Leifert aponta que o Irã é mais time no chão, "
            "mas a bola aérea de Chris Wood é um perigo real se a zaga iraniana falhar no posicionamento."
        ),
        "cheeky_prediction": "1 - 1. A Nova Zelândia é limitada, mas a bola aérea de Wood contra a defesa iraniana pode forçar um empate truncado na estreia."
    },
    {
        "id": "WC26-05",
        "date": "2026-06-16 13:00",
        "home_team": "França",
        "away_team": "Senegal",
        "home_emoji": "🇫🇷",
        "away_emoji": "🇸🇳",
        "stage": "Fase de Grupos - Grupo I",
        "venue": "MetLife Stadium (East Rutherford, EUA)",
        "weather": "Noite fresca, vento moderado.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.67, "draw": 0.21, "away": 0.12},
        "prob_sofascore": {"home": 0.63, "draw": 0.23, "away": 0.14},
        "odds": {"home": 1.42, "draw": 4.30, "away": 7.50},
        "tactical_analysis": (
            "A França tem um dos elencos mais letais do mundo, liderado por Kylian Mbappé em velocidade. Senegal "
            "é a principal força africana, jogando de forma física e compacta. Se Senegal conseguir segurar a pressão "
            "inicial, pode incomodar nos contra-ataques rápidos."
        ),
        "key_factors": "França com Mbappé confirmado. Senegal desfalcada de um volante titular por suspensão.",
        "pro_opinion": (
            "Casimiro comenta que Senegal é disparado o melhor time africano, mas a França com Mbappé é imparável "
            "se houver espaço para correr. Mauro Cezar avalia que o meio de campo francês ditará o ritmo da vitória segura."
        ),
        "cheeky_prediction": "2 - 1. Senegal é forte física e defensivamente, conseguirá marcar um gol na bola parada, mas a França vence na individualidade de Mbappé."
    },
    {
        "id": "WC26-06",
        "date": "2026-06-16 16:00",
        "home_team": "Iraque",
        "away_team": "Noruega",
        "home_emoji": "🇮🇶",
        "away_emoji": "🇳🇴",
        "stage": "Fase de Grupos - Grupo I",
        "venue": "Gillette Stadium (Foxborough, EUA)",
        "weather": "Clima ameno de Massachusetts.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.16, "draw": 0.24, "away": 0.60},
        "prob_sofascore": {"home": 0.18, "draw": 0.25, "away": 0.57},
        "odds": {"home": 5.50, "draw": 3.75, "away": 1.62},
        "tactical_analysis": (
            "A Noruega conta com a potência devastadora de Erling Haaland e os passes cirúrgicos de Martin Ødegaard. "
            "O Iraque é raçudo e foca em compactar o meio, mas tem sérias dificuldades contra atacantes físicos e de elite."
        ),
        "key_factors": "Haaland e Ødegaard em excelente forma física. Iraque completo mas taticamente inferior.",
        "pro_opinion": (
            "Tiago Leifert avisa que Ødegaard flutuando livre vai enfiar três ou quatro bolas limpas para Haaland guardar. "
            "Arnaldo Ribeiro ressalta que o Iraque não tem recursos físicos para conter Haaland por 90 minutos."
        ),
        "cheeky_prediction": "0 - 3. Haaland deve começar sua campanha de artilheiro com pelo menos dois gols diante da frágil defesa iraquiana."
    },
    {
        "id": "WC26-07",
        "date": "2026-06-16 19:00",
        "home_team": "Argentina",
        "away_team": "Argélia",
        "home_emoji": "🇦🇷",
        "away_emoji": "🇩🇿",
        "stage": "Fase de Grupos - Grupo J",
        "venue": "Arrowhead Stadium (Kansas City, EUA)",
        "weather": "Clima quente, céu aberto.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.73, "draw": 0.18, "away": 0.09},
        "prob_sofascore": {"home": 0.70, "draw": 0.19, "away": 0.11},
        "odds": {"home": 1.30, "draw": 5.00, "away": 9.50},
        "tactical_analysis": (
            "Argentina jogará com controle total de posse de bola e Lionel Messi flutuando entre as linhas. "
            "A Argélia é taticamente imprevisível, forte individualmente mas instável na defesa contra trocas de passes rápidas."
        ),
        "key_factors": "Argentina completa e favorita ao título. Argélia aposta em contra-ataques rápidos com Mahrez (se atuar).",
        "pro_opinion": (
            "Casimiro crê em noite festiva para Lionel Messi distribuindo assistências. Arnaldo Ribeiro aponta que "
            "a Argélia tem qualidade individual no ataque, mas peca na recomposição tática contra tabelas curtas."
        ),
        "cheeky_prediction": "3 - 1. A Argentina domina e goleia, mas a Argélia deve conseguir um gol de honra em jogada individual rápida."
    },
    {
        "id": "WC26-08",
        "date": "2026-06-16 22:00",
        "home_team": "Áustria",
        "away_team": "Jordânia",
        "home_emoji": "🇦🇹",
        "away_emoji": "🇯🇴",
        "stage": "Fase de Grupos - Grupo J",
        "venue": "Levi's Stadium (Santa Clara, EUA)",
        "weather": "Clima fresco da Califórnia.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.60, "draw": 0.25, "away": 0.15},
        "prob_sofascore": {"home": 0.57, "draw": 0.27, "away": 0.16},
        "odds": {"home": 1.60, "draw": 3.70, "away": 5.75},
        "tactical_analysis": (
            "A Áustria sob o comando do estilo de 'Gegenpressing' de Ralf Rangnick vai sufocar a saída de bola da Jordânia. "
            "A Jordânia, surpresa asiática, joga recuada e explora a velocidade, mas terá imensa dificuldade para respirar "
            "contra a pressão austríaca."
        ),
        "key_factors": "Áustria com style físico e intenso muito bem assimilado. Jordânia sem desfalques mas limitada tecnicamente.",
        "pro_opinion": (
            "Mauro Cezar analisa que a pressão pós-perda da Áustria de Ralf Rangnick vai asfixiar a Jordânia. "
            "Tiago Leifert elogia a velocidade da Jordânia nos contra-ataques, mas acha imprevisível resistirem à intensidade austríaca."
        ),
        "cheeky_prediction": "2 - 0. A Áustria ganha sem sustos, forçando erros na saída de bola jordaniana desde o início."
    },
    {
        "id": "WC26-09",
        "date": "2026-06-17 11:00",
        "home_team": "Portugal",
        "away_team": "RD Congo",
        "home_emoji": "🇵🇹",
        "away_emoji": "🇨🇩",
        "stage": "Fase de Grupos - Grupo K",
        "venue": "NRG Stadium (Houston, EUA)",
        "weather": "Clima quente e úmido de Houston.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.71, "draw": 0.19, "away": 0.10},
        "prob_sofascore": {"home": 0.68, "draw": 0.20, "away": 0.12},
        "odds": {"home": 1.35, "draw": 4.60, "away": 8.00},
        "tactical_analysis": (
            "Portugal tem um ataque avassalador com Bruno Fernandes, Rafael Leão e Cristiano Ronaldo. A RD Congo tenta "
            "compensar a disparidade técnica com imposição física e transições aéreas, mas concede muitos espaços "
            "entre as linhas defensivas."
        ),
        "key_factors": "Portugal completo e muito entrosado. RD Congo joga no limite físico.",
        "pro_opinion": (
            "Casimiro destaca a abundância de talento em Portugal, sugerindo placar elástico caso Bruno Fernandes "
            "esteja inspirado. Arnaldo Ribeiro aponta a RD Congo como fisicamente muito forte, mas indisciplinada taticamente."
        ),
        "cheeky_prediction": "4 - 1. Portugal passeia com gols de Cristiano Ronaldo e Rafael Leão explorando as costas da zaga congolesa."
    },
    {
        "id": "WC26-10",
        "date": "2026-06-17 14:00",
        "home_team": "Inglaterra",
        "away_team": "Croácia",
        "home_emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "away_emoji": "🇭🇷",
        "stage": "Fase de Grupos - Grupo K",
        "venue": "AT&T Stadium (Arlington, EUA)",
        "weather": "Clima ameno, estádio fechado.",
        "status": "SCHEDULED",
        "prob_opta": {"home": 0.49, "draw": 0.28, "away": 0.23},
        "prob_sofascore": {"home": 0.46, "draw": 0.29, "away": 0.25},
        "odds": {"home": 1.95, "draw": 3.35, "away": 3.75},
        "tactical_analysis": (
            "O confronto mais equilibrado da rodada. A Inglaterra aposta na criatividade de Jude Bellingham e na "
            "finalização cirúrgica de Harry Kane. A Croácia, comandada pelo lendário Luka Modric, dita o ritmo "
            "cadenciado do jogo com seu meio-campo técnico, tentando esfriar a partida."
        ),
        "key_factors": "Inglaterra com Bellingham e Kane em alta. Croácia com zaga sólida liderada por Gvardiol, Modric faz sua última Copa.",
        "pro_opinion": (
            "Tiago Leifert prevê um jogo de xadrez, onde Modric tentará acalmar a partida para anular a velocidade "
            "de Bellingham e Foden. Arnaldo Ribeiro acredita que a Inglaterra é favorita física, mas a Croácia é "
            "mestre em levar jogos equilibrados em Copas."
        ),
        "cheeky_prediction": "1 - 1. Jogo muito estudado e cadenciado no meio-campo. A Croácia é especialista em estreias duras e segura o empate."
    }
]

MATCHES_JSON_PATH = "/home/rafa/Projects/bolao/world_cup_matches.json"

def load_world_cup_matches():
    if not os.path.exists(MATCHES_JSON_PATH):
        try:
            with open(MATCHES_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_WORLD_CUP_MATCHES, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao inicializar world_cup_matches.json: {e}")
        return DEFAULT_WORLD_CUP_MATCHES
    try:
        with open(MATCHES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar world_cup_matches.json: {e}. Usando lista padrão.")
        return DEFAULT_WORLD_CUP_MATCHES

WORLD_CUP_MATCHES = load_world_cup_matches()


# Helper math functions
def poisson_probability(k, lamb):
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lamb, k) * math.exp(-lamb)) / math.factorial(k)

def calculate_score_probs(lambda_h, lambda_a, max_goals=5):
    scores = {}
    total_prob = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob = poisson_probability(h, lambda_h) * poisson_probability(a, lambda_a)
            scores[(h, a)] = prob
            total_prob += prob
    for k in scores:
        scores[k] /= total_prob
    return scores

def calculate_expected_points(guess_h, guess_a, score_probs):
    expected_pts = 0.0
    g_outcome = "HOME" if guess_h > guess_a else ("AWAY" if guess_h < guess_a else "DRAW")
    for (ah, aa), prob in score_probs.items():
        pts_outcome = 0
        a_outcome = "HOME" if ah > aa else ("AWAY" if ah < aa else "DRAW")
        if g_outcome == a_outcome:
            pts_outcome = 2
            
        pts_exact = 0
        if guess_h == ah and guess_a == aa:
            pts_exact = 5
            
        pts_bonus = 0
        if pts_outcome == 2 and pts_exact == 0:
            if guess_h == ah or guess_a == aa:
                pts_bonus = 1
                
        game_total = 5 if pts_exact == 5 else (pts_outcome + pts_bonus)
        expected_pts += game_total * prob
    return expected_pts

# Load settings (weights)
def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        default = {
            "weight_opta": 0.30, 
            "weight_sofascore": 0.30, 
            "weight_odds": 0.40, 
            "odds_api_key": "",
            "predicted_champion": "França",
            "predicted_top_scorer": "Kylian Mbappé",
            "points_champion": 0,
            "points_top_scorer": 0,
            "resolved_champion": False,
            "resolved_top_scorer": False,
            "prediction_strategy": "ML"
        }
        with open(SETTINGS_PATH, "w") as f:
            json.dump(default, f, indent=2)
        return default
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
    
    # Ensure default values are present for bolao settings
    defaults_added = False
    for k, v in [
        ("predicted_champion", "França"),
        ("predicted_top_scorer", "Kylian Mbappé"),
        ("points_champion", 0),
        ("points_top_scorer", 0),
        ("resolved_champion", False),
        ("resolved_top_scorer", False),
        ("prediction_strategy", "ML")
    ]:
        if k not in settings:
            settings[k] = v
            defaults_added = True
            
    if defaults_added:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
            
    return settings

# Save settings
def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)

# Get odds probability
def get_odds_prob(odds):
    imp_h = 1.0 / float(odds["home"])
    imp_d = 1.0 / float(odds["draw"])
    imp_a = 1.0 / float(odds["away"])
    sum_imp = imp_h + imp_d + imp_a
    return {"home": imp_h / sum_imp, "draw": imp_d / sum_imp, "away": imp_a / sum_imp}

def get_calibrated_total_goals():
    try:
        scores = read_csv_scores()
        finished_goals = []
        for m_id, s in scores.items():
            if s.get("status") == "FINISHED" and s.get("home") is not None and s.get("away") is not None:
                finished_goals.append(int(s["home"]) + int(s["away"]))
        if finished_goals:
            avg_goals = sum(finished_goals) / len(finished_goals)
            return max(2.0, min(3.5, avg_goals))
    except Exception:
        pass
    return 2.6

def load_team_metrics():
    import sqlite3
    db_path = "/home/rafa/Projects/bolao/bolao.db"
    if not os.path.exists(db_path):
        return {}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT team_name, fifa_points, market_value_eur, pele_rating, pele_tilt FROM world_cup_teams")
        rows = cursor.fetchall()
        conn.close()
        return {r[0]: {
            "fifa_points": r[1],
            "market_value": r[2],
            "pele_rating": r[3],
            "pele_tilt": r[4]
        } for r in rows}
    except Exception as e:
        print(f"Erro ao carregar métricas das seleções do banco de dados: {e}")
        return {}

# Carrega métricas globais uma única vez na inicialização
TEAM_METRICS = load_team_metrics()

def get_pele_prob(home, away):
    h_m = TEAM_METRICS.get(home, {"pele_rating": 1750.0, "pele_tilt": 0.0})
    a_m = TEAM_METRICS.get(away, {"pele_rating": 1750.0, "pele_tilt": 0.0})
    
    r_h = h_m["pele_rating"]
    r_a = a_m["pele_rating"]
    
    # Bônus de Host (EUA, México e Canadá jogando em casa na América do Norte)
    if home in ["Estados Unidos", "México", "Canadá"]:
        r_h += 50.0
    if away in ["Estados Unidos", "México", "Canadá"]:
        r_a += 50.0
        
    diff = r_h - r_a
    base_goals = get_calibrated_total_goals() / 2.0
    
    # Ajuste de Tilt (postura ultra-ofensiva ou defensiva)
    tilt_h = h_m["pele_tilt"]
    tilt_a = a_m["pele_tilt"]
    tilt_adjust = (tilt_h + tilt_a) * 0.5
    
    lambda_h = max(0.2, base_goals + 0.05 * (diff / 10.0) + tilt_adjust)
    lambda_a = max(0.2, base_goals - 0.05 * (diff / 10.0) + tilt_adjust)
    
    score_probs = calculate_score_probs(lambda_h, lambda_a)
    h_prob = sum(p for (h, a), p in score_probs.items() if h > a)
    d_prob = sum(p for (h, a), p in score_probs.items() if h == a)
    a_prob = sum(p for (h, a), p in score_probs.items() if h < a)
    
    s = h_prob + d_prob + a_prob
    return {"home": h_prob / s, "draw": d_prob / s, "away": a_prob / s}

def get_fifa_tm_prob(home, away):
    h_m = TEAM_METRICS.get(home, {"fifa_points": 1500.0, "market_value": 100.0})
    a_m = TEAM_METRICS.get(away, {"fifa_points": 1500.0, "market_value": 100.0})
    
    # Normalização de pontos FIFA (base 1200)
    f_h = (h_m["fifa_points"] - 1200.0) / 10.0
    f_a = (a_m["fifa_points"] - 1200.0) / 10.0
    
    # Normalização do preço do elenco no Transfermarkt (escala logarítmica)
    tm_h = 20.0 * math.log10(max(1.0, h_m["market_value"]))
    tm_a = 20.0 * math.log10(max(1.0, a_m["market_value"]))
    
    # Rating composto: 45% FIFA + 55% Transfermarkt
    r_h = 0.45 * f_h + 0.55 * tm_h
    r_a = 0.45 * f_a + 0.55 * tm_a
    
    # Bônus de Host
    if home in ["Estados Unidos", "México", "Canadá"]:
        r_h += 5.0
    if away in ["Estados Unidos", "México", "Canadá"]:
        r_a += 5.0
        
    diff = r_h - r_a
    base_goals = get_calibrated_total_goals() / 2.0
    
    lambda_h = max(0.2, base_goals + 0.05 * diff)
    lambda_a = max(0.2, base_goals - 0.05 * diff)
    
    score_probs = calculate_score_probs(lambda_h, lambda_a)
    h_prob = sum(p for (h, a), p in score_probs.items() if h > a)
    d_prob = sum(p for (h, a), p in score_probs.items() if h == a)
    a_prob = sum(p for (h, a), p in score_probs.items() if h < a)
    
    s = h_prob + d_prob + a_prob
    return {"home": h_prob / s, "draw": d_prob / s, "away": a_prob / s}

def get_prediction_from_ratings(home, away):
    # Delegação integrada para compatibilidade
    pele = get_pele_prob(home, away)
    fifa_tm = get_fifa_tm_prob(home, away)
    
    h_prob = 0.60 * pele["home"] + 0.40 * fifa_tm["home"]
    d_prob = 0.60 * pele["draw"] + 0.40 * fifa_tm["draw"]
    a_prob = 0.60 * pele["away"] + 0.40 * fifa_tm["away"]
    
    s = h_prob + d_prob + a_prob
    return h_prob / s, d_prob / s, a_prob / s

def compute_predictions(match, settings):
    opta = match.get("prob_opta", {"home": 0.333, "draw": 0.333, "away": 0.334})
    sofa = match.get("prob_sofascore", {"home": 0.333, "draw": 0.333, "away": 0.334})
    
    is_opta_fallback = abs(opta.get("home", 0.333) - 0.333) < 0.01
    is_sofa_fallback = abs(sofa.get("home", 0.333) - 0.333) < 0.01
    
    pele_prob = get_pele_prob(match["home_team"], match["away_team"])
    fifa_tm_prob = get_fifa_tm_prob(match["home_team"], match["away_team"])
    odds_prob = get_odds_prob(match["odds"])
    
    # Pesos padrão do ensemble
    w_pele = 0.35
    w_fifa_tm = 0.25
    w_odds = 0.40
    
    if not is_opta_fallback and not is_sofa_fallback:
        w_pele = 0.30
        w_fifa_tm = 0.20
        w_odds = 0.30
        w_opta = float(settings.get("weight_opta", 0.12))
        w_sofa = float(settings.get("weight_sofascore", 0.08))
        
        sum_w = w_pele + w_fifa_tm + w_odds + w_opta + w_sofa
        w_pele /= sum_w
        w_fifa_tm /= sum_w
        w_odds /= sum_w
        w_opta /= sum_w
        w_sofa /= sum_w
        
        consensus_h = pele_prob["home"] * w_pele + fifa_tm_prob["home"] * w_fifa_tm + odds_prob["home"] * w_odds + opta["home"] * w_opta + sofa["home"] * w_sofa
        consensus_d = pele_prob["draw"] * w_pele + fifa_tm_prob["draw"] * w_fifa_tm + odds_prob["draw"] * w_odds + opta["draw"] * w_opta + sofa["draw"] * w_sofa
        consensus_a = pele_prob["away"] * w_pele + fifa_tm_prob["away"] * w_fifa_tm + odds_prob["away"] * w_odds + opta["away"] * w_opta + sofa["away"] * w_sofa
    else:
        consensus_h = pele_prob["home"] * w_pele + fifa_tm_prob["home"] * w_fifa_tm + odds_prob["home"] * w_odds
        consensus_d = pele_prob["draw"] * w_pele + fifa_tm_prob["draw"] * w_fifa_tm + odds_prob["draw"] * w_odds
        consensus_a = pele_prob["away"] * w_pele + fifa_tm_prob["away"] * w_fifa_tm + odds_prob["away"] * w_odds
        
    s = consensus_h + consensus_d + consensus_a
    consensus_h /= s
    consensus_d /= s
    consensus_a /= s
    
    # Expectativa de gols de Poisson
    total_goals = get_calibrated_total_goals()
    home_share = consensus_h + 0.5 * consensus_d
    lambda_h = total_goals * home_share
    lambda_a = total_goals * (1.0 - home_share)
    
    # Probabilidade crua de gols
    score_probs = calculate_score_probs(lambda_h, lambda_a)
    
    # Calibração de empates (Adaptação Dixon-Coles)
    raw_draw = sum(p for (h, a), p in score_probs.items() if h == a)
    if consensus_d > raw_draw:
        diff_d = consensus_d - raw_draw
        score_probs[(1, 1)] = score_probs.get((1, 1), 0.0) + diff_d * 0.60
        score_probs[(0, 0)] = score_probs.get((0, 0), 0.0) + diff_d * 0.30
        score_probs[(2, 2)] = score_probs.get((2, 2), 0.0) + diff_d * 0.10
        
        s_probs = sum(score_probs.values())
        for k in score_probs:
            score_probs[k] /= s_probs
    elif consensus_d < raw_draw and raw_draw > 0:
        factor = consensus_d / raw_draw
        for (h, a) in list(score_probs.keys()):
            if h == a:
                score_probs[(h, a)] *= factor
        s_probs = sum(score_probs.values())
        for k in score_probs:
            score_probs[k] /= s_probs
            
    # Escolha do palpite ideal baseada na estratégia configurada (ML ou EP)
    strategy = settings.get("prediction_strategy", "ML")
    if strategy == "ML":
        best_guess = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[0][0]
        max_ep = calculate_expected_points(best_guess[0], best_guess[1], score_probs)
    else:
        best_guess = (1, 1)
        max_ep = -1.0
        for gh in range(6):  # Expandido para 0-5 gols
            for ga in range(6):
                ep = calculate_expected_points(gh, ga, score_probs)
                if ep > max_ep:
                    max_ep = ep
                    best_guess = (gh, ga)
                
    return {
        "consensus": (consensus_h, consensus_d, consensus_a),
        "suggested": best_guess,
        "expected_points": max_ep,
        "top_scores": sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:3]
    }

# Read existing results from CSV (to preserve actual scores entered by user)
def read_csv_scores():
    scores = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("home_score") and row.get("away_score"):
                    scores[row["match_id"]] = {
                        "home": int(row["home_score"]),
                        "away": int(row["away_score"]),
                        "status": row.get("status", "FINISHED")
                    }
    return scores

# Write / Update CSV with specific scores and settings
def update_csv_with_scores(scores, settings=None):
    if settings is None:
        settings = load_settings()
        
    headers = [
        "match_id", "date", "home_team", "away_team", "stage", "venue", "status",
        "home_score", "away_score", "prob_opta_home", "prob_opta_draw", "prob_opta_away",
        "prob_sofascore_home", "prob_sofascore_draw", "prob_sofascore_away",
        "odds_home", "odds_draw", "odds_away",
        "consensus_home", "consensus_draw", "consensus_away",
        "suggested_score", "expected_points", "tactical_summary",
        "home_emoji", "away_emoji", "weather", "pro_opinion", "cheeky_prediction"
    ]
    
    rows = []
    for match in WORLD_CUP_MATCHES:
        pred = compute_predictions(match, settings)
        
        # Pull score from CSV if already recorded as played
        m_id = match["id"]
        h_score = ""
        a_score = ""
        status = match["status"]
        if m_id in scores:
            h_score = scores[m_id]["home"]
            a_score = scores[m_id]["away"]
            status = scores[m_id]["status"]
            
        # Format Top 3 scores for CSV
        top_scores_formatted = ", ".join([f"{s[0][0]}x{s[0][1]} ({s[1]*100:.1f}%)" for s in pred["top_scores"]])
            
        row = {
            "match_id": m_id,
            "date": match["date"],
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "stage": match["stage"],
            "venue": match["venue"],
            "status": status,
            "home_score": h_score,
            "away_score": a_score,
            "prob_opta_home": f"{match['prob_opta']['home']:.2f}",
            "prob_opta_draw": f"{match['prob_opta']['draw']:.2f}",
            "prob_opta_away": f"{match['prob_opta']['away']:.2f}",
            "prob_sofascore_home": f"{match['prob_sofascore']['home']:.2f}",
            "prob_sofascore_draw": f"{match['prob_sofascore']['draw']:.2f}",
            "prob_sofascore_away": f"{match['prob_sofascore']['away']:.2f}",
            "odds_home": f"{match['odds']['home']:.2f}",
            "odds_draw": f"{match['odds']['draw']:.2f}",
            "odds_away": f"{match['odds']['away']:.2f}",
            "consensus_home": f"{pred['consensus'][0]:.2f}",
            "consensus_draw": f"{pred['consensus'][1]:.2f}",
            "consensus_away": f"{pred['consensus'][2]:.2f}",
            "suggested_score": top_scores_formatted,
            "expected_points": f"{pred['expected_points']:.2f}",
            "tactical_summary": match["tactical_analysis"][:150] + "...",
            "home_emoji": match.get("home_emoji", ""),
            "away_emoji": match.get("away_emoji", ""),
            "weather": match.get("weather", ""),
            "pro_opinion": match.get("pro_opinion", ""),
            "cheeky_prediction": match.get("cheeky_prediction", "")
        }
        rows.append(row)
        
    try:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")
        return False

# Write / Update CSV with current state
def update_csv():
    return update_csv_with_scores(read_csv_scores(), load_settings())

# Brier score calculation (BS = sum( (p_i - y_i)^2 ))
def get_brier_score(prob_h, prob_d, prob_a, actual_outcome):
    y_h = 1.0 if actual_outcome == "HOME" else 0.0
    y_d = 1.0 if actual_outcome == "DRAW" else 0.0
    y_a = 1.0 if actual_outcome == "AWAY" else 0.0
    return math.pow(prob_h - y_h, 2) + math.pow(prob_d - y_d, 2) + math.pow(prob_a - y_a, 2)

# Tuning weights based on past finished games
def tune_weights():
    print("=== DYNAMIC WEIGHT TUNING MODULE ===")
    existing_scores = read_csv_scores()
    
    finished_games = []
    for match in WORLD_CUP_MATCHES:
        m_id = match["id"]
        if m_id in existing_scores and existing_scores[m_id]["status"] == "FINISHED":
            home_s = existing_scores[m_id]["home"]
            away_s = existing_scores[m_id]["away"]
            outcome = "HOME" if home_s > away_s else ("AWAY" if home_s < away_s else "DRAW")
            finished_games.append({
                "match": match,
                "outcome": outcome
            })
            
    if not finished_games:
        print("Aviso: Nenhum jogo finalizado encontrado no CSV. Mais jogos são necessários para calibrar os pesos.")
        return
        
    print(f"Analisando {len(finished_games)} partida(s) finalizada(s) para calibração...")
    
    # Calculate average Brier Score for each source
    brier_opta = 0.0
    brier_sofa = 0.0
    brier_odds = 0.0
    
    for game in finished_games:
        m = game["match"]
        out = game["outcome"]
        
        # Opta
        brier_opta += get_brier_score(m["prob_opta"]["home"], m["prob_opta"]["draw"], m["prob_opta"]["away"], out)
        # Sofascore
        brier_sofa += get_brier_score(m["prob_sofascore"]["home"], m["prob_sofascore"]["draw"], m["prob_sofascore"]["away"], out)
        # Odds
        odds_p = get_odds_prob(m["odds"])
        brier_odds += get_brier_score(odds_p["home"], odds_p["draw"], odds_p["away"], out)
        
    avg_b_opta = brier_opta / len(finished_games)
    avg_b_sofa = brier_sofa / len(finished_games)
    avg_b_odds = brier_odds / len(finished_games)
    
    print(f"Brier Scores Médios (Menor é melhor):")
    print(f"  - Opta: {avg_b_opta:.4f}")
    print(f"  - Sofascore: {avg_b_sofa:.4f}")
    print(f"  - Odds de Mercado: {avg_b_odds:.4f}")
    
    # Compute accuracy scores (2.0 - BrierScore, where 2.0 is worst and 0.0 is perfect)
    acc_opta = max(0.01, 2.0 - avg_b_opta)
    acc_sofa = max(0.01, 2.0 - avg_b_sofa)
    acc_odds = max(0.01, 2.0 - avg_b_odds)
    
    # Calculate new normalized weights
    sum_acc = acc_opta + acc_sofa + acc_odds
    new_w_opta = acc_opta / sum_acc
    new_w_sofa = acc_sofa / sum_acc
    new_w_odds = acc_odds / sum_acc
    
    print("\nNovos pesos sugeridos (proporcionais à acurácia do torneio):")
    print(f"  - Peso Opta: {new_w_opta:.2%}")
    print(f"  - Peso Sofascore: {new_w_sofa:.2%}")
    print(f"  - Peso Odds: {new_w_odds:.2%}")
    
    settings = load_settings()
    settings["weight_opta"] = new_w_opta
    settings["weight_sofascore"] = new_w_sofa
    settings["weight_odds"] = new_w_odds
    save_settings(settings)

# Print Qualitative Markdown Report
def print_markdown_report(date_str=None):
    settings = load_settings()
    existing_scores = read_csv_scores()
    
    print("\n# 🏆 COPA DO MUNDO 2026 - CENTRO DE PREVISÕES TÁTICAS")
    print(f"**Data local:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  ")
    print(f"**Pesos do Modelo:** Opta ({settings.get('weight_opta'):.0%}) | Sofascore ({settings.get('weight_sofascore'):.0%}) | Odds ({settings.get('weight_odds'):.0%})")
    print()
    print("---")
    
    # ------------------ SEÇÃO DE REGISTRO DE ANDAMENTO ------------------
    finished_count = 0
    correct_outcome_count = 0
    correct_exact_score_count = 0
    total_brier_score = 0.0
    
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "FINISHED" and row.get("home_score") != "" and row.get("away_score") != "":
                    try:
                        home_actual = int(row["home_score"])
                        away_actual = int(row["away_score"])
                        actual_outcome = "HOME" if home_actual > away_actual else ("AWAY" if home_actual < away_actual else "DRAW")
                        
                        try:
                            prob_h = float(row["consensus_home"])
                            prob_d = float(row["consensus_draw"])
                            prob_a = float(row["consensus_away"])
                        except (ValueError, KeyError, TypeError, ValueError):
                            # Fallback: compute prediction from matches JSON
                            m_id = row.get("match_id")
                            match = next((m for m in WORLD_CUP_MATCHES if m["id"] == m_id), None)
                            if match:
                                pred = compute_predictions(match, settings)
                                prob_h, prob_d, prob_a = pred["consensus"]
                            else:
                                continue
                                
                        finished_count += 1
                        
                        # Outcome prediction
                        if prob_h > prob_d and prob_h > prob_a:
                            pred_outcome = "HOME"
                        elif prob_a > prob_h and prob_a > prob_d:
                            pred_outcome = "AWAY"
                        else:
                            pred_outcome = "DRAW"
                            
                        if pred_outcome == actual_outcome:
                            correct_outcome_count += 1
                            
                        # Exact score — only the #1 most probable prediction
                        s_score_col = row.get("suggested_score", "")
                        first_part = s_score_col.split(",")[0].strip()
                        if " (" in first_part:
                            first_score_str = first_part.split(" (")[0]
                            if "x" in first_score_str:
                                try:
                                    h_g, a_g = map(int, first_score_str.split("x"))
                                    if (home_actual, away_actual) == (h_g, a_g):
                                        correct_exact_score_count += 1
                                except ValueError:
                                    pass
                            
                        # Brier score
                        total_brier_score += get_brier_score(prob_h, prob_d, prob_a, actual_outcome)
                    except Exception as e:
                        print(f"Erro ao processar linha do CSV para métricas: {e}")
            
    print("\n### 📈 METRÍCAS DE DESEMPENHO DO MODELO (REGISTRO DE ANDAMENTO)\n")
    if finished_count > 0:
        outcome_acc = (correct_outcome_count / finished_count) * 100
        exact_acc = (correct_exact_score_count / finished_count) * 100
        avg_brier = total_brier_score / finished_count
        quality = "Excelente" if avg_brier < 0.35 else ("Bom" if avg_brier < 0.50 else "Regular")
        
        print(f"* **Total de Partidas Finalizadas:** {finished_count}")
        print(f"* **Acurácia de Vencedor/Empate (Resultado H/D/A):** {correct_outcome_count}/{finished_count} ({outcome_acc:.1f}%)")
        print(f"* **Acurácia de Placar Exato (1ª Opção):** {correct_exact_score_count}/{finished_count} ({exact_acc:.1f}%)")
        print(f"* **Erro Médio Quadrático (Brier Score do Modelo):** {avg_brier:.4f} ({quality})")
    else:
        print("* Nenhuma partida finalizada registrada ainda. O modelo começará a rastrear a acurácia assim que os primeiros resultados forem inseridos.")
    print("\n---")
    # ---------------------------------------------------------------------
    
    today_str = date_str if date_str else datetime.now().strftime("%Y-%m-%d")
    printed_count = 0
    
    for i, match in enumerate(WORLD_CUP_MATCHES):
        match_date_str = match["date"].split(" ")[0]
        if match_date_str != today_str:
            continue
            
        printed_count += 1
        m_id = match["id"]
        pred = compute_predictions(match, settings)
        consensus = pred["consensus"]
        
        # Check if match has finished score
        score_text = ""
        if m_id in existing_scores:
            score_text = f" (Resultado Real: {existing_scores[m_id]['home']}x{existing_scores[m_id]['away']})"
            
        home_emoji = match.get("home_emoji", "")
        away_emoji = match.get("away_emoji", "")
        
        # Extract time from date string (format "2026-06-15 15:00")
        dt = datetime.strptime(match["date"], "%Y-%m-%d %H:%M")
        time_str = dt.strftime("%H:%M")
        
        print(f"\n### {printed_count}. {home_emoji} {match['home_team']} vs. {away_emoji} {match['away_team']}{score_text}\n")
        print(f"* **Grupo:** {match['stage']} | **Horário:** {time_str} (Brasília)")
        print(f"* **Local:** {match['venue']} - {match.get('weather', '')}")
        
        prob_h = consensus[0] * 100
        prob_d = consensus[1] * 100
        prob_a = consensus[2] * 100
        print(f"* **Probabilidades Consolidadas (H/D/A):** {prob_h:.1f}% ({match['home_team']}) / {prob_d:.1f}% (Empate) / {prob_a:.1f}% ({match['away_team']})")
        print(f"* **Odds Médias (H/D/A):** {match['odds']['home']:.2f} / {match['odds']['draw']:.2f} / {match['odds']['away']:.2f}")
        print()
        print("**📋 Análise Tática e Contextual**")
        print()
        print(f"* **O Confronto Tático:** {match['tactical_analysis']}")
        print(f"* **Notícias & Fatores Físicos:** {match['key_factors']}")
        print(f"* **O que dizem os Profissionais:** {match.get('pro_opinion', '')}")
        print()
        print("**🎯 Palpites para o seu Bolão**")
        print()
        
        print("* **O Palpite Matemático (Top 3 Maiores):**")
        print("")
        for idx, sp in enumerate(pred["top_scores"]):
            home_goals, away_goals = sp[0]
            prob = sp[1]
            opt_mark = " 🎯" if (home_goals == pred["suggested"][0] and away_goals == pred["suggested"][1]) else ""
            print(f"* {home_goals}x{away_goals} - Probabilidade: {prob*100:.1f}%{opt_mark}")
        print(f"* **O Palpite da Resenha (Para se destacar):** {match.get('cheeky_prediction', '')}")
        print("\n" + "-" * 85)
        
    if printed_count == 0:
        print(f"\n* Nenhuma partida da Copa do Mundo programada para a data de hoje ({datetime.now().strftime('%d/%m/%Y')}).")



def print_history_report():
    settings = load_settings()
    existing_scores = read_csv_scores()
    
    print("\n# 📊 RELATÓRIO HISTÓRICO DE DESEMPENHO DO MODELO")
    print(f"**Data local:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  ")
    print()
    print("| ID | Data | Partida | Placar Real | Palpite 🎯 (1ª Opção) | Outras Opções (Top 3) | Acertou Vencedor/Empate? | Acertou Placar Exato? |")
    print("| :--- | :--- | :--- | :---: | :---: | :--- | :---: | :--- |")
    
    finished_count = 0
    correct_outcome_count = 0
    correct_exact_score_count = 0
    correct_exact_first_count = 0
    
    # Sort matches chronologically by date
    sorted_matches = sorted(WORLD_CUP_MATCHES, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"))
    
    for match in sorted_matches:
        m_id = match["id"]
        if m_id in existing_scores and existing_scores[m_id]["status"] == "FINISHED":
            finished_count += 1
            home_actual = existing_scores[m_id]["home"]
            away_actual = existing_scores[m_id]["away"]
            actual_score = f"{home_actual}x{away_actual}"
            actual_outcome = "HOME" if home_actual > away_actual else ("AWAY" if home_actual < away_actual else "DRAW")
            
            # Predict
            pred = compute_predictions(match, settings)
            prob_h, prob_d, prob_a = pred["consensus"]
            
            # Predicted outcome
            if prob_h > prob_d and prob_h > prob_a:
                pred_outcome = "HOME"
            elif prob_a > prob_h and prob_a > prob_d:
                pred_outcome = "AWAY"
            else:
                pred_outcome = "DRAW"
                
            outcome_correct = "SIM" if pred_outcome == actual_outcome else "NÃO"
            if pred_outcome == actual_outcome:
                correct_outcome_count += 1
                
            # Score suggestions
            top_scores = pred["top_scores"]
            first_score = f"{top_scores[0][0][0]}x{top_scores[0][0][1]}"
            first_prob = top_scores[0][1]
            
            top_scores_list = [f"{s[0][0]}x{s[0][1]}" for s in top_scores]
            
            exact_correct = "NÃO"
            if actual_score == first_score:
                exact_correct = "✓ SIM"
                correct_exact_first_count += 1
                correct_exact_score_count += 1
                
            # Date formatting (input format: "2026-06-11 13:00")
            dt = datetime.strptime(match["date"], "%Y-%m-%d %H:%M")
            date_str = dt.strftime("%d/%m")
            
            other_options_str = ", ".join([f"{s[0][0]}x{s[0][1]} ({s[1]*100:.1f}%)" for s in top_scores])
            
            home_emoji = match.get("home_emoji", "")
            away_emoji = match.get("away_emoji", "")
            
            print(f"| **{m_id}** | {date_str} | {home_emoji} {match['home_team']} vs. {away_emoji} {match['away_team']} | **{actual_score}** | {first_score} ({first_prob*100:.1f}%) | {other_options_str} | **{outcome_correct}** | **{exact_correct}** |")
            
    print("\n### 📈 MÉTRICAS ACUMULADAS:")
    if finished_count > 0:
        outcome_acc = (correct_outcome_count / finished_count) * 100
        exact_top3_acc = (correct_exact_score_count / finished_count) * 100
        exact_first_acc = (correct_exact_first_count / finished_count) * 100
        print(f"* **Total de Partidas Finalizadas:** {finished_count}")
        print(f"* **Acurácia de Vencedor/Empate (Resultado H/D/A):** {correct_outcome_count}/{finished_count} ({outcome_acc:.1f}%)")
        print(f"* **Acurácia de Placar Exato (1ª Opção):** {correct_exact_first_count}/{finished_count} ({exact_first_acc:.1f}%)")
    else:
        print("* Nenhuma partida finalizada registrada ainda.")

def print_bolao_report():
    settings = load_settings()
    existing_scores = read_csv_scores()
    
    print("\n# 🏆 PONTUAÇÃO DO MODELO NO BOLÃO")
    print(f"**Data local:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  ")
    print()
    print("| ID | Partida | Palpite 🎯 | Placar Real | Resultado (+2) | Placar Exato (+5) | Bônus Gols (+1) | Pontos Obtidos |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    
    total_matches_pts = 0
    finished_count = 0
    
    # Sort chronologically by date
    sorted_matches = sorted(WORLD_CUP_MATCHES, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M"))
    
    for match in sorted_matches:
        m_id = match["id"]
        if m_id in existing_scores and existing_scores[m_id]["status"] == "FINISHED":
            finished_count += 1
            home_actual = existing_scores[m_id]["home"]
            away_actual = existing_scores[m_id]["away"]
            actual_score = f"{home_actual}x{away_actual}"
            
            # Predict
            pred = compute_predictions(match, settings)
            gh, ga = pred["suggested"] # Optimal guess 🎯
            
            pred_outcome = "HOME" if gh > ga else ("AWAY" if gh < ga else "DRAW")
            actual_outcome = "HOME" if home_actual > away_actual else ("AWAY" if home_actual < away_actual else "DRAW")
            
            # Rule 1: Acertar o resultado (Vitória ou Empate) -> +2 pts
            pts_outcome = 0
            if pred_outcome == actual_outcome:
                pts_outcome = 2
                
            # Rule 2: Placar exato -> +5 pts (does not sum with outcome)
            pts_exact = 0
            if gh == home_actual and ga == away_actual:
                pts_exact = 5
                
            # Rule 3: Bônus por gols de um time -> +1 pt (só se acertar o vencedor e não for placar exato)
            pts_bonus = 0
            if pts_outcome == 2 and pts_exact == 0:
                match_home = (gh == home_actual)
                match_away = (ga == away_actual)
                if match_home or match_away:
                    pts_bonus = 1
                    
            # Total points for this match
            if pts_exact == 5:
                game_total = 5
            else:
                game_total = pts_outcome + pts_bonus
                
            total_matches_pts += game_total
            
            home_emoji = match.get("home_emoji", "")
            away_emoji = match.get("away_emoji", "")
            
            txt_outcome = "+2" if pts_outcome == 2 and pts_exact == 0 else ("-" if pts_exact == 5 else "0")
            txt_exact = "+5" if pts_exact == 5 else "0"
            txt_bonus = "+1" if pts_bonus == 1 else "0"
            
            print(f"| **{m_id}** | {home_emoji} {match['home_team']} vs. {match['away_team']} {away_emoji} | {gh}x{ga} | **{actual_score}** | {txt_outcome} | {txt_exact} | {txt_bonus} | **{game_total} pts** |")
            
    print("\n### 🏅 OUTROS PALPITES (PONTOS DE LONGO PRAZO):")
    # Read guesses and status from settings
    champ = settings.get("predicted_champion", "França")
    champ_pts = settings.get("points_champion", 0)
    champ_resolved = settings.get("resolved_champion", False)
    champ_status = "Em andamento" if not champ_resolved else ("✓ Acertou (+10 pts)" if champ_pts > 0 else "✗ Errou (0 pts)")
    
    scorer = settings.get("predicted_top_scorer", "Kylian Mbappé")
    scorer_pts = settings.get("points_top_scorer", 0)
    scorer_resolved = settings.get("resolved_top_scorer", False)
    scorer_status = "Em andamento" if not scorer_resolved else ("✓ Acertou (+8 pts)" if scorer_pts > 0 else "✗ Errou (0 pts)")
    
    print(f"* **Palpite de Campeão:** {champ} — Status: *{champ_status}* | **{champ_pts} pts**")
    print(f"* **Palpite de Artilheiro:** {scorer} — Status: *{scorer_status}* | **{scorer_pts} pts**")
    
    total_pts = total_matches_pts + int(champ_pts) + int(scorer_pts)
    print(f"\n# 🏆 PONTUAÇÃO TOTAL ACUMULADA: **{total_pts} pontos**")

def fetch_scorepick_data():
    settings = load_settings()
    email = settings.get("scorepick_email", "")
    password = settings.get("scorepick_password", "")
    pool_id = settings.get("scorepick_pool_id", "")
    
    if not email or not password or not pool_id:
        print("Erro: Credenciais do ScorePick não encontradas no settings.json.")
        sys.exit(1)
        
    client = ScorePickClient(email, password)
    if not client.login():
        print("Erro ao autenticar no ScorePick.")
        sys.exit(1)
        
    print("Buscando jogos e palpites do ScorePick...")
    sp_matches_raw = client.get_matches("WC")
    sp_bets = client.get_bets(pool_id)
    
    sp_matches = []
    print("Buscando detalhes e probabilidades de cada jogo...")
    for idx, sm in enumerate(sp_matches_raw):
        if sm["status"] == "scheduled":
            print(f"  [{idx+1}/{len(sp_matches_raw)}] Detalhes de {sm['home_team']['name']} vs {sm['away_team']['name']}...")
            detail = client.get_match_detail(sm["id"])
            if detail:
                sp_matches.append(detail)
            else:
                sp_matches.append(sm)
        else:
            sp_matches.append(sm)
            
    client.close()
    
    print(f"Retornados {len(sp_matches)} jogos e {len(sp_bets)} palpites da API.")
    
    # Map SP matches to local matches, updating scores & status
    local_matches = load_world_cup_matches()
    
    # Mapping helper
    def map_team_name(name):
        mapping = {
            "Spain": "Espanha",
            "Cape Verde Islands": "Cabo Verde",
            "Cape Verde": "Cabo Verde",
            "Belgium": "Bélgica",
            "Egypt": "Egito",
            "Saudi Arabia": "Arábia Saudita",
            "Uruguay": "Uruguai",
            "Iran": "Irã",
            "New Zealand": "Nova Zelândia",
            "France": "França",
            "Senegal": "Senegal",
            "Iraq": "Iraque",
            "Norway": "Noruega",
            "Argentina": "Argentina",
            "Algeria": "Algélia",
            "Austria": "Áustria",
            "Jordan": "Jordânia",
            "Portugal": "Portugal",
            "Congo DR": "RD Congo",
            "England": "Inglaterra",
            "Croatia": "Croácia",
            "Mexico": "México",
            "South Africa": "África do Sul",
            "South Korea": "Coreia do Sul",
            "Czechia": "República Tcheca",
            "Czech Republic": "República Tcheca",
            "Canada": "Canadá",
            "Bosnia-Herzegovina": "Bósnia-Herzegovina",
            "Bosnia and Herzegovina": "Bósnia-Herzegovina",
            "United States": "Estados Unidos",
            "Paraguay": "Paraguai",
            "Qatar": "Catar",
            "Switzerland": "Suíça",
            "Brazil": "Brasil",
            "Morocco": "Marrocos",
            "Scotland": "Escócia",
            "Haiti": "Haiti",
            "Australia": "Austrália",
            "Turkey": "Turquia",
            "Germany": "Alemanha",
            "Curaçao": "Curaçao",
            "Netherlands": "Holanda",
            "Japan": "Japão",
            "Ivory Coast": "Costa do Marfim",
            "Ecuador": "Equador",
            "Sweden": "Suécia",
            "Tunisia": "Tunísia",
            "Ghana": "Gana",
            "Panama": "Panamá",
            "Uzbekistan": "Uzbequistão",
            "Colombia": "Colômbia"
        }
        return mapping.get(name, name)
        
    updated_count = 0
    added_count = 0
    
    new_local_matches = []
    matched_sp_ids = set()
    
    # First: attempt to match with existing local matches
    for lm in local_matches:
        lm_home = lm["home_team"]
        lm_away = lm["away_team"]
        lm_date = lm["date"].split(" ")[0]
        
        sp_match = None
        for sm in sp_matches:
            sm_home = map_team_name(sm["home_team"]["name"])
            sm_away = map_team_name(sm["away_team"]["name"])
            sm_date = sm["kickoff_at"].split("T")[0]
            
            try:
                date_diff = abs((datetime.strptime(lm_date, "%Y-%m-%d") - datetime.strptime(sm_date, "%Y-%m-%d")).days)
            except Exception:
                date_diff = 999
                
            teams_match = (lm_home == sm_home and lm_away == sm_away) or (lm_home == sm_away and lm_away == sm_home)
            
            if teams_match and date_diff <= 1:
                sp_match = sm
                break
                
        if sp_match:
            matched_sp_ids.add(sp_match["id"])
            lm["status"] = sp_match["status"].upper()
            if sp_match["status"] == "finished" and sp_match["home_score"] is not None:
                lm["home_score"] = int(sp_match["home_score"])
                lm["away_score"] = int(sp_match["away_score"])
                if map_team_name(sp_match["home_team"]["name"]) == lm["away_team"]:
                    lm["home_score"], lm["away_score"] = lm["away_score"], lm["home_score"]
            if "external_ids" not in lm:
                lm["external_ids"] = {}
            lm["external_ids"]["scorepick"] = sp_match["id"]
            updated_count += 1
            new_local_matches.append(lm)
        else:
            new_local_matches.append(lm)
            
    # Second: add new matches from ScorePick that don't exist locally
    for sm in sp_matches:
        if sm["id"] in matched_sp_ids:
            continue
            
        dt_str = sm["kickoff_at"].split(".")[0]
        if "-" in dt_str[10:]:
            dt_str = dt_str.split("-")[0]
        if "+" in dt_str[10:]:
            dt_str = dt_str.split("+")[0]
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            formatted_date = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            formatted_date = sm["kickoff_at"].replace("T", " ")[:16]
            
        home = map_team_name(sm["home_team"]["name"])
        away = map_team_name(sm["away_team"]["name"])
        
        pred = sm.get("prediction") or {}
        home_pct = float(pred.get("home_pct", 33.3))
        draw_pct = float(pred.get("draw_pct", 33.3))
        away_pct = float(pred.get("away_pct", 33.4))
        
        h_prob = home_pct / 100.0
        d_prob = draw_pct / 100.0
        a_prob = away_pct / 100.0
        
        s = h_prob + d_prob + a_prob
        if s > 0:
            h_prob /= s
            d_prob /= s
            a_prob /= s
        else:
            h_prob, d_prob, a_prob = 0.40, 0.30, 0.30
        
        new_match = {
            "id": f"SP-{sm['id']}",
            "date": formatted_date,
            "home_team": home,
            "away_team": away,
            "home_emoji": "",
            "away_emoji": "",
            "stage": sm["round"],
            "venue": sm["venue"]["name"] if sm.get("venue") else "",
            "weather": "",
            "status": sm["status"].upper(),
            "prob_opta": {"home": h_prob, "draw": d_prob, "away": a_prob},
            "prob_sofascore": {"home": h_prob, "draw": d_prob, "away": a_prob},
            "odds": {"home": round(1.0/max(0.01, h_prob), 2), "draw": round(1.0/max(0.01, d_prob), 2), "away": round(1.0/max(0.01, a_prob), 2)},
            "tactical_analysis": f"Previsão baseada nas probabilidades oficiais da ScorePick ({home_pct:.0f}% / {draw_pct:.0f}% / {away_pct:.0f}%).",
            "key_factors": "Análise estatística baseada em probabilidades consolidadas.",
            "pro_opinion": "",
            "cheeky_prediction": "",
            "external_ids": {"scorepick": sm["id"]}
        }
        
        if sm["status"] == "finished" and sm["home_score"] is not None:
            new_match["home_score"] = int(sm["home_score"])
            new_match["away_score"] = int(sm["away_score"])
            
        new_local_matches.append(new_match)
        added_count += 1
        
    with open(MATCHES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(new_local_matches, f, indent=2, ensure_ascii=False)
        
    print(f"Sincronização concluída! {updated_count} jogos locais atualizados, {added_count} novos jogos adicionados.")
    
    global WORLD_CUP_MATCHES
    WORLD_CUP_MATCHES = new_local_matches
    
    scores_dict = {}
    for m in WORLD_CUP_MATCHES:
        if m.get("status") == "FINISHED" and m.get("home_score") is not None:
            scores_dict[m["id"]] = {
                "home": m["home_score"],
                "away": m["away_score"],
                "status": "FINISHED"
            }
    update_csv_with_scores(scores_dict, settings)

def submit_scorepick_bets():
    settings = load_settings()
    email = settings.get("scorepick_email", "")
    password = settings.get("scorepick_password", "")
    pool_id = settings.get("scorepick_pool_id", "")
    
    if not email or not password or not pool_id:
        print("Erro: Credenciais do ScorePick não encontradas no settings.json.")
        sys.exit(1)
        
    fetch_scorepick_data()
    
    client = ScorePickClient(email, password)
    if not client.login():
        print("Erro ao autenticar no ScorePick.")
        sys.exit(1)
        
    sp_bets = client.get_bets(pool_id)
    bets_by_match = {b["match"]: b for b in sp_bets}
    
    sub_count = 0
    skip_count = 0
    error_count = 0
    
    print("\nCalculando palpites ideais baseados na calibração de gols e novas regras do bolão...")
    for match in WORLD_CUP_MATCHES:
        sp_id = match.get("external_ids", {}).get("scorepick")
        if not sp_id:
            continue
            
        status = match["status"]
        if status == "FINISHED":
            continue
            
        existing_bet = bets_by_match.get(sp_id)
        if existing_bet and existing_bet.get("is_locked"):
            continue
            
        pred = compute_predictions(match, settings)
        suggested = pred["suggested"]
        
        if existing_bet:
            ex_h = existing_bet.get("home_score")
            ex_a = existing_bet.get("away_score")
            if ex_h == suggested[0] and ex_a == suggested[1]:
                skip_count += 1
                continue
                
        print(f"Enviando palpite para {match['home_team']} vs {match['away_team']}: {suggested[0]}x{suggested[1]}...")
        success, res = client.submit_bet(pool_id, sp_id, suggested[0], suggested[1])
        if success:
            sub_count += 1
        else:
            print(f"Erro ao enviar palpite para o jogo {sp_id}: {res}")
            error_count += 1
            
    client.close()
    print(f"\nSubmissão concluída! Enviados: {sub_count} | Pulados: {skip_count} | Erros: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="World Cup 2026 Prediction Manager")
    parser.add_argument("--report", action="store_true", help="Print qualitative match report")
    parser.add_argument("--date", type=str, default=None, help="Filter report for specific date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--history", action="store_true", help="Print quantitative history performance report")
    parser.add_argument("--bolao", action="store_true", help="Print model points according to bolao rules")
    parser.add_argument("--tune", action="store_true", help="Run backtesting and optimize consensus weights")
    parser.add_argument("--result", nargs=3, metavar=("MATCH_ID", "HOME_SCORE", "AWAY_SCORE"), help="Record a finished match score")
    parser.add_argument("--fetch-sp", action="store_true", help="Fetch matches and bets from ScorePick and merge with local database")
    parser.add_argument("--submit-sp", action="store_true", help="Submit optimal guesses to ScorePick pool")
    
    args = parser.parse_args()
    
    if args.fetch_sp:
        fetch_scorepick_data()
        sys.exit(0)
        
    if args.submit_sp:
        submit_scorepick_bets()
        sys.exit(0)
        
    # If run without arguments, default to updating CSV and printing report
    if not any(v for k, v in vars(args).items() if k != "date"):
        update_csv()
        print_markdown_report(date_str=args.date)
        sys.exit(0)
        
    if args.result:
        m_id, h_score, a_score = args.result
        
        # Check if match_id exists in our predefined list
        if not any(m["id"] == m_id for m in WORLD_CUP_MATCHES):
            print(f"Erro: Match ID '{m_id}' não encontrado nos jogos predefinidos.")
            sys.exit(1)
            
        try:
            h_score_int = int(h_score)
            a_score_int = int(a_score)
        except ValueError:
            print("Erro: Placar deve conter números inteiros válidos.")
            sys.exit(1)
            
        # 1. Carrega os resultados existentes e insere o novo resultado
        scores = read_csv_scores()
        scores[m_id] = {"home": h_score_int, "away": a_score_int, "status": "FINISHED"}
        
        # Carrega pesos antigos para comparação
        old_settings = load_settings()
        old_weights = {
            "opta": old_settings.get("weight_opta", 0.33),
            "sofascore": old_settings.get("weight_sofascore", 0.33),
            "odds": old_settings.get("weight_odds", 0.34)
        }
        
        # 2. Salva temporariamente no CSV para que a calibração de pesos consiga ler o jogo como finalizado
        if not update_csv_with_scores(scores, old_settings):
            print("Erro ao atualizar base de dados com o novo resultado.")
            sys.exit(1)
            
        print(f"✔ Sucesso: Resultado registrado para o jogo '{m_id}': {h_score_int}x{a_score_int}.")
        
        # 3. Executa a calibração automática dos pesos
        print("\n--- Executando Recalibração de Pesos Automatizada ---")
        tune_weights()
        
        # 4. Carrega os novos pesos e atualiza o CSV final com as previsões atualizadas
        new_settings = load_settings()
        update_csv_with_scores(scores, new_settings)
        
        print(f"\n✔ Pesos atualizados no settings.json:")
        print(f"  - Peso Opta:      {old_weights['opta']:.0%} -> {new_settings.get('weight_opta'):.0%}")
        print(f"  - Peso Sofascore: {old_weights['sofascore']:.0%} -> {new_settings.get('weight_sofascore'):.0%}")
        print(f"  - Peso Odds:      {old_weights['odds']:.0%} -> {new_settings.get('weight_odds'):.0%}")
        print("✔ Todas as previsões futuras foram recalculadas com os novos pesos e atualizadas no CSV!")
        
    if args.tune and not args.result:
        tune_weights()
        # Se tune_weights atualizou os pesos, vamos atualizar o CSV de previsões também
        update_csv()
        
    if args.report:
        print_markdown_report(date_str=args.date)
        
    if args.history:
        print_history_report()
        
    if args.bolao:
        print_bolao_report()


