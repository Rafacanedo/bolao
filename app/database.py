import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bolao.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Matches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        league TEXT NOT NULL,
        match_date TEXT NOT NULL,
        status TEXT DEFAULT 'SCHEDULED',
        home_score INTEGER,
        away_score INTEGER,
        external_ids TEXT
    )
    """)
    
    # Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        source TEXT NOT NULL,
        home_win_prob REAL,
        draw_prob REAL,
        away_win_prob REAL,
        home_score REAL,
        away_score REAL,
        updated_at TEXT,
        FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE,
        UNIQUE(match_id, source)
    )
    """)
    
    # Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    # Insert default weights if not present
    default_weights = {
        "weight_sofascore": "0.2",
        "weight_understat": "0.3",
        "weight_odds": "0.4",
        "weight_whoscored": "0.1",
        "weight_google": "0.0",
        "weight_forebet": "0.0",
        "odds_api_key": ""
    }
    for k, v in default_weights.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    # Create world_cup_team_rounds table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS world_cup_team_rounds (
        team_name TEXT NOT NULL,
        round TEXT NOT NULL,
        fifa_rank INTEGER,
        fifa_points REAL,
        pele_rating REAL,
        qualitative_status TEXT,
        PRIMARY KEY (team_name, round),
        FOREIGN KEY (team_name) REFERENCES world_cup_teams (team_name) ON DELETE CASCADE
    )
    """)
    
    # Verify/create top_11_value_eur column in world_cup_teams if table exists
    try:
        cursor.execute("SELECT top_11_value_eur FROM world_cup_teams LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE world_cup_teams ADD COLUMN top_11_value_eur REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass
            
    conn.commit()
    conn.close()

def get_team_metrics(round_name=None):
    """
    Query teams metrics joined with their round-by-round statistics.
    Supports filtering by specific round or fetching the current (latest) round state.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Sort order mapping helper for SQLite
    round_case = """
        CASE r.round 
            WHEN 'Pré-Copa' THEN 0 
            WHEN 'Rodada 1' THEN 1 
            WHEN 'Rodada 2' THEN 2 
            WHEN 'Rodada 3' THEN 3 
            WHEN 'Oitavas de Final' THEN 4
            WHEN 'Quartas de Final' THEN 5
            WHEN 'Semifinal' THEN 6
            WHEN 'Final' THEN 7
            ELSE 99 END
    """
    
    if round_name and round_name != "all" and round_name != "current":
        cursor.execute(f"""
            SELECT t.team_name, t.name_en, t.emoji, t.market_value_eur, t.top_11_value_eur,
                   r.round, r.fifa_rank, r.fifa_points, r.pele_rating, r.qualitative_status
            FROM world_cup_teams t
            JOIN world_cup_team_rounds r ON t.team_name = r.team_name
            WHERE r.round = ?
            ORDER BY t.market_value_eur DESC
        """, (round_name,))
    elif round_name == "current":
        # Get the latest round for each team
        cursor.execute(f"""
            SELECT t.team_name, t.name_en, t.emoji, t.market_value_eur, t.top_11_value_eur,
                   r.round, r.fifa_rank, r.fifa_points, r.pele_rating, r.qualitative_status
            FROM world_cup_teams t
            JOIN world_cup_team_rounds r ON t.team_name = r.team_name
            WHERE r.round = (
                SELECT r2.round FROM world_cup_team_rounds r2 
                WHERE r2.team_name = t.team_name 
                ORDER BY {round_case.replace("r.", "r2.")} DESC LIMIT 1
            )
            ORDER BY t.market_value_eur DESC
        """)
    else:
        # All history
        cursor.execute(f"""
            SELECT t.team_name, t.name_en, t.emoji, t.market_value_eur, t.top_11_value_eur,
                   r.round, r.fifa_rank, r.fifa_points, r.pele_rating, r.qualitative_status
            FROM world_cup_teams t
            JOIN world_cup_team_rounds r ON t.team_name = r.team_name
            ORDER BY {round_case} ASC, t.market_value_eur DESC
        """)
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def export_team_metrics_to_csv():
    """
    Exports all team metrics from all rounds in a tidy/long format CSV file.
    """
    import csv
    metrics = get_team_metrics(round_name="all")
    csv_path = "/home/rafa/Projects/bolao/world_cup_teams_metrics.csv"
    headers = [
        "team_name", "round", "market_value_eur", "top_11_value_eur", 
        "fifa_rank", "fifa_points", "pele_rating", "qualitative_status"
    ]
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in metrics:
                writer.writerow({
                    "team_name": row["team_name"],
                    "round": row["round"],
                    "market_value_eur": row["market_value_eur"],
                    "top_11_value_eur": row["top_11_value_eur"],
                    "fifa_rank": row["fifa_rank"],
                    "fifa_points": row["fifa_points"],
                    "pele_rating": row["pele_rating"],
                    "qualitative_status": row["qualitative_status"]
                })
        return True
    except Exception as e:
        import logging
        logging.getLogger("BolaoAPI").error(f"Erro ao exportar métricas de seleções para CSV: {e}")
        return False

def save_match(home_team, away_team, league, match_date, status='SCHEDULED', home_score=None, away_score=None, external_ids=None):
    """
    Saves or updates a match based on its unique slug (date + normalized teams).
    Returns the match ID.
    """
    # Create unique slug for match deduplication (YYYY-MM-DD-home-away)
    date_part = match_date.split("T")[0] if "T" in match_date else match_date.split(" ")[0]
    
    # Simple normalization for slug
    norm_home = "".join(e for e in home_team.lower() if e.isalnum())
    norm_away = "".join(e for e in away_team.lower() if e.isalnum())
    slug = f"{date_part}-{norm_home}-{norm_away}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if match already exists (by slug or close slug)
    cursor.execute("SELECT id, external_ids, home_score, away_score FROM matches WHERE slug = ?", (slug,))
    existing = cursor.fetchone()
    
    ext_ids_str = json.dumps(external_ids) if external_ids else "{}"
    
    if existing:
        match_id = existing['id']
        # Merge external IDs
        existing_ext = json.loads(existing['external_ids'] or "{}")
        if external_ids:
            existing_ext.update(external_ids)
        merged_ext_str = json.dumps(existing_ext)
        
        # Update score and status if changed (keep completed scores)
        cursor.execute("""
            UPDATE matches 
            SET status = ?, 
                home_score = COALESCE(?, home_score), 
                away_score = COALESCE(?, away_score),
                external_ids = ?
            WHERE id = ?
        """, (status, home_score, away_score, merged_ext_str, match_id))
    else:
        cursor.execute("""
            INSERT INTO matches (slug, home_team, away_team, league, match_date, status, home_score, away_score, external_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (slug, home_team, away_team, league, match_date, status, home_score, away_score, ext_ids_str))
        match_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return match_id

def save_prediction(match_id, source, home_win_prob, draw_prob, away_win_prob, home_score=None, away_score=None):
    """
    Saves or updates a prediction for a match.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO predictions (match_id, source, home_win_prob, draw_prob, away_win_prob, home_score, away_score, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(match_id, source) DO UPDATE SET
            home_win_prob = excluded.home_win_prob,
            draw_prob = excluded.draw_prob,
            away_win_prob = excluded.away_win_prob,
            home_score = COALESCE(excluded.home_score, predictions.home_score),
            away_score = COALESCE(excluded.away_score, predictions.away_score),
            updated_at = excluded.updated_at
    """, (match_id, source, home_win_prob, draw_prob, away_win_prob, home_score, away_score, now))
    conn.commit()
    conn.close()

def get_matches(league=None):
    """
    Returns matches and their joined predictions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM matches"
    params = []
    if league:
        query += " WHERE league = ?"
        params.append(league)
    query += " ORDER BY match_date ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    matches_list = []
    for row in rows:
        match_dict = dict(row)
        match_dict['external_ids'] = json.loads(row['external_ids'] or "{}")
        
        # Get predictions for this match
        cursor.execute("SELECT * FROM predictions WHERE match_id = ?", (row['id'],))
        pred_rows = cursor.fetchall()
        match_dict['predictions'] = [dict(pr) for pr in pred_rows]
        
        matches_list.append(match_dict)
        
    conn.close()
    return matches_list

def get_match(match_id):
    """
    Returns a single match with its predictions.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    match_dict = dict(row)
    match_dict['external_ids'] = json.loads(row['external_ids'] or "{}")
    
    cursor.execute("SELECT * FROM predictions WHERE match_id = ?", (match_id,))
    pred_rows = cursor.fetchall()
    match_dict['predictions'] = [dict(pr) for pr in pred_rows]
    
    conn.close()
    return match_dict

def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def save_settings(settings_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in settings_dict.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
