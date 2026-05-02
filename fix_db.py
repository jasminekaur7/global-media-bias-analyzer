import pandas as pd
from sqlalchemy import create_engine

# --- SETTINGS ---
DB_PASS = "jasmine"  # <--- Change this!
CSV_FILE = "data.csv"

try:
    # 1. Connect to your database
    engine = create_engine('postgresql://neondb_owner:npg_GSZgsy4Eaf2p@ep-green-wind-anshqoip.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require')

    # 2. Read your CSV
    df = pd.read_csv(CSV_FILE)
    
    # 3. Clean the data (Ensure scores are numbers)
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')
try: 
    # 4. Push to SQL
    # This 'replaces' the table to match your CSV perfectly
   # Update this line in fix_db.py
    df.to_sql(
    'news_signals', 
    engine, 
    if_exists='replace',  # This will try to drop the table first
    index=False,
    method='multi',       # Faster for cloud
    chunksize=1000        # Smaller chunks to avoid overwhelming the connection  
    )
    print("✅ Success! The news data is now live in the Neon Cloud.")
    print("You can now run app_deploy.py")
except Exception as e:
    print(f"❌ ERROR: {e}")