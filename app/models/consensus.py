import math
import logging

logger = logging.getLogger("ConsensusEngine")

def poisson_probability(k, lamb):
    """
    Calculates Poisson probability: (lamb^k * e^-lamb) / k!
    """
    if lamb <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lamb, k) * math.exp(-lamb)) / math.factorial(k)

def calculate_score_probabilities(lambda_h, lambda_a, max_goals=5):
    """
    Generates a matrix of score probabilities using Poisson distribution.
    Returns a dict with key (h_goals, a_goals) -> probability.
    """
    scores = {}
    total_prob = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p_h = poisson_probability(h, lambda_h)
            p_a = poisson_probability(a, lambda_a)
            prob = p_h * p_a
            scores[(h, a)] = prob
            total_prob += prob
            
    # Normalize so they sum to 1.0 (since we cap at max_goals)
    if total_prob > 0:
        for k in scores:
            scores[k] /= total_prob
            
    return scores

def get_match_outcome(h, a):
    if h > a:
        return "HOME_WIN"
    elif h < a:
        return "AWAY_WIN"
    else:
        return "DRAW"

def calculate_expected_points(guess_h, guess_a, score_probs, rule_exact=5, rule_outcome=2, team_goals_bonus=True, points_team_goals=1):
    """
    Calculates the expected points of a guess (guess_h, guess_a)
    given the full score probability matrix and real bolão rules.
    """
    expected_pts = 0.0
    guess_outcome = get_match_outcome(guess_h, guess_a)
    
    for (actual_h, actual_a), prob in score_probs.items():
        pts_outcome = 0
        actual_outcome = get_match_outcome(actual_h, actual_a)
        if guess_outcome == actual_outcome:
            pts_outcome = rule_outcome
            
        pts_exact = 0
        if guess_h == actual_h and guess_a == actual_a:
            pts_exact = rule_exact
            
        pts_bonus = 0
        if team_goals_bonus and pts_outcome > 0 and pts_exact == 0:
            if guess_h == actual_h or guess_a == actual_a:
                pts_bonus = points_team_goals
                
        game_total = pts_exact if pts_exact > 0 else (pts_outcome + pts_bonus)
        expected_pts += game_total * prob
        
    return expected_pts

def get_consensus_prediction(predictions, weights, rule_exact=5, rule_outcome=2, team_goals_bonus=True, points_team_goals=1):
    """
    Combines W/D/L probabilities from multiple sources using user-defined weights.
    Estimates expected goals (lambda_h, lambda_a) and computes:
    - Consensus probabilities
    - Most likely score (highest single probability)
    - Optimal guess (maximizing expected points in bolão)
    """
    # Active weights filter
    active_weights = {}
    for p in predictions:
        source = p["source"]
        weight_key = f"weight_{source}"
        weight = float(weights.get(weight_key, 0.1))
        
        # Check if prediction has data
        if p.get("home_win_prob") is not None:
            active_weights[source] = {
                "weight": weight,
                "home": p["home_win_prob"],
                "draw": p["draw_prob"],
                "away": p["away_win_prob"]
            }
            
    if not active_weights:
        # Equal distribution if no predictions
        return {
            "consensus_home": 0.40,
            "consensus_draw": 0.30,
            "consensus_away": 0.30,
            "most_likely_score": (1, 1),
            "optimal_guess": (1, 1),
            "score_probabilities": {},
            "details": {}
        }
        
    # Calculate weighted average W/D/L
    total_w = sum(item["weight"] for item in active_weights.values())
    if total_w <= 0:
        # Fallback to equal weights of active sources
        for k in active_weights:
            active_weights[k]["weight"] = 1.0
        total_w = len(active_weights)
        
    avg_home = sum(item["home"] * item["weight"] for item in active_weights.values()) / total_w
    avg_draw = sum(item["draw"] * item["weight"] for item in active_weights.values()) / total_w
    avg_away = sum(item["away"] * item["weight"] for item in active_weights.values()) / total_w
    
    # Normalize to ensure they sum to exactly 1.0
    sum_probs = avg_home + avg_draw + avg_away
    avg_home /= sum_probs
    avg_draw /= sum_probs
    avg_away /= sum_probs
    
    # Estimate lambda (expected goals) for home and away
    # Base total goals for professional matches is around 2.6
    total_expected_goals = 2.6
    
    # Home goals proportion based on win probability and half of draw probability
    home_share = (avg_home + 0.5 * avg_draw)
    lambda_h = total_expected_goals * home_share
    lambda_a = total_expected_goals * (1.0 - home_share)
    
    # Compute score probabilities (Poisson)
    max_goals = 5
    score_probs = calculate_score_probabilities(lambda_h, lambda_a, max_goals)
    
    # 1. Most Likely Score (highest probability in matrix)
    most_likely = max(score_probs, key=score_probs.get)
    
    # 2. Optimal Sweepstakes Guess (maximizing expected points)
    best_guess = (1, 1)
    max_expected_pts = -1.0
    
    for gh in range(4):  # limit guess to a realistic 0-3 goals to avoid outlier guesses
        for ga in range(4):
            ep = calculate_expected_points(gh, ga, score_probs, rule_exact, rule_outcome, team_goals_bonus, points_team_goals)
            if ep > max_expected_pts:
                max_expected_pts = ep
                best_guess = (gh, ga)
                
    # Format detailed info
    details = {source: {"home": item["home"], "draw": item["draw"], "away": item["away"], "weight": item["weight"]} 
               for source, item in active_weights.items()}
               
    return {
        "consensus_home": avg_home,
        "consensus_draw": avg_draw,
        "consensus_away": avg_away,
        "most_likely_score": most_likely,
        "optimal_guess": best_guess,
        "expected_points": max_expected_pts,
        "score_probabilities": [{"score": f"{h}-{a}", "prob": prob} for (h, a), prob in sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:6]],
        "details": details
    }

if __name__ == "__main__":
    # Test consensus calculations
    preds = [
        {"source": "understat", "home_win_prob": 0.60, "draw_prob": 0.25, "away_win_prob": 0.15},
        {"source": "sofascore", "home_win_prob": 0.50, "draw_prob": 0.30, "away_win_prob": 0.20},
    ]
    weights = {"weight_understat": 0.6, "weight_sofascore": 0.4}
    res = get_consensus_prediction(preds, weights)
    print("Test Results:")
    print("Consensus H/D/A:", f"{res['consensus_home']:.2%} / {res['consensus_draw']:.2%} / {res['consensus_away']:.2%}")
    print("Most Likely Score:", res["most_likely_score"])
    print("Optimal Guess:", res["optimal_guess"], "with Expected Points:", f"{res['expected_points']:.2f}")
    print("Top score probs:", res["score_probabilities"])
