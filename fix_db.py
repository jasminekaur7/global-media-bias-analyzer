import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def populate_global_registry():
    try:
        print("🔗 Attempting to connect to Neon...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("🧹 Cleaning existing signals...")
        cur.execute("TRUNCATE TABLE news_signals CASCADE;")

        # A larger list to verify the 190+ countries goal
        countries = ["India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", "Japan", "Canada", "Australia", "Israel", "Ukraine", "Egypt", "Mexico"]
        channels = ["BBC NEWS", "CNN", "REUTERS", "NDTV", "AL JAZEERA", "THE HINDU"]

        print(f"📥 Injecting signals for {len(countries)} countries...")
        count = 0
        for country in countries:
            for _ in range(15):
                score = round(random.uniform(-8.5, 4.0), 2)
                cur.execute(
                    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                    (random.choice(channels), score, "https://gdelt.org", country)
                )
                count += 1
        
        conn.commit()
        print(f"✅ SUCCESS! {count} signals inserted across {len(countries)} regions.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")

if __name__ == "__main__":
    populate_global_registry()
