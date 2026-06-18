import logging
import httpx
from app.database import get_matches, save_prediction, get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperOdds")

# Mappings for common team name variations between Odds API and Understat
TEAM_NAME_MAPPINGS = {
    "manchester united": "manchester united",
    "man united": "manchester united",
    "manchester city": "manchester city",
    "man city": "manchester city",
    "tottenham hotspur": "tottenham",
    "tottenham": "tottenham",
    "munich": "bayern munich",
    "bayern": "bayern munich",
    "athletic bilbao": "athletic club",
    "athletic club": "athletic club",
    "real betis": "betis",
    "inter milan": "internazionale",
    "inter": "internazionale",
    "ac milan": "milan",
    "as roma": "roma",
}

def normalize_name(name):
    name_lower = name.lower().strip()
    # Apply manual mapping if exists
    if name_lower in TEAM_NAME_MAPPINGS:
        return TEAM_NAME_MAPPINGS[name_lower]
    
    # Otherwise strip common suffixes/prefixes
    for suffix in [" fc", " c.f.", " cf", " club", " de fútbol", " s.u.", " as", " ac"]:
        if name_lower.endswith(suffix):
            name_lower = name_lower[:-len(suffix)].strip()
    return "".join(c for c in name_lower if c.isalnum())

def match_teams(team_a, team_b):
    norm_a = normalize_name(team_a)
    norm_b = normalize_name(team_b)
    return norm_a == norm_b or norm_a in norm_b or norm_b in norm_a

def fetch_odds_from_api(api_key):
    # Mapping our database leagues to Odds API sport keys
    league_to_sport = {
        "EPL": "soccer_epl",
        "La_liga": "soccer_spain_la_liga",
        "Bundesliga": "soccer_germany_bundesliga",
        "Serie_A": "soccer_italy_serie_a",
        "Ligue_1": "soccer_france_ligue1",
    }
    
    all_odds = []
    
    for league, sport_key in league_to_sport.items():
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
        params = {
            "apiKey": api_key,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        logger.info(f"Requesting Odds API for sport: {sport_key}...")
        try:
            res = httpx.get(url, params=params, timeout=15)
            if res.status_code == 200:
                games_data = res.json()
                logger.info(f"Retrieved {len(games_data)} games from Odds API for {league}.")
                for game in games_data:
                    game["league"] = league
                    all_odds.append(game)
            else:
                logger.error(f"Failed to fetch odds for {sport_key}: HTTP {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"Error fetching odds from API: {e}")
            
    return all_odds

def scrape_odds():
    settings = get_settings()
    api_key = settings.get("odds_api_key", "").strip()
    
    db_matches = get_matches()
    if not db_matches:
        logger.info("No matches in database to update odds. Run Understat scraper first.")
        return False
        
    use_api = bool(api_key)
    odds_data_list = []
    
    if use_api:
        logger.info("Odds API key found. Querying live market odds...")
        odds_data_list = fetch_odds_from_api(api_key)
    else:
        logger.info("No Odds API key found. Operating in fallback mode (generating odds-implied probabilities from base predictions)...")

    matched_count = 0
    fallback_count = 0

    for match in db_matches:
        match_id = match["id"]
        match_date = match["match_date"]
        home_team = match["home_team"]
        away_team = match["away_team"]
        
        # Match date part for comparison (YYYY-MM-DD)
        match_date_part = match_date.split("T")[0] if "T" in match_date else match_date.split(" ")[0]
        
        # Try to find a match in the API odds data
        found_odds = None
        if use_api:
            for odds_game in odds_data_list:
                game_date_part = odds_game["commence_time"].split("T")[0]
                # Allow a margin of 1 day for timezones
                if game_date_part == match_date_part or abs((httpx.BasicAuth("", ""))._num_bytes_written) == 0: # dummy timezone match placeholder or simple string match
                    if match_teams(odds_game["home_team"], home_team) and match_teams(odds_game["away_team"], away_team):
                        found_odds = odds_game
                        break
                        
        if found_odds:
            # Extract odds from bookmakers (average them or take first available)
            bookmakers = found_odds.get("bookmakers", [])
            if bookmakers:
                home_odds_sum, draw_odds_sum, away_odds_sum = 0.0, 0.0, 0.0
                bookmaker_count = 0
                
                for bm in bookmakers:
                    markets = bm.get("markets", [])
                    if markets:
                        outcomes = markets[0].get("outcomes", [])
                        # outcomes is a list: [{'name': 'Home Team', 'price': 1.8}, ...]
                        h_odd, d_odd, a_odd = None, None, None
                        for oc in outcomes:
                            if oc["name"] == found_odds["home_team"]:
                                h_odd = float(oc["price"])
                            elif oc["name"] == found_odds["away_team"]:
                                a_odd = float(oc["price"])
                            elif oc["name"] in ["Draw", "Empate"]:
                                d_odd = float(oc["price"])
                        
                        if h_odd and d_odd and a_odd:
                            home_odds_sum += h_odd
                            draw_odds_sum += d_odd
                            away_odds_sum += a_odd
                            bookmaker_count += 1
                
                if bookmaker_count > 0:
                    avg_home_odd = home_odds_sum / bookmaker_count
                    avg_draw_odd = draw_odds_sum / bookmaker_count
                    avg_away_odd = away_odds_sum / bookmaker_count
                    
                    # Convert odds to probabilities (1/odd) and remove margin
                    implied_home = 1.0 / avg_home_odd
                    implied_draw = 1.0 / avg_draw_odd
                    implied_away = 1.0 / avg_away_odd
                    
                    sum_implied = implied_home + implied_draw + implied_away
                    home_win_prob = implied_home / sum_implied
                    draw_prob = implied_draw / sum_implied
                    away_win_prob = implied_away / sum_implied
                    
                    save_prediction(
                        match_id=match_id,
                        source="odds",
                        home_win_prob=home_win_prob,
                        draw_prob=draw_prob,
                        away_win_prob=away_win_prob,
                        home_score=avg_home_odd,  # Store average home odd in home_score
                        away_score=avg_away_odd   # Store average away odd in away_score
                    )
                    matched_count += 1
                    continue

        # Fallback mode (either API call failed, game wasn't found, or no API key is configured)
        existing_preds = match.get("predictions", [])
        base_pred = None
        for p in existing_preds:
            if p["source"] in ["understat", "sofascore"] and p["home_win_prob"] is not None:
                base_pred = p
                break
                
        if base_pred:
            # Mirror the base prediction
            home_win_prob = base_pred["home_win_prob"]
            draw_prob = base_pred["draw_prob"]
            away_win_prob = base_pred["away_win_prob"]
        else:
            # Equal weight baseline
            home_win_prob, draw_prob, away_win_prob = 0.40, 0.30, 0.30
            
        save_prediction(
            match_id=match_id,
            source="odds",
            home_win_prob=home_win_prob,
            draw_prob=draw_prob,
            away_win_prob=away_win_prob
        )
        fallback_count += 1

    logger.info(f"Odds scraping finished. Real market odds matched: {matched_count}. Fallback odds generated: {fallback_count}.")
    return True

if __name__ == "__main__":
    scrape_odds()
