import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

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
    /* Card Container Styling */
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

# 3. Database Connection
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", ""))

@st.cache_data(ttl=15)
def fetch_data(query):
    if not DATABASE_URL:
        st.error("⚠️ DATABASE_URL secret is not configured.")
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
    # Fetch Raw Fact Data
    raw_df = fetch_data("SELECT * FROM raw_traffic_fact ORDER BY timestamp DESC;")

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
    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Executive Metric Cards
    total_records = len(df)
    avg_density = df['vehicle_count'].mean() if not df.empty else 0
    avg_speed = df['avg_speed_kmh'].mean() if not df.empty else 0

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
                <div class="metric-sub">Network Speed</div>
            </div>
        ''', unsafe_allow_html=True)
    with m4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">ACTIVE ZONES</div>
                <div class="metric-value" style="color: #FFA657;">{len(selected_zones)}</div>
                <div class="metric-sub">Zones Selected</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 7. Tabbed Navigation View
    tab1, tab2, tab3 = st.tabs(["📊 Zone Overview", "📈 Speed vs Volume Correlation", "📋 Raw Telemetry Explorer"])

    with tab1:
        st.subheader("Zone Performance Breakdown")
        
        # Aggregate stats by zone
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
                color="vehicle_count",
                color_continuous_scale="Reds",
                template="plotly_dark"
            )
            fig_vol.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_vol, use_container_width=True)

        with col_right:
            fig_speed = px.bar(
                zone_summary,
                x="zone_name",
                y="avg_speed_kmh",
                title="<b>Average Transit Speed (km/h) by Zone</b>",
                labels={"zone_name": "Zone", "avg_speed_kmh": "Avg Speed (km/h)"},
                color="avg_speed_kmh",
                color_continuous_scale="Viridis",
                template="plotly_dark"
            )
            fig_speed.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_speed, use_container_width=True)

    with tab2:
        st.subheader("Congestion & Speed Correlation")
        fig_scatter = px.scatter(
            df,
            x="vehicle_count",
            y="avg_speed_kmh",
            color="zone_name",
            size="vehicle_count",
            hover_data=["timestamp"],
            title="<b>Vehicle Density vs Speed Distribution</b>",
            labels={"vehicle_count": "Vehicle Count", "avg_speed_kmh": "Speed (km/h)", "zone_name": "Zone"},
            template="plotly_dark"
        )
        fig_scatter.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Live Telemetry Fact Table")
        st.dataframe(df, use_container_width=True, height=400)

except Exception as e:
        st.error(f"Database Query Error: {e}")
