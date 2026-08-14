import os
import random
from datetime import datetime
import pandas as pd
import psycopg2

# 1. EXTRACT: Fetch raw traffic metrics
def extract_traffic_data():
    zones = ["Central Junction", "Tech Park Belt", "Outer Ring Road", "Airport Corridor"]
    data = []
    for zone in zones:
        data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "zone_name": zone,
            "vehicle_count": random.randint(150, 1200),
            "avg_speed_kmh": round(random.uniform(12.0, 65.0), 2)
        })
    return pd.DataFrame(data)

# 2. TRANSFORM: Data hygiene & rule-based metric generation
def transform_data(df):
    def get_status(speed):
        if speed < 20:
            return "HEAVY_CONGESTION"
        elif speed < 40:
            return "MODERATE_FLOW"
        return "SMOOTH_TRAFFIC"

    df["congestion_status"] = df["avg_speed_kmh"].apply(get_status)
    return df

# 3. LOAD: Ingest clean records into Neon PostgreSQL
def load_to_postgres(df):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable is missing.")
        return

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Create table schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_traffic_fact (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            zone_name VARCHAR(100),
            vehicle_count INT,
            avg_speed_kmh FLOAT,
            congestion_status VARCHAR(50)
        );
    """)

    # Ingest rows
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO raw_traffic_fact (timestamp, zone_name, vehicle_count, avg_speed_kmh, congestion_status)
            VALUES (%s, %s, %s, %s, %s);
        """, (row["timestamp"], row["zone_name"], row["vehicle_count"], row["avg_speed_kmh"], row["congestion_status"]))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Successful Ingestion! Loaded {len(df)} rows into Neon Postgres at {datetime.now()}")

if __name__ == "__main__":
    raw_df = extract_traffic_data()
    clean_df = transform_data(raw_df)
    load_to_postgres(clean_df)
