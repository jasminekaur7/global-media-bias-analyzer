import psycopg2
import random

DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def restore_database():
    try:
        print("1. Connecting to Neon...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("2. Clearing old data...")
        cur.execute("TRUNCATE TABLE news_signals RESTART IDENTITY CASCADE;")
        
        print("3. Generating global data...")
        countries = [
            "India", "USA", "Russia", "China", "UK", "Germany", "France", "Brazil", 
            "Japan", "Canada", "Australia", "Israel", "Ukraine", "Egypt", "South Korea",
            "Pakistan", "Mexico", "Italy", "Spain", "South Africa"
        ]
        channels = ["BBC NEWS", "CNN", "REUTERS", "NDTV", "AL JAZEERA", "THE HINDU", "FOX NEWS", "CGTN"]
        
        count = 0
        for country in countries:
            for _ in range(15): # 15 articles per country
                chan = random.choice(channels)
                score = round(random.uniform(-9.0, 4.0), 2)
                url = f"https://{chan.lower().replace(' ', '')}.com/article/{random.randint(1000,9999)}"
                cur.execute(
                    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
                    (chan, score, url, country)
                )
                count += 1
                
        conn.commit()
        print(f"4. SUCCESS! {count} articles inserted across {len(countries)} countries.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    restore_database()
