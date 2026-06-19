import os
import sqlite3
import csv
import json
import argparse
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import urllib.parse
import re

DB_PATH = "/home/rafa/Projects/bolao/bolao.db"
CSV_PATH = "/home/rafa/Projects/bolao/world_cup_teams_metrics.csv"
MATCHES_JSON_PATH = "/home/rafa/Projects/bolao/world_cup_matches.json"

# Sentiment keywords in Portuguese
POSITIVE_KEYWORDS = [
    "surpreendeu", "surpresa", "brilhou", "goleou", "goleada", "otimo", "ótimo", 
    "excelente", "historica", "histórica", "destaque", "espetaculo", "espetáculo", 
    "sensacao", "sensação", "dominou", "venceu bem", "show", "impecavel", "impecável"
]

NEGATIVE_KEYWORDS = [
    "vexame", "decepcao", "decepção", "decepcionou", "crise", "vergonha", "fracasso", 
    "derrotado", "pessimo", "péssimo", "pobre", "fragil", "frágil", "apatico", "apático", 
    "eliminado", "sofreu", "falhou", "decepcionante", "vergonhoso"
]

def get_match_round(match_date_str):
    """
    Map World Cup match dates in June 2026 to Rodada 1, 2, or 3.
    """
    try:
        # Expected format: "2026-06-11 13:00"
        date_part = match_date_str.split(" ")[0]
        dt = datetime.strptime(date_part, "%Y-%m-%d")
        if dt.day <= 17:
            return "Rodada 1"
        elif dt.day <= 23:
            return "Rodada 2"
        else:
            return "Rodada 3"
    except Exception:
        return "Rodada 1"

def get_previous_round_data(team_name, current_round):
    """
    Get the team statistics (FIFA points, Pelé rating, FIFA rank) from the previous round.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT round, fifa_points, pele_rating, fifa_rank 
        FROM world_cup_team_rounds 
        WHERE team_name = ?
    """, (team_name,))
    rows = cursor.fetchall()
    conn.close()
    
    rounds_order = ["Pré-Copa", "Rodada 1", "Rodada 2", "Rodada 3"]
    if current_round in rounds_order:
        curr_idx = rounds_order.index(current_round)
        # Look backwards for the closest previous round recorded
        for prev_r in reversed(rounds_order[:curr_idx]):
            for row in rows:
                if row[0] == prev_r:
                    return {"fifa_points": row[1], "pele_rating": row[2], "fifa_rank": row[3]}
                    
    # Fallback to current global team values
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fifa_points, pele_rating, fifa_rank 
        FROM world_cup_teams 
        WHERE team_name = ?
    """, (team_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"fifa_points": row[0], "pele_rating": row[1], "fifa_rank": row[2]}
    return {"fifa_points": 1500.0, "pele_rating": 1750.0, "fifa_rank": 50}

def fetch_web_sentiment(team_name, round_name, match_desc):
    """
    Scrape DuckDuckGo search snippets for reviews of a team's performance.
    Count positive/negative terms and return score.
    """
    query = f'"{team_name}" jogo Copa do Mundo 2026 {round_name} analise'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    pos_count = 0
    neg_count = 0
    
    print(f"  -> Buscando sentimento na web para {team_name}...")
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                snippets = soup.find_all('a', class_='result__snippet')
                text_corpus = " ".join([s.get_text().lower() for s in snippets])
                
                # Count positive keywords
                for kw in POSITIVE_KEYWORDS:
                    matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', text_corpus))
                    pos_count += matches
                
                # Count negative keywords
                for kw in NEGATIVE_KEYWORDS:
                    matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', text_corpus))
                    neg_count += matches
                    
                print(f"     [Sentimento: +{pos_count} / -{neg_count}]")
    except Exception as e:
        print(f"     [Falha no scraping de sentimento: {e}. Usando neutro.]")
        
    return pos_count, neg_count

def calculate_elo_updates(p1, p2, outcome, importance=50.0, scaling=600.0):
    """
    Standard Elo formula.
    outcome: 1.0 (win), 0.5 (draw), 0.0 (loss)
    Returns: points change for team 1.
    """
    expected = 1.0 / (10 ** (-(p1 - p2) / scaling) + 1.0)
    change = importance * (outcome - expected)
    return change

def get_match_odds_probability(match, team_role):
    """
    Calculate the consensus prediction probability of winning for the team in this match.
    team_role: 'home' or 'away'
    """
    # Try to load odds and compute consensus from existing properties or default to 33%
    # We can fetch this from the CSV or matches list.
    # For now, let's use the local consensus if available, or fallback
    try:
        google = match.get("prob_google", {"home": 0.333, "draw": 0.333, "away": 0.334})
        sofascore = match.get("prob_sofascore", {"home": 0.333, "draw": 0.333, "away": 0.334})
        forebet = match.get("prob_forebet", {"home": 0.333, "draw": 0.333, "away": 0.334})
        
        avg_home = (google.get("home", 0.333) + sofascore.get("home", 0.333) + forebet.get("home", 0.333)) / 3.0
        avg_away = (google.get("away", 0.333) + sofascore.get("away", 0.333) + forebet.get("away", 0.333)) / 3.0
        
        if team_role == 'home':
            return avg_home
        return avg_away
    except Exception:
        return 0.333

def update_round(round_number):
    round_name = f"Rodada {round_number}"
    print(f"=== INICIANDO PROCESSAMENTO DA {round_name.upper()} ===")
    
    # 1. Load all teams
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT team_name, market_value_eur, top_11_value_eur, pele_tilt FROM world_cup_teams")
    teams = cursor.fetchall()
    conn.close()
    
    team_names = [t[0] for t in teams]
    team_details = {t[0]: {"market_value": t[1], "top_11_value": t[2], "tilt": t[3]} for t in teams}
    
    # 2. Get previous round metrics for all teams
    previous_stats = {}
    for team_name in team_names:
        previous_stats[team_name] = get_previous_round_data(team_name, round_name)
        
    # 3. Load all matches and filter for matches played in this round
    if not os.path.exists(MATCHES_JSON_PATH):
        print(f"Erro: Arquivo {MATCHES_JSON_PATH} não encontrado.")
        return
        
    with open(MATCHES_JSON_PATH, "r", encoding="utf-8") as f:
        matches = json.load(f)
        
    round_matches = []
    for m in matches:
        if get_match_round(m["date"]) == round_name:
            round_matches.append(m)
            
    print(f"Encontradas {len(round_matches)} partidas agendadas para esta rodada.")
    
    # Track which teams actually played and their new stats
    teams_played = set()
    updated_stats = {name: dict(stats) for name, stats in previous_stats.items()}
    qualitative_ratings = {name: "-" for name in team_names}
    
    # Process each match in this round
    for match in round_matches:
        home_team = match["home_team"]
        away_team = match["away_team"]
        
        # Check if match is finished and has a recorded score
        is_finished = match.get("status") == "FINISHED" or (match.get("home_score") is not None and match.get("away_score") is not None)
        
        if not is_finished:
            print(f"  Match {match['id']}: {home_team} vs {away_team} ainda não finalizada. Pulando.")
            continue
            
        teams_played.add(home_team)
        teams_played.add(away_team)
        
        home_score = int(match["home_score"])
        away_score = int(match["away_score"])
        match_desc = f"{home_team} {home_score} x {away_score} {away_team}"
        print(f"  Processando partida: {match_desc}")
        
        # Outcomes: 1.0 (win), 0.5 (draw), 0.0 (loss)
        home_outcome = 1.0 if home_score > away_score else (0.5 if home_score == away_score else 0.0)
        away_outcome = 1.0 - home_outcome
        
        # Get previous stats
        prev_home = previous_stats[home_team]
        prev_away = previous_stats[away_team]
        
        # 3.1 Calculate Elo Points Updates (FIFA Points using official World Cup Importance=50)
        fifa_change = calculate_elo_updates(prev_home["fifa_points"], prev_away["fifa_points"], home_outcome, importance=50.0, scaling=600.0)
        updated_stats[home_team]["fifa_points"] += fifa_change
        updated_stats[away_team]["fifa_points"] -= fifa_change
        
        # 3.2 Calculate Pelé Rating Updates (Elo K=40, scaling=400)
        pele_change = calculate_elo_updates(prev_home["pele_rating"], prev_away["pele_rating"], home_outcome, importance=40.0, scaling=400.0)
        updated_stats[home_team]["pele_rating"] += pele_change
        updated_stats[away_team]["pele_rating"] -= pele_change
        
        # 3.3 Sentiment Analysis
        home_pos, home_neg = fetch_web_sentiment(home_team, round_name, match_desc)
        away_pos, away_neg = fetch_web_sentiment(away_team, round_name, match_desc)
        
        # 3.4 Heuristic for Expectation status
        home_p_win = get_match_odds_probability(match, 'home')
        away_p_win = get_match_odds_probability(match, 'away')
        
        # Qualify Home Team
        if home_outcome == 1.0: # Win
            if home_p_win < 0.40:
                h_status = "Superou Expectativas"
            else:
                h_status = "Dentro da Expectativa"
        elif home_outcome == 0.0: # Loss
            if home_p_win > 0.55:
                h_status = "Decepção"
            else:
                h_status = "Dentro da Expectativa"
        else: # Draw
            if home_p_win > 0.60:
                h_status = "Decepção"
            elif away_p_win > 0.60:
                h_status = "Superou Expectativas"
            else:
                h_status = "Dentro da Expectativa"
                
        # Qualify Away Team
        if away_outcome == 1.0: # Win
            if away_p_win < 0.40:
                a_status = "Superou Expectativas"
            else:
                a_status = "Dentro da Expectativa"
        elif away_outcome == 0.0: # Loss
            if away_p_win > 0.55:
                a_status = "Decepção"
            else:
                a_status = "Dentro da Expectativa"
        else: # Draw
            if away_p_win > 0.60:
                a_status = "Decepção"
            elif home_p_win > 0.60:
                a_status = "Superou Expectativas"
            else:
                a_status = "Dentro da Expectativa"
                
        # Adjust with Sentiment Scraper counts
        # Home
        if h_status == "Dentro da Expectativa":
            if (home_pos - home_neg) >= 2:
                h_status = "Superou Expectativas"
            elif (home_neg - home_pos) >= 2:
                h_status = "Decepção"
        # Away
        if a_status == "Dentro da Expectativa":
            if (away_pos - away_neg) >= 2:
                a_status = "Superou Expectativas"
            elif (away_neg - away_pos) >= 2:
                a_status = "Decepção"
                
        qualitative_ratings[home_team] = h_status
        qualitative_ratings[away_team] = a_status
        
        print(f"    Home ({home_team}): FIFA (+{fifa_change:+.2f}) | Pelé ({pele_change:+.2f}) | Status: {h_status}")
        print(f"    Away ({away_team}): FIFA ({-fifa_change:+.2f}) | Pelé ({-pele_change:+.2f}) | Status: {a_status}")

    # 4. Sort and Recalculate FIFA Rankings for all 48 teams
    sorted_by_fifa = sorted(team_names, key=lambda x: updated_stats[x]["fifa_points"], reverse=True)
    for index, name in enumerate(sorted_by_fifa):
        updated_stats[name]["fifa_rank"] = index + 1
        
    # 5. Save results to the SQLite Database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Save round results and also update global team rankings in world_cup_teams
    for name in team_names:
        stats = updated_stats[name]
        qual = qualitative_ratings[name]
        
        # Save to world_cup_team_rounds
        cursor.execute("""
            INSERT OR REPLACE INTO world_cup_team_rounds (team_name, round, fifa_rank, fifa_points, pele_rating, qualitative_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, round_name, stats["fifa_rank"], stats["fifa_points"], stats["pele_rating"], qual))
        
        # Update global state in world_cup_teams
        cursor.execute("""
            UPDATE world_cup_teams 
            SET fifa_rank = ?, fifa_points = ?, pele_rating = ?
            WHERE team_name = ?
        """, (stats["fifa_rank"], stats["fifa_points"], stats["pele_rating"], name))
        
    conn.commit()
    conn.close()
    
    # 6. Regenerate CSV
    try:
        from app.database import export_team_metrics_to_csv
        if export_team_metrics_to_csv():
            print(f"✔ Rodada '{round_name}' processada e exportada para CSV com sucesso!")
        else:
            print("Warning: CSV export failed.")
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update World Cup Team Ratings and Sentiment for a Specific Round")
    parser.add_argument("--round", type=int, required=True, help="Round number (1, 2, or 3)")
    args = parser.parse_args()
    
    if args.round not in [1, 2, 3]:
        print("Erro: Apenas as rodadas 1, 2 e 3 são suportadas atualmente.")
        exit(1)
        
    update_round(args.round)
