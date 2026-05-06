import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def populate_global():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    print("🚀 Purging old data and injecting global signals...")
    cur.execute("TRUNCATE TABLE news_signals CASCADE;")

    # Expanded list for global scale
    countries = ["India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", "Japan", "Canada", 
                 "Australia", "Israel", "Ukraine", "Egypt", "South Korea", "Turkey", "Italy", "Pakistan", "Mexico"]
    
    for country in countries:
        for _ in range(random.randint(15, 30)):
            chan = random.choice(["BBC", "CNN", "REUTERS", "NDTV", "AL JAZEERA", "FOX NEWS"])
            cur.execute("INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                        (chan, round(random.uniform(-9.5, 4.0), 2), f"https://{chan.lower()}.com/intel", country))
    
    conn.commit()
    conn.close()
    print(f"✅ Global data sync complete for {len(countries)} regions.")

populate_global()
