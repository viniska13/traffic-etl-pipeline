import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Urban Transit Telemetry Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Styling (Executive Dark Look)
st.markdown("""
    <style>
    .metric-card {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .metric-title {
        color: #8B949E;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .metric-value {
        color: #58A6FF;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-sub {
        color: #7EE787;
        font-size: 0.8rem;
        margin-top: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# Fixed color palette reused across every chart, so a zone is always the same color
ZONE_COLORS = {
    "Central Junction": "#58A6FF",
    "Tech Park Belt": "#7EE787",
    "Outer Ring Road": "#FFA657",
    "Airport Corridor": "#F778BA",
}
STATUS_COLORS = {
    "HEAVY_CONGESTION": "#F85149",
    "MODERATE_FLOW": "#FFA657",
    "SMOOTH_TRAFFIC": "#7EE787",
}
# Approximate coordinates for the zone map (demo zones spread across a metro area)
ZONE_COORDS = {
    "Central Junction": {"lat": 12.9716, "lon": 77.5946},
    "Tech Park Belt": {"lat": 12.9352, "lon": 77.6245},
    "Outer Ring Road": {"lat": 12.9698, "lon": 77.7500},
    "Airport Corridor": {"lat": 13.1986, "lon": 77.7066},
}

# 3. Database Connection
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", ""))

@st.cache_data(ttl=15)
def fetch_data(query):
    if not DATABASE_URL:
        st.error("DATABASE_URL secret is not configured.")
        st.stop()
    conn = psycopg2.connect(DATABASE_URL)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# 4. Sidebar Controls
st.sidebar.title("🎛️ Control Panel")
st.sidebar.caption("Data Engineering Pipeline: **ACTIVE 🟢**")
st.sidebar.markdown("---")

try:
    # Fetch Raw Fact Data — secondary sort by id keeps rows from the same batch in a
    # stable, deterministic order instead of an arbitrary tie-break on identical timestamps
    raw_df = fetch_data("SELECT * FROM raw_traffic_fact ORDER BY timestamp DESC, id DESC;")
    raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])

    # Interactive Sidebar Filter
    all_zones = sorted(raw_df['zone_name'].dropna().unique().tolist())
    selected_zones = st.sidebar.multiselect("Filter Monitored Zones", all_zones, default=all_zones)

    st.sidebar.markdown("---")
    st.sidebar.info("💡 Data is auto-refreshed from Neon PostgreSQL Data Warehouse.")

    # Filtered Dataframe
    if selected_zones:
        df = raw_df[raw_df['zone_name'].isin(selected_zones)].copy()
    else:
        df = raw_df.copy()

    # 5. Header Section
    st.title("⚡ Urban Transit Telemetry & Analytics Platform")
    st.caption("Real-Time ETL Data Pipeline | Cloud Data Warehouse (Neon PostgreSQL) + Automated GitHub Actions Ingestion")

    with st.expander("ℹ️ About this project / Architecture"):
        st.markdown("""
        **Pipeline:** GitHub Actions (hourly cron) runs `etl_pipeline.py`, which generates and
        transforms zone-level traffic telemetry and loads it into a Neon PostgreSQL warehouse.
        This Streamlit app queries that warehouse live and renders the views below.

        **Stack:** Python · GitHub Actions · Neon (serverless Postgres) · Streamlit · Plotly

        **Source:** [github.com/viniska13/traffic-etl-pipeline](https://github.com/viniska13/traffic-etl-pipeline)
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Executive Metric Cards
    total_records = len(df)
    avg_density = df['vehicle_count'].mean() if not df.empty else 0
    avg_speed = df['avg_speed_kmh'].mean() if not df.empty else 0

    # Freshness: when the warehouse last received data
    last_sync = raw_df['timestamp'].max() if not raw_df.empty else None
    if last_sync is not None:
        minutes_ago = int((pd.Timestamp.now() - last_sync).total_seconds() // 60)
        freshness_label = f"{minutes_ago} min ago" if minutes_ago >= 1 else "just now"
    else:
        freshness_label = "N/A"

    # Speed trend vs the previous ingestion batch
    batch_times = sorted(df['timestamp'].unique()) if not df.empty else []
    speed_delta = None
    if len(batch_times) >= 2:
        last_batch_speed = df[df['timestamp'] == batch_times[-1]]['avg_speed_kmh'].mean()
        prev_batch_speed = df[df['timestamp'] == batch_times[-2]]['avg_speed_kmh'].mean()
        speed_delta = last_batch_speed - prev_batch_speed

    if speed_delta is None:
        delta_html = "Network Speed"
    elif speed_delta >= 0:
        delta_html = f"▲ {speed_delta:.1f} km/h vs last sync"
    else:
        delta_html = f"▼ {abs(speed_delta):.1f} km/h vs last sync"

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">TOTAL TELEMETRY LOGS</div>
                <div class="metric-value">{total_records:,}</div>
                <div class="metric-sub">Synced from Fact Table</div>
            </div>
        ''', unsafe_allow_html=True)
    with m2:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">AVG VEHICLE DENSITY</div>
                <div class="metric-value">{avg_density:.1f}</div>
                <div class="metric-sub">Vehicles / Zone</div>
            </div>
        ''', unsafe_allow_html=True)
    with m3:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">AVG TRANSIT SPEED</div>
                <div class="metric-value" style="color: #7EE787;">{avg_speed:.1f} <span style="font-size: 1rem;">km/h</span></div>
                <div class="metric-sub">{delta_html}</div>
            </div>
        ''', unsafe_allow_html=True)
    with m4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">LAST SYNCED</div>
                <div class="metric-value" style="color: #FFA657; font-size: 1.4rem;">{freshness_label}</div>
                <div class="metric-sub">From GitHub Actions cron</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 7. Tabbed Navigation View
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Zone Overview",
        "📈 Speed vs Volume Correlation",
        "⏱️ Trends Over Time",
        "🗺️ Zone Map",
        "📋 Raw Telemetry Explorer",
    ])

    with tab1:
        st.subheader("Zone Performance Breakdown")

        zone_summary = df.groupby('zone_name').agg({
            'vehicle_count': 'mean',
            'avg_speed_kmh': 'mean'
        }).reset_index()

        col_left, col_right = st.columns(2)

        with col_left:
            fig_vol = px.bar(
                zone_summary,
                x="zone_name",
                y="vehicle_count",
                title="<b>Average Traffic Volume by Zone</b>",
                labels={"zone_name": "Zone", "vehicle_count": "Avg Vehicles"},
                color="zone_name",
                color_discrete_map=ZONE_COLORS,
                template="plotly_dark"
            )
            fig_vol.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_vol, use_container_width=True)

        with col_right:
            fig_speed = px.bar(
                zone_summary,
                x="zone_name",
                y="avg_speed_kmh",
                title="<b>Average Transit Speed (km/h) by Zone</b>",
                labels={"zone_name": "Zone", "avg_speed_kmh": "Avg Speed (km/h)"},
                color="zone_name",
                color_discrete_map=ZONE_COLORS,
                template="plotly_dark"
            )
            fig_speed.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_speed, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Congestion Status Distribution")
        status_counts = df.groupby(['zone_name', 'congestion_status']).size().reset_index(name='count')
        fig_status = px.bar(
            status_counts,
            x="zone_name", y="count", color="congestion_status",
            color_discrete_map=STATUS_COLORS,
            barmode="stack",
            title="<b>Congestion Status Mix by Zone</b>",
            labels={"zone_name": "Zone", "count": "Log Count", "congestion_status": "Status"},
            template="plotly_dark"
        )
        fig_status.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with tab2:
        st.subheader("Congestion & Speed Correlation")
        fig_scatter = px.scatter(
            df,
            x="vehicle_count",
            y="avg_speed_kmh",
            color="zone_name",
            size="vehicle_count",
            hover_data=["timestamp", "congestion_status"],
            title="<b>Vehicle Density vs Speed Distribution</b>",
            labels={"vehicle_count": "Vehicle Count", "avg_speed_kmh": "Speed (km/h)", "zone_name": "Zone"},
            color_discrete_map=ZONE_COLORS,
            template="plotly_dark"
        )
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Speed should trend downward as vehicle count rises — that inverse relationship is the core signal this pipeline is built to surface.")

    with tab3:
        st.subheader("Trends Across Pipeline Runs")
        batch_trend = df.groupby(['timestamp', 'zone_name']).agg({
            'vehicle_count': 'mean',
            'avg_speed_kmh': 'mean'
        }).reset_index().sort_values('timestamp')

        fig_trend_speed = px.line(
            batch_trend, x="timestamp", y="avg_speed_kmh", color="zone_name",
            markers=True, color_discrete_map=ZONE_COLORS,
            title="<b>Average Speed Across Ingestion Runs</b>",
            labels={"timestamp": "Pipeline Run", "avg_speed_kmh": "Avg Speed (km/h)", "zone_name": "Zone"},
            template="plotly_dark"
        )
        fig_trend_speed.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_trend_speed, use_container_width=True)

        fig_trend_vol = px.line(
            batch_trend, x="timestamp", y="vehicle_count", color="zone_name",
            markers=True, color_discrete_map=ZONE_COLORS,
            title="<b>Vehicle Count Across Ingestion Runs</b>",
            labels={"timestamp": "Pipeline Run", "vehicle_count": "Avg Vehicles", "zone_name": "Zone"},
            template="plotly_dark"
        )
        fig_trend_vol.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_trend_vol, use_container_width=True)

    with tab4:
        st.subheader("Live Zone Map")
        latest_snapshot = df.sort_values('timestamp').groupby('zone_name').tail(1).copy()
        latest_snapshot['lat'] = latest_snapshot['zone_name'].map(lambda z: ZONE_COORDS.get(z, {}).get('lat'))
        latest_snapshot['lon'] = latest_snapshot['zone_name'].map(lambda z: ZONE_COORDS.get(z, {}).get('lon'))
        latest_snapshot = latest_snapshot.dropna(subset=['lat', 'lon'])

        if not latest_snapshot.empty:
            fig_map = px.scatter_mapbox(
                latest_snapshot,
                lat="lat", lon="lon",
                color="congestion_status",
                size="vehicle_count",
                hover_name="zone_name",
                hover_data=["avg_speed_kmh", "vehicle_count"],
                color_discrete_map=STATUS_COLORS,
                zoom=10, height=480,
                mapbox_style="carto-darkmatter",
                title="<b>Zone Status (most recent reading per zone)</b>"
            )
            fig_map.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_map, use_container_width=True)
            st.caption("Zone coordinates are approximate placements for this demo dataset.")
        else:
            st.info("No zone data available for the current filter.")

    with tab5:
        st.subheader("Live Telemetry Fact Table")

        def highlight_status(val):
            color = STATUS_COLORS.get(val, "#C9D1D9")
            return f"color: {color}; font-weight: 600;"

        styled_df = df.style.applymap(highlight_status, subset=['congestion_status'])
        st.dataframe(styled_df, use_container_width=True, height=400)

except Exception as e:
    st.error("Something went wrong loading telemetry data. The dashboard will retry on the next refresh.")
    with st.expander("Technical details (for debugging)"):
        st.code(str(e))
