import json
import sqlite3
import httpx
import sys
from app.scorepick_client import ScorePickClient

SETTINGS_PATH = "/home/rafa/Projects/bolao/settings.json"
MATCHES_PATH = "/home/rafa/Projects/bolao/world_cup_matches.json"
DB_PATH = "/home/rafa/Projects/bolao/bolao.db"

def load_settings():
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def load_matches():
    with open(MATCHES_PATH, "r") as f:
        return json.load(f)

def save_opponent_bet(conn, match_sp_id, bet):
    cursor = conn.cursor()
    # columns in opponent_bets: match_id, user_id, user_name, home_score, away_score, points_awarded, is_exact, is_locked, created_at, updated_at
    match_id = match_sp_id
    user_id = bet.get("user_id")
    user_name = bet.get("user_display_name", bet.get("user_email", "Unknown"))
    home_score = bet.get("home_score")
    away_score = bet.get("away_score")
    points_awarded = bet.get("points_awarded", 0)
    is_exact = 1 if bet.get("is_exact") else 0
    is_locked = 1 if bet.get("is_locked") else 0
    created_at = bet.get("created_at")
    updated_at = bet.get("updated_at")
    
    if user_id is None:
        return False
        
    cursor.execute("""
    INSERT INTO opponent_bets (match_id, user_id, user_name, home_score, away_score, points_awarded, is_exact, is_locked, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(match_id, user_id) DO UPDATE SET
        home_score = excluded.home_score,
        away_score = excluded.away_score,
        points_awarded = excluded.points_awarded,
        is_exact = excluded.is_exact,
        is_locked = excluded.is_locked,
        updated_at = excluded.updated_at
    """, (match_id, user_id, user_name, home_score, away_score, points_awarded, is_exact, is_locked, created_at, updated_at))
    return True

def main():
    print("=== SCRAPER DE PALPITES DOS OPONENTES (SCOREPICK) ===")
    settings = load_settings()
    matches = load_matches()
    
    email = settings.get("scorepick_email")
    password = settings.get("scorepick_password")
    pool_id = settings.get("scorepick_pool_id")
    
    if not email or not password or not pool_id:
        print("Erro: Credenciais do ScorePick ausentes no settings.json")
        sys.exit(1)
        
    client = ScorePickClient(email, password)
    if not client.login():
        print("Erro ao autenticar no ScorePick.")
        sys.exit(1)
        
    conn = sqlite3.connect(DB_PATH)
    
    imported_matches_count = 0
    total_bets_count = 0
    
    # We will fetch bets for all matches that have a scorepick ID
    sp_matches = [m for m in matches if m.get("external_ids", {}).get("scorepick") is not None]
    print(f"Encontrados {len(sp_matches)} jogos vinculados ao ScorePick localmente.")
    
    for idx, match in enumerate(sp_matches):
        sp_id = match["external_ids"]["scorepick"]
        # Fetch bets for this match in the pool
        url = f"{client.BASE_URL}/api/pools/{pool_id}/matches/{sp_id}/bets/"
        try:
            r = client.client.get(url)
            if r.status_code == 200:
                bets = r.json()
                if bets:
                    # Filter bets that are locked (locked means we have opponent data)
                    # Note: we can also save unlocked bets, but they only contain our own.
                    # It's fine to save them all, is_locked will indicate if they are public.
                    saved_for_this_match = 0
                    for bet in bets:
                        if save_opponent_bet(conn, sp_id, bet):
                            saved_for_this_match += 1
                    
                    if saved_for_this_match > 0:
                        imported_matches_count += 1
                        total_bets_count += saved_for_this_match
                        
                    # Print progress for locked bets (which have > 1 bet)
                    if len(bets) > 1:
                        print(f"  [+] Jogo {sp_id}: {match['home_team']} vs {match['away_team']} - Coletados {len(bets)} palpites (TRAVADO)")
            else:
                # Some matches might not have bets active or exist yet
                pass
        except Exception as e:
            print(f"  [-] Erro ao buscar palpites para o jogo {sp_id}: {e}")
            
    conn.commit()
    conn.close()
    client.close()
    
    print(f"\nImportação concluída com sucesso!")
    print(f"Total de jogos processados com palpites salvos: {imported_matches_count}")
    print(f"Total de palpites individuais salvos no SQLite: {total_bets_count}")

if __name__ == "__main__":
    main()
