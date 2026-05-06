import psycopg2
import random

# Your Neon Connection String
DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def run_global_ingestion():
    conn = None
    try:
        print("🚀 Connecting to Neon Cloud...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        print("🧹 Clearing old table data...")
        cur.execute("TRUNCATE TABLE news_signals CASCADE;")

        # Expanded Global Dataset
        countries = ["India", "USA", "Russia", "UK", "China", "Germany", "France", "Canada", "Japan", "Australia"]
        channels = [
            ("BBC NEWS", "UK"), ("CNN", "USA"), ("REUTERS", "UK"), 
            ("AL JAZEERA", "Qatar"), ("NDTV", "India"), ("THE HINDU", "India"), 
            ("DW NEWS", "Germany"), ("FRANCE 24", "France"), ("CGTN", "China"), 
            ("ABC NEWS", "Australia"), ("CBC", "Canada"), ("NHK WORLD", "Japan")
        ]

        print("📥 Injecting 120 global signals...")
        for country in countries:
            for _ in range(12): # 12 articles per country
                channel_name, _ = random.choice(channels)
                # Random sentiment logic: Negative-heavy for demo purposes
                score = round(random.uniform(-9.5, 3.5), 2) 
                url = f"https://{channel_name.lower().replace(' ', '')}.com/report/{random.randint(1000, 9999)}"
                
                cur.execute(
                    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                    (channel_name, score, url, country)
                )

        conn.commit()
        print(f"✅ SUCCESS: {len(countries)} countries and 120 signals are now live.")

    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Connection closed.")

if __name__ == "__main__":
    run_global_ingestion()
