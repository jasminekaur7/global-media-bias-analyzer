import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def populate_global_sentinel():
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("🚀 Purging old data and syncing global registry...")
        cur.execute("TRUNCATE TABLE news_signals CASCADE;")

        # A massive list to ensure the app feels global
        countries = [
            "India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", 
            "Japan", "Canada", "Australia", "Israel", "Ukraine", "Pakistan", "South Africa",
            "Mexico", "Egypt", "South Korea", "Turkey", "Italy", "Argentina", "Nigeria"
        ]
        
        channels = [
            ("BBC NEWS", "UK"), ("CNN", "USA"), ("REUTERS", "UK"), ("AL JAZEERA", "Qatar"),
            ("NDTV", "India"), ("THE HINDU", "India"), ("CGTN", "China"), ("DW NEWS", "Germany"),
            ("NHK WORLD", "Japan"), ("ABC NEWS", "Australia"), ("CBC", "Canada")
        ]

        # Injecting 300+ signals across the globe
        for country in countries:
            for _ in range(random.randint(10, 20)):
                chan, _ = random.choice(channels)
                score = round(random.uniform(-9.8, 4.5), 2)
                url = f"https://{chan.lower().replace(' ', '')}.com/int/{random.randint(100, 999)}"
                cur.execute(
                    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                    (chan, score, url, country)
                )
        
        conn.commit()
        print(f"✅ SUCCESS: {len(countries)} regions populated with active signals.")
    except Exception as e: print(f"❌ Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    populate_global_sentinel()
