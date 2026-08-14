import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

st.set_page_config(
    page_title="Urban Transit ETL & Traffic Dashboard",
    layout="wide"
)

st.title("Urban Transit ETL & Traffic Analytics Dashboard")
st.caption("Live traffic telemetry powered by Neon Cloud PostgreSQL & Automated Ingestion")

# Fetch DATABASE_URL from Streamlit Secrets or Environment Variable
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", ""))

@st.cache_data(ttl=30)
def fetch_data(query):
    if not DATABASE_URL:
        st.error("DATABASE_URL is not configured.")
        st.stop()
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

try:
    # 1. Top Metrics Section
    summary_query = """
    SELECT 
        COUNT(*) AS total_records,
        ROUND(AVG(vehicle_count)::numeric, 2) AS overall_avg_vehicles,
        ROUND(AVG(avg_speed_kmh)::numeric, 2) AS overall_avg_speed
    FROM raw_traffic_fact;
    """
    summary_df = fetch_data(summary_query)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Telemetry Records", f"{summary_df['total_records'][0]:,}")
    col2.metric("Average Vehicle Density", f"{summary_df['overall_avg_vehicles'][0]} vehicles")
    col3.metric("Average Transit Speed", f"{summary_df['overall_avg_speed'][0]} km/h")

    st.markdown("---")

    # 2. Zone Comparison Visualizations
    st.subheader("Zone Performance Analytics")
    zone_query = """
    SELECT 
        zone_name,
        ROUND(AVG(vehicle_count)::numeric, 2) AS avg_vehicles,
        ROUND(AVG(avg_speed_kmh)::numeric, 2) AS avg_speed
    FROM raw_traffic_fact
    GROUP BY zone_name
    ORDER BY avg_vehicles DESC;
    """
    zone_df = fetch_data(zone_query)

    col_left, col_right = st.columns(2)

    with col_left:
        fig_vol = px.bar(
            zone_df,
            x="zone_name",
            y="avg_vehicles",
            title="Average Vehicle Volume by Zone",
            labels={"zone_name": "Zone", "avg_vehicles": "Avg Vehicle Count"},
            color="avg_vehicles",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_right:
        fig_speed = px.bar(
            zone_df,
            x="zone_name",
            y="avg_speed",
            title="Average Speed (km/h) by Zone",
            labels={"zone_name": "Zone", "avg_speed": "Avg Speed (km/h)"},
            color="avg_speed",
            color_continuous_scale="Greens"
        )
        st.plotly_chart(fig_speed, use_container_width=True)

    st.markdown("---")

    # 3. Live Data Table
    st.subheader("Recent Ingested Telemetry Data")
    raw_query = "SELECT * FROM raw_traffic_fact ORDER BY timestamp DESC LIMIT 50;"
    raw_df = fetch_data(raw_query)
    st.dataframe(raw_df, use_container_width=True)

except Exception as e:
    st.error(f"Error connecting to Neon PostgreSQL: {e}")
