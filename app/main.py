import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
import os
from datetime import datetime

from app.database import (
    init_db, get_matches, get_match, get_settings, save_settings, save_prediction
)
from app.scrapers.understat import scrape_understat
from app.scrapers.sofascore import scrape_sofascore
from app.scrapers.odds import scrape_odds
from app.models.consensus import get_consensus_prediction

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BolaoAPI")

# Initialize database on startup
init_db()

app = FastAPI(
    title="Bolão Expert API",
    description="Backend API for managing football match predictions, scrapers, and consensus models.",
    version="1.0.0"
)

# Request / Response Schemas
class SettingsUpdate(BaseModel):
    weight_sofascore: float = Field(..., ge=0.0, le=1.0)
    weight_understat: float = Field(..., ge=0.0, le=1.0)
    weight_odds: float = Field(..., ge=0.0, le=1.0)
    weight_whoscored: float = Field(..., ge=0.0, le=1.0)
    weight_opta: float = Field(..., ge=0.0, le=1.0)
    odds_api_key: str = Field(default="")

class ManualPredictionUpdate(BaseModel):
    source: str = Field(..., description="Source name: manual, whoscored, or opta")
    home_win_prob: float = Field(..., ge=0.0, le=1.0)
    draw_prob: float = Field(..., ge=0.0, le=1.0)
    away_win_prob: float = Field(..., ge=0.0, le=1.0)
    home_score: Optional[float] = Field(None, ge=0.0, description="Predicted home goals or odd value")
    away_score: Optional[float] = Field(None, ge=0.0, description="Predicted away goals or odd value")

# Background Scraping Worker
def run_scrapers_task(scraper_name: str):
    conn_settings = get_settings()
    save_settings({f"status_{scraper_name}": "running", f"last_run_{scraper_name}": datetime.now().isoformat()})
    
    try:
        success = False
        if scraper_name == "understat":
            success = scrape_understat()
        elif scraper_name == "sofascore":
            success = scrape_sofascore()
        elif scraper_name == "odds":
            success = scrape_odds()
        elif scraper_name == "all":
            logger.info("Running all scrapers sequentially...")
            s1 = scrape_understat()
            s2 = scrape_sofascore()
            s3 = scrape_odds()
            success = s1 and s2 and s3
            
        status = "idle" if success else "error"
        save_settings({f"status_{scraper_name}": status})
        logger.info(f"Background scraper task '{scraper_name}' finished with status: {status}")
    except Exception as e:
        logger.error(f"Error running background scraper '{scraper_name}': {e}")
        save_settings({f"status_{scraper_name}": "error"})

# API Endpoints
@app.get("/api/matches")
def read_matches(league: Optional[str] = None):
    try:
        matches = get_matches(league=league)
        weights = get_settings()
        
        # Calculate consensus for each match
        enriched_matches = []
        for match in matches:
            predictions = match["predictions"]
            consensus = get_consensus_prediction(predictions, weights)
            match["consensus"] = consensus
            enriched_matches.append(match)
            
        return enriched_matches
    except Exception as e:
        logger.error(f"Failed to read matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/matches/{match_id}")
def read_match(match_id: int):
    match = get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    weights = get_settings()
    match["consensus"] = get_consensus_prediction(match["predictions"], weights)
    return match

@app.post("/api/matches/{match_id}/manual")
def add_manual_prediction(match_id: int, pred: ManualPredictionUpdate):
    match = get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    try:
        save_prediction(
            match_id=match_id,
            source=pred.source,
            home_win_prob=pred.home_win_prob,
            draw_prob=pred.draw_prob,
            away_win_prob=pred.away_win_prob,
            home_score=pred.home_score,
            away_score=pred.away_score
        )
        return {"status": "success", "message": f"Prediction saved for source {pred.source}."}
    except Exception as e:
        logger.error(f"Failed to save manual prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
def read_settings():
    return get_settings()

@app.post("/api/settings")
def update_settings(new_settings: SettingsUpdate):
    try:
        save_settings(new_settings.model_dump())
        return {"status": "success", "message": "Settings updated successfully."}
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
def trigger_scrape(scraper: str, background_tasks: BackgroundTasks):
    valid_scrapers = ["understat", "sofascore", "odds", "all"]
    if scraper not in valid_scrapers:
        raise HTTPException(status_code=400, detail=f"Invalid scraper name. Choose from {valid_scrapers}")
        
    current_settings = get_settings()
    current_status = current_settings.get(f"status_{scraper}", "idle")
    
    if current_status == "running":
        return {"status": "running", "message": f"Scraper '{scraper}' is already running in background."}
        
    background_tasks.add_task(run_scrapers_task, scraper)
    return {"status": "started", "message": f"Scraper '{scraper}' started in background."}

@app.get("/api/stats")
def get_stats():
    matches = get_matches()
    leagues = set(m["league"] for m in matches)
    total_preds = sum(len(m["predictions"]) for m in matches)
    
    settings = get_settings()
    scraper_statuses = {
        "understat": settings.get("status_understat", "idle"),
        "sofascore": settings.get("status_sofascore", "idle"),
        "odds": settings.get("status_odds", "idle")
    }
    
    return {
        "total_matches": len(matches),
        "leagues": list(leagues),
        "total_predictions": total_preds,
        "scrapers": scraper_statuses
    }

# Serve static frontend files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    logger.warning("Static files directory not found. Please create 'app/static' to serve the UI.")
