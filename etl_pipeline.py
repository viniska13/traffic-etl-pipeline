import os
import random
from datetime import datetime
import pandas as pd
import psycopg2

# Zone metadata lives in Neon (zone_dimension table), not hardcoded in the app.
ZONE_COORDS = {
    "Central Junction": {"lat": 12.9716, "lon": 77.5946},
    "Tech Park Belt": {"lat": 12.9352, "lon": 77.6245},
    "Outer Ring Road": {"lat": 12.9698, "lon": 77.7500},
    "Airport Corridor": {"lat": 13.1986, "lon": 77.7066},
    "Silk Board Junction": {"lat": 12.9172, "lon": 77.6228},
    "Whitefield Corridor": {"lat": 12.9750, "lon": 77.7480},
    "Electronic City Link": {"lat": 12.8452, "lon": 77.6602},
    "Hebbal Flyover": {"lat": 13.0358, "lon": 77.5970},
}
ZONES = list(ZONE_COORDS.keys())


def get_hourly_multiplier(hour):
    """Simulates realistic rush-hour traffic patterns instead of flat randomness:
    heavier during morning (8-10) and evening (17-20) commute windows, lighter overnight."""
    if 8 <= hour <= 10 or 17 <= hour <= 20:
        return random.uniform(1.3, 1.6)   # rush hour
    elif 0 <= hour <= 5:
        return random.uniform(0.25, 0.45)  # overnight lull
    else:
        return random.uniform(0.8, 1.1)    # regular daytime


# 1. EXTRACT: Simulate raw traffic metrics with realistic density-speed-time relationships
def extract_traffic_data():
    current_hour = datetime.now().hour
    multiplier = get_hourly_multiplier(current_hour)

    data = []
    for zone in ZONES:
        base_count = random.randint(150, 700)
        vehicle_count = int(min(1200, max(60, base_count * multiplier)))

        # Speed drops as density rises (inverse relationship), plus small noise
        density_ratio = vehicle_count / 1200
        base_speed = 65 - (density_ratio * 48)
        noise = random.uniform(-3.5, 3.5)
        avg_speed_kmh = max(8.0, min(65.0, base_speed + noise))

        data.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "zone_name": zone,
            "vehicle_count": vehicle_count,
            "avg_speed_kmh": round(avg_speed_kmh, 2)
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
    try:
        cursor = conn.cursor()

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zone_dimension (
                zone_name VARCHAR(100) PRIMARY KEY,
                latitude FLOAT,
                longitude FLOAT
            );
        """)
        for zone, coords in ZONE_COORDS.items():
            cursor.execute("""
                INSERT INTO zone_dimension (zone_name, latitude, longitude)
                VALUES (%s, %s, %s)
                ON CONFLICT (zone_name) DO NOTHING;
            """, (zone, coords["lat"], coords["lon"]))

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO raw_traffic_fact (timestamp, zone_name, vehicle_count, avg_speed_kmh, congestion_status)
                VALUES (%s, %s, %s, %s, %s);
            """, (row["timestamp"], row["zone_name"], row["vehicle_count"], row["avg_speed_kmh"], row["congestion_status"]))

        conn.commit()
        cursor.close()
        print(f"Successful ingestion. Loaded {len(df)} rows into Neon Postgres at {datetime.now()}")
    finally:
        conn.close()


if __name__ == "__main__":
    raw_df = extract_traffic_data()
    clean_df = transform_data(raw_df)
    load_to_postgres(clean_df)
