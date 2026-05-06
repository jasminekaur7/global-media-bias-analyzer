import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def populate_global_data():
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        print("🚀 Purging old data...")
        cur.execute("TRUNCATE TABLE news_signals CASCADE;")

        # Massive country list to ensure the app feels global
        countries = [
            "India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", "Japan", "Canada", 
            "Australia", "Israel", "Ukraine", "Pakistan", "South Africa", "Mexico", "Egypt", "South Korea", 
            "Turkey", "Italy", "Argentina", "Nigeria", "Spain", "Vietnam", "Poland", "Thailand", "Iran"
        ]
        
        channels = [
            "BBC NEWS", "CNN", "REUTERS", "AL JAZEERA", "NDTV", "THE HINDU", 
            "CGTN", "DW NEWS", "NHK WORLD", "ABC NEWS", "CBC", "FRANCE 24"
        ]

        print(f"📥 Injecting signals for {len(countries)} regions...")
        for country in countries:
            # Generate 15-20 articles per country for better graphs
            for _ in range(random.randint(15, 20)):
                chan = random.choice(channels)
                score = round(random.uniform(-9.8, 4.5), 2)
                url = f"https://{chan.lower().replace(' ', '')}.com/intel/{random.randint(1000, 9999)}"
                cur.execute(
                    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                    (chan, score, url, country)
                )
        
        conn.commit()
        print(f"✅ SUCCESS: Global registry is live.")
    except Exception as e: print(f"❌ Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    populate_global_data()
