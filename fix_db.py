import pandas as pd
from sqlalchemy import create_engine

# --- SETTINGS ---
DB_PASS = "jasmine"  # <--- Change this!
CSV_FILE = "data.csv"

try:
    # 1. Connect to your database
    engine = create_engine(f'postgresql://postgres:{DB_PASS}@localhost:5432/shadow_network')

    # 2. Read your CSV
    df = pd.read_csv(CSV_FILE)
    
    # 3. Clean the data (Ensure scores are numbers)
    df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')

    # 4. Push to SQL
    # This 'replaces' the table to match your CSV perfectly
    df.to_sql('news_signals', engine, if_exists='replace', index=False)
    
    print("✅ SUCCESS: Your data is now in the database!")
    print("You can now run app_deploy.py")

except Exception as e:
    print(f"❌ ERROR: {e}")