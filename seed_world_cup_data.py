import sqlite3
import os

DB_PATH = "/home/rafa/Projects/bolao/bolao.db"

def init_world_cup_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create world_cup_teams table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS world_cup_teams (
        team_name TEXT PRIMARY KEY,
        name_en TEXT NOT NULL,
        emoji TEXT,
        fifa_rank INTEGER,
        fifa_points REAL,
        market_value_eur REAL, -- Millions of Euros
        pele_rating REAL,
        pele_tilt REAL
    );
    """)
    
    # Create opponent_bets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opponent_bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        home_score INTEGER,
        away_score INTEGER,
        points_awarded INTEGER,
        is_exact INTEGER, -- Boolean (0 or 1)
        is_locked INTEGER, -- Boolean (0 or 1)
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(match_id, user_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("Tables world_cup_teams and opponent_bets created/verified in bolao.db.")

def seed_teams():
    # Complete dataset for 48 teams: [name_pt, name_en, emoji, fifa_rank, fifa_points, market_value_eur (M), pele_rating, pele_tilt]
    teams_data = [
        # Group A
        ["México", "Mexico", "🇲🇽", 14, 1687.48, 250.0, 1850.0, 0.2],
        ["Coreia do Sul", "South Korea", "🇰🇷", 27, 1554.0, 280.0, 1790.0, 0.0],
        ["República Tcheca", "Czechia", "🇨🇿", 22, 1600.0, 170.0, 1780.0, 0.0],
        ["África do Sul", "South Africa", "🇿🇦", 40, 1430.0, 75.0, 1620.0, -0.1],
        
        # Group B
        ["Canadá", "Canada", "🇨🇦", 24, 1580.0, 180.0, 1830.0, 0.1],
        ["Suíça", "Switzerland", "🇨🇭", 19, 1650.0, 333.0, 1810.0, 0.0],
        ["Bósnia-Herzegovina", "Bosnia-Herzegovina", "🇧🇦", 37, 1470.0, 70.0, 1710.0, -0.1],
        ["Catar", "Qatar", "🇶🇦", 41, 1420.0, 15.0, 1700.0, 0.0],
        
        # Group C
        ["Brasil", "Brazil", "🇧🇷", 6, 1765.86, 928.0, 2070.0, 0.3],
        ["Marrocos", "Morocco", "🇲🇦", 7, 1755.10, 448.0, 1850.0, -0.2],
        ["Escócia", "Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", 34, 1505.0, 140.0, 1740.0, 0.0],
        ["Haiti", "Haiti", "🇭🇹", 45, 1340.0, 30.0, 1620.0, 0.0],
        
        # Group D
        ["Estados Unidos", "United States", "🇺🇸", 17, 1671.23, 386.0, 1930.0, 0.1],
        ["Turquia", "Turkey", "🇹🇷", 29, 1540.0, 474.0, 1840.0, 0.1],
        ["Paraguai", "Paraguay", "🇵🇾", 32, 1515.0, 120.0, 1820.0, -0.1],
        ["Austrália", "Australia", "🇦🇺", 31, 1520.0, 160.0, 1740.0, 0.0],
        
        # Group E
        ["Alemanha", "Germany", "🇩🇪", 10, 1735.77, 947.0, 1970.0, 0.6],
        ["Equador", "Ecuador", "🇪🇨", 26, 1560.0, 369.0, 1880.0, -0.1],
        ["Costa do Marfim", "Ivory Coast", "🇨🇮", 32, 1515.0, 522.0, 1820.0, -0.1],
        ["Curaçao", "Curaçao", "🇨🇼", 48, 1250.0, 8.0, 1550.0, 0.0],
        
        # Group F
        ["Holanda", "Netherlands", "🇳🇱", 8, 1753.57, 754.0, 1950.0, 0.2],
        ["Japão", "Japan", "🇯🇵", 18, 1661.58, 310.0, 1840.0, 0.1],
        ["Suécia", "Sweden", "🇸🇪", 21, 1610.0, 406.0, 1820.0, 0.0],
        ["Tunísia", "Tunisia", "🇹🇳", 33, 1510.0, 120.0, 1730.0, -0.1],
        
        # Group G
        ["Bélgica", "Belgium", "🇧🇪", 9, 1742.24, 548.0, 1940.0, 0.1],
        ["Egito", "Egypt", "🇪🇬", 23, 1590.0, 155.0, 1740.0, 0.0],
        ["Irã", "Iran", "🇮🇷", 20, 1619.58, 35.0, 1720.0, -0.1],
        ["Nova Zelândia", "New Zealand", "🇳🇿", 46, 1320.0, 18.0, 1620.0, -0.1],
        
        # Group H
        ["Espanha", "Spain", "🇪🇸", 2, 1874.71, 1220.0, 2085.0, 0.4],
        ["Uruguai", "Uruguay", "🇺🇾", 16, 1673.07, 359.0, 1910.0, -0.1],
        ["Arábia Saudita", "Saudi Arabia", "🇸🇦", 36, 1480.0, 65.0, 1680.0, -0.1],
        ["Cabo Verde", "Cape Verde", "🇨🇻", 47, 1300.0, 12.0, 1560.0, 0.0],
        
        # Group I
        ["França", "France", "🇫🇷", 3, 1870.70, 1520.0, 2080.0, 0.4],
        ["Noruega", "Norway", "🇳🇴", 25, 1571.0, 590.0, 1960.0, 0.3],
        ["Senegal", "Senegal", "🇸🇳", 15, 1684.07, 478.0, 1800.0, -0.2],
        ["Iraque", "Iraq", "🇮🇶", 43, 1385.0, 25.0, 1650.0, 0.0],
        
        # Group J
        ["Argentina", "Argentina", "🇦🇷", 1, 1877.27, 807.0, 2090.0, 0.3],
        ["Áustria", "Austria", "🇦🇹", 28, 1548.0, 220.0, 1850.0, 0.1],
        ["Algélia", "Algeria", "🇩🇿", 30, 1530.0, 100.0, 1770.0, 0.1],
        ["Jordânia", "Jordan", "🇯🇴", 44, 1370.0, 22.0, 1620.0, 0.0],
        
        # Group K
        ["Colômbia", "Colombia", "🇨🇴", 13, 1698.35, 320.0, 1980.0, -0.1],
        ["Portugal", "Portugal", "🇵🇹", 5, 1767.85, 1010.0, 1960.0, 0.2],
        ["RD Congo", "Congo DR", "🇨🇩", 38, 1455.0, 40.0, 1720.0, -0.1],
        ["Uzbequistão", "Uzbekistan", "🇺🇿", 39, 1440.0, 55.0, 1700.0, 0.0],
        
        # Group L
        ["Inglaterra", "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", 4, 1828.02, 1360.0, 2070.0, 0.2],
        ["Croácia", "Croatia", "🇭🇷", 11, 1714.87, 387.0, 1910.0, 0.0],
        ["Panamá", "Panama", "🇵🇦", 42, 1400.0, 45.0, 1700.0, 0.0],
        ["Gana", "Ghana", "🇬🇭", 35, 1495.0, 110.0, 1670.0, 0.0]
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert or replace
    cursor.executemany("""
    INSERT OR REPLACE INTO world_cup_teams (team_name, name_en, emoji, fifa_rank, fifa_points, market_value_eur, pele_rating, pele_tilt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, teams_data)
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT count(*) FROM world_cup_teams")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Successfully seeded {count} teams in world_cup_teams.")

if __name__ == "__main__":
    init_world_cup_tables()
    seed_teams()
