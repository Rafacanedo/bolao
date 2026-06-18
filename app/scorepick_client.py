import httpx
import logging

logger = logging.getLogger("ScorePickClient")

class ScorePickClient:
    BASE_URL = "https://scorepick.theluckydun.com.br"
    
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.client = httpx.Client(timeout=15.0, follow_redirects=True)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.client.headers.update(self.headers)
        self.is_authenticated = False
        
    def login(self):
        url = f"{self.BASE_URL}/api/auth/app/v1/auth/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        try:
            r = self.client.post(url, json=payload)
            if r.status_code == 200:
                data = r.json()
                if data.get("meta", {}).get("is_authenticated"):
                    self.is_authenticated = True
                    logger.info("Successfully authenticated with ScorePick.")
                    return True
            logger.error(f"Login failed: status {r.status_code}, response: {r.text}")
            return False
        except Exception as e:
            logger.error(f"Exception during login: {e}")
            return False
            
    def get_pool_details(self, pool_id):
        url = f"{self.BASE_URL}/api/pools/{pool_id}/"
        try:
            r = self.client.get(url)
            if r.status_code == 200:
                return r.json()
            logger.error(f"Failed to get pool details for {pool_id}: status {r.status_code}")
            return None
        except Exception as e:
            logger.error(f"Exception fetching pool details: {e}")
            return None
            
    def get_matches(self, championship_code="WC"):
        url = f"{self.BASE_URL}/api/matches/?championship={championship_code}"
        try:
            r = self.client.get(url)
            if r.status_code == 200:
                return r.json()
            logger.error(f"Failed to get matches: status {r.status_code}")
            return []
        except Exception as e:
            logger.error(f"Exception fetching matches: {e}")
            return []
            
    def get_match_detail(self, match_id):
        url = f"{self.BASE_URL}/api/matches/{match_id}/"
        try:
            r = self.client.get(url)
            if r.status_code == 200:
                return r.json()
            logger.error(f"Failed to get match detail for {match_id}: status {r.status_code}")
            return None
        except Exception as e:
            logger.error(f"Exception fetching match detail: {e}")
            return None
            
    def get_bets(self, pool_id):
        url = f"{self.BASE_URL}/api/pools/{pool_id}/bets/"
        try:
            r = self.client.get(url)
            if r.status_code == 200:
                return r.json()
            logger.error(f"Failed to get bets: status {r.status_code}")
            return []
        except Exception as e:
            logger.error(f"Exception fetching bets: {e}")
            return []
            
    def submit_bet(self, pool_id, match_id, home_score, away_score):
        url = f"{self.BASE_URL}/api/pools/{pool_id}/bets/"
        payload = {
            "match_id": int(match_id),
            "home_score": int(home_score),
            "away_score": int(away_score)
        }
        try:
            r = self.client.post(url, json=payload)
            if r.status_code in [200, 201]:
                logger.info(f"Successfully submitted bet {home_score}x{away_score} for match {match_id}")
                return True, r.json()
            logger.error(f"Failed to submit bet for match {match_id}: status {r.status_code}, response: {r.text}")
            return False, r.text
        except Exception as e:
            logger.error(f"Exception submitting bet for match {match_id}: {e}")
            return False, str(e)
            
    def close(self):
        self.client.close()
