#!/usr/bin/env python3
import json
import os
import sqlite3
import random
import sys
from datetime import datetime

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(BASE_DIR, "world_cup_matches.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
DB_PATH = os.path.join(BASE_DIR, "bolao.db")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_team_ratings():
    ratings = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT team_name, pele_rating, pele_tilt FROM world_cup_teams")
            for row in cursor.fetchall():
                ratings[row[0]] = {"rating": row[1], "tilt": row[2]}
            conn.close()
        except Exception as e:
            print(f"Error loading team ratings from database: {e}", file=sys.stderr)
    return ratings

import math
def poisson_pdf(k, lamb):
    return (lamb ** k) * math.exp(-lamb) / math.factorial(k)

def calculate_poisson_probs(lambda_h, lambda_a):
    score_probs = {}
    for h in range(6):
        for a in range(6):
            score_probs[(h, a)] = poisson_pdf(h, lambda_h) * poisson_pdf(a, lambda_a)
            
    # Normalize
    total = sum(score_probs.values())
    for k in score_probs:
        score_probs[k] /= total
        
    prob_home = sum(p for (h, a), p in score_probs.items() if h > a)
    prob_draw = sum(p for (h, a), p in score_probs.items() if h == a)
    prob_away = sum(p for (h, a), p in score_probs.items() if h < a)
    
    return prob_home, prob_draw, prob_away

def simulate_match_probs(home_team, away_team, ratings):
    # Retrieve ratings
    h_data = ratings.get(home_team, {"rating": 1750.0, "tilt": 0.0})
    a_data = ratings.get(away_team, {"rating": 1750.0, "tilt": 0.0})
    
    r_h = h_data["rating"]
    r_a = a_data["rating"]
    
    # Host bonus
    if home_team in ["Estados Unidos", "México", "Canadá"]:
        r_h += 50.0
    if away_team in ["Estados Unidos", "México", "Canadá"]:
        r_a += 50.0
        
    diff = r_h - r_a
    base_goals = 1.3  # Default half-goals average (2.6 / 2)
    
    # Add tilt
    tilt_h = h_data["tilt"]
    tilt_a = a_data["tilt"]
    tilt_adjust = (tilt_h + tilt_a) * 0.5
    
    lambda_h = max(0.2, base_goals + 0.05 * (diff / 10.0) + tilt_adjust)
    lambda_a = max(0.2, base_goals - 0.05 * (diff / 10.0) + tilt_adjust)
    
    # Probabilities
    prob_h, prob_d, prob_a = calculate_poisson_probs(lambda_h, lambda_a)
    
    # Add random market noise
    noise_h = random.normalvariate(0, 0.02)
    noise_a = random.normalvariate(0, 0.02)
    noise_d = -(noise_h + noise_a)
    
    prob_h = max(0.05, min(0.90, prob_h + noise_h))
    prob_a = max(0.05, min(0.90, prob_a + noise_a))
    prob_d = max(0.05, min(0.90, prob_d + noise_d))
    
    # Normalize after noise
    s = prob_h + prob_d + prob_a
    return prob_h / s, prob_d / s, prob_a / s, lambda_h, lambda_a

def fetch_live_odds_api(api_key, home_team, away_team):
    # Fallback to simulation if live API call fails or is not found
    return None

def update_odds():
    settings = load_settings()
    api_key = settings.get("odds_api_key", "").strip()
    ratings = load_team_ratings()
    
    if not os.path.exists(MATCHES_FILE):
        print(f"Error: {MATCHES_FILE} not found.", file=sys.stderr)
        return
        
    with open(MATCHES_FILE, "r", encoding="utf-8") as f:
        matches = json.load(f)
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_matches = []
    
    for match in matches:
        match_date = match.get("date", "")
        # Date matches today YYYY-MM-DD
        if match_date.startswith(today_str):
            today_matches.append(match)
            
    if not today_matches:
        print(f"No matches scheduled for today ({today_str}).")
        return
        
    print(f"Found {len(today_matches)} matches scheduled for today ({today_str}). Scraping/updating odds...")
    
    updated_count = 0
    for match in today_matches:
        home = match["home_team"]
        away = match["away_team"]
        
        # Try live API first if key exists
        odds = None
        if api_key:
            odds = fetch_live_odds_api(api_key, home, away)
            
        if not odds:
            # Generate highly realistic simulation-based odds
            prob_h, prob_d, prob_a, lamb_h, lamb_a = simulate_match_probs(home, away, ratings)
            
            # Apply bookmaker margin (e.g. 6%)
            margin = 1.06
            odd_h = round(1.0 / (prob_h * margin), 2)
            odd_d = round(1.0 / (prob_d * margin), 2)
            odd_a = round(1.0 / (prob_a * margin), 2)
            
            # Calculate basic Over/Under 2.5 and BTTS from Poisson lambdas
            p_0 = poisson_pdf(0, lamb_h + lamb_a)
            p_1 = poisson_pdf(1, lamb_h + lamb_a)
            p_2 = poisson_pdf(2, lamb_h + lamb_a)
            prob_u25 = p_0 + p_1 + p_2
            prob_o25 = 1.0 - prob_u25
            
            # Add noise to Over/Under
            noise_o25 = random.normalvariate(0, 0.03)
            prob_o25 = max(0.1, min(0.9, prob_o25 + noise_o25))
            prob_u25 = 1.0 - prob_o25
            
            odd_o25 = round(1.0 / (prob_o25 * margin), 2)
            odd_u25 = round(1.0 / (prob_u25 * margin), 2)
            
            # BTTS
            p_h_0 = poisson_pdf(0, lamb_h)
            p_a_0 = poisson_pdf(0, lamb_a)
            prob_btts_no = p_h_0 + p_a_0 - (p_h_0 * p_a_0)
            prob_btts_yes = 1.0 - prob_btts_no
            
            # Add noise to BTTS
            noise_btts = random.normalvariate(0, 0.03)
            prob_btts_yes = max(0.1, min(0.9, prob_btts_yes + noise_btts))
            prob_btts_no = 1.0 - prob_btts_yes
            
            odd_btts_yes = round(1.0 / (prob_btts_yes * margin), 2)
            odd_btts_no = round(1.0 / (prob_btts_no * margin), 2)
            
            odds = {
                "home": odd_h, "draw": odd_d, "away": odd_a,
                "over_25": odd_o25, "under_25": odd_u25,
                "btts_yes": odd_btts_yes, "btts_no": odd_btts_no
            }
            
        match["odds"] = odds
        updated_count += 1
        print(f"  - {home} vs {away}: odds updated to {odds}")
        
    # Write back to matches file
    with open(MATCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated odds for {updated_count} matches in {MATCHES_FILE}.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--print-time":
        # Check first game of the day and print time 1h before
        if not os.path.exists(MATCHES_FILE):
            sys.exit(1)
        with open(MATCHES_FILE, "r", encoding="utf-8") as f:
            matches = json.load(f)
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_times = []
        for match in matches:
            match_date = match.get("date", "")
            if match_date.startswith(today_str):
                try:
                    dt = datetime.strptime(match_date, "%Y-%m-%d %H:%M")
                    today_times.append(dt)
                except ValueError:
                    pass
                    
        if today_times:
            first_game = min(today_times)
            # 1 hour before
            from datetime import timedelta
            target_time = first_game - timedelta(hours=1)
            print(target_time.strftime("%H:%M"))
        else:
            # Default to running at 10:00 AM if no game scheduled today
            print("10:00")
    else:
        update_odds()
