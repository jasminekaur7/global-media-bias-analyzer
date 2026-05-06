import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def populate_global():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    # List of 15+ countries to show scale
    countries = ["India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", "Japan", "Canada", "Australia", "Israel", "Ukraine", "Egypt", "South Korea"]
    
    for country in countries:
        for _ in range(20): # 20 articles per country
            cur.execute("INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                        (random.choice(["BBC", "CNN", "REUTERS", "NDTV"]), random.uniform(-9, 4), "https://gdelt.org", country))
    conn.commit()
    print("✅ GLOBAL DATA INJECTED.")

populate_global()
