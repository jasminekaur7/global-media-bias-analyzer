import psycopg2

# We are intentionally removing the try/except block so Python FORCES the exact red error to show.
DB_URL = "postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

print("Step 1: Connecting to Neon Cloud...")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

print("Step 2: Connection successful. Inserting test data...")
cur.execute(
    "INSERT INTO news_signals (actor_name, sentiment_score, source_url, location_name) VALUES (%s, %s, %s, %s)",
    ("TEST NEWS", 1.5, "https://test.com", "India")
)

print("Step 3: Committing data to the cloud...")
conn.commit()

print("Step 4: Verifying the row exists...")
cur.execute("SELECT COUNT(*) FROM news_signals;")
count = cur.fetchone()[0]

print(f"✅ FINAL SUCCESS: The database now has {count} rows.")

cur.close()
conn.close()
