import json
import logging
from curl_cffi import requests
from app.database import save_match, save_prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperUnderstat")

LEAGUES = ["EPL", "La_liga", "Bundesliga", "Serie_A", "Ligue_1"]
SEASONS = [2025]  # Can add more seasons dynamically

HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://understat.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_understat():
    session = requests.Session()
    logger.info("Initializing session and fetching cookies from Understat...")
    try:
        session.get("https://understat.com", headers=HEADERS, impersonate="chrome")
    except Exception as e:
        logger.error(f"Failed to fetch homepage cookies: {e}")
        return False

    success_count = 0
    match_count = 0
    prediction_count = 0

    for league in LEAGUES:
        for season in SEASONS:
            url = f"https://understat.com/getLeagueData/{league}/{season}"
            logger.info(f"Fetching league data for {league} {season}...")
            try:
                res = session.get(url, headers=HEADERS, impersonate="chrome")
                if res.status_code != 200:
                    logger.error(f"Failed to fetch data for {league} {season}: HTTP {res.status_code}")
                    continue
                
                data = res.json()
                matches = data.get("dates", [])
                logger.info(f"Found {len(matches)} matches for {league} {season}")
                
                for match in matches:
                    home_team = match["h"]["title"]
                    away_team = match["a"]["title"]
                    match_date = match["datetime"]
                    match_id = match["id"]
                    is_result = match["isResult"]
                    
                    status = "FINISHED" if is_result else "SCHEDULED"
                    home_score = int(match["goals"]["h"]) if is_result and match["goals"]["h"] is not None else None
                    away_score = int(match["goals"]["a"]) if is_result and match["goals"]["a"] is not None else None
                    
                    external_ids = {"understat": match_id}
                    
                    # Save match to database
                    db_match_id = save_match(
                        home_team=home_team,
                        away_team=away_team,
                        league=league,
                        match_date=match_date,
                        status=status,
                        home_score=home_score,
                        away_score=away_score,
                        external_ids=external_ids
                    )
                    match_count += 1
                    
                    # Save prediction if forecast data is available
                    forecast = match.get("forecast")
                    if forecast and "w" in forecast and "d" in forecast and "l" in forecast:
                        try:
                            home_win_prob = float(forecast["w"])
                            draw_prob = float(forecast["d"])
                            away_win_prob = float(forecast["l"])
                            
                            # Estimate predicted score using xG or forecast probabilities
                            # Understat doesn't offer direct score prediction in datesData,
                            # but we can save the forecast and compute score elsewhere.
                            save_prediction(
                                match_id=db_match_id,
                                source="understat",
                                home_win_prob=home_win_prob,
                                draw_prob=draw_prob,
                                away_win_prob=away_win_prob
                            )
                            prediction_count += 1
                        except Exception as e:
                            logger.warning(f"Error parsing forecast for match {match_id}: {e}")
                            
                success_count += 1
            except Exception as e:
                logger.error(f"Error processing {league} {season}: {e}")

    logger.info(f"Understat scraping completed. Success leagues: {success_count}/{len(LEAGUES)}. Total matches processed: {match_count}. Predictions saved: {prediction_count}")
    return True

if __name__ == "__main__":
    scrape_understat()
