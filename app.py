import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import folium
from streamlit_folium import st_folium
import os
import traceback

# 1. Page Configuration
st.set_page_config(
    page_title="Urban Transit Telemetry Platform",
    page_icon=None,  # no emoji/icon — plain professional tab title
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS — Neon Black/Blue Theme, no emoji iconography
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
        background-color: #05070D;
    }
    .stApp {
        background: radial-gradient(circle at 15% 0%, #0A1830 0%, #05070D 45%);
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 0.5px;
    }
    h1 { text-shadow: 0 0 18px rgba(0, 217, 255, 0.45); }

    [data-testid="stHeaderActionElements"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    .metric-card {
        background: linear-gradient(160deg, #0B1220 0%, #060A14 100%);
        border: 1px solid rgba(0, 217, 255, 0.35);
        border-radius: 14px;
        padding: 22px 20px;
        text-align: center;
        box-shadow: 0 0 18px rgba(0, 145, 255, 0.15), inset 0 0 20px rgba(0, 217, 255, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px) scale(1.01);
        border-color: #00D9FF;
        box-shadow: 0 0 28px rgba(0, 217, 255, 0.4);
    }
    .metric-title {
        color: #6E86A8; font-size: 0.78rem; font-weight: 700;
        letter-spacing: 1.6px; margin-bottom: 10px; text-transform: uppercase;
    }
    .metric-value {
        font-family: 'Orbitron', sans-serif; color: #00D9FF;
        font-size: 1.9rem; font-weight: 800; text-shadow: 0 0 14px rgba(0, 217, 255, 0.55);
    }
    .metric-sub { color: #39E6A6; font-size: 0.78rem; margin-top: 8px; letter-spacing: 0.3px; }

    .section-divider {
        height: 1px; background: linear-gradient(90deg, #00D9FF66, transparent 70%);
        margin: 28px 0 18px 0; box-shadow: 0 0 8px rgba(0, 217, 255, 0.25);
    }

    /* --- Control Panel (sidebar) --- */
    section[data-testid="stSidebar"] {
        background-color: #050810;
        border-right: 1px solid rgba(0, 217, 255, 0.2);
        min-width: 320px !important;
        width: 320px !important;
    }
    .sidebar-brand {
        display: flex; align-items: center; gap: 10px;
        padding: 4px 0 14px 0; margin-bottom: 10px;
        border-bottom: 1px solid rgba(0, 217, 255, 0.15);
    }
    .sidebar-brand-mark {
        width: 30px; height: 30px; border-radius: 7px;
        background: linear-gradient(145deg, #00D9FF, #2979FF);
        box-shadow: 0 0 12px rgba(0, 217, 255, 0.5);
        display: flex; align-items: center; justify-content: center;
        font-family: 'Orbitron', sans-serif; font-weight: 800; color: #05070D; font-size: 0.85rem;
    }
    .sidebar-brand-text {
        font-family: 'Orbitron', sans-serif; color: #00D9FF;
        font-size: 0.92rem; font-weight: 700; letter-spacing: 0.5px;
    }
    .status-pill {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(57, 230, 166, 0.08);
        border: 1px solid rgba(57, 230, 166, 0.35);
        border-radius: 20px; padding: 6px 14px; margin: 6px 0 16px 0;
        font-size: 0.78rem; color: #39E6A6; font-weight: 600; letter-spacing: 0.5px;
    }
    .status-dot {
        width: 8px; height: 8px; border-radius: 50%; background: #39E6A6;
        box-shadow: 0 0 8px #39E6A6; animation: pulse 1.8s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.35; } 100% { opacity: 1; } }
    .sidebar-section-label {
        color: #6E86A8; font-size: 0.72rem; font-weight: 700;
        letter-spacing: 1.4px; text-transform: uppercase; margin: 18px 0 8px 0;
    }

    /* --- Tabs, restyled as a clean professional nav bar --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; border-bottom: 1px solid rgba(0, 217, 255, 0.15);
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600; letter-spacing: 0.3px; color: #6E86A8;
    }
    .stTabs [aria-selected="true"] {
        color: #00D9FF !important; border-bottom-color: #00D9FF !important;
    }

    /* --- Buttons (Accept/Reject, etc.) themed to match --- */
    .stButton > button {
        background-color: transparent;
        border: 1px solid rgba(0, 217, 255, 0.4);
        color: #C9D6E8;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #00D9FF;
        color: #00D9FF;
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
    }

    /* --- Multiselect chip styling --- */
    span[data-baseweb="tag"] {
        background-color: rgba(0, 217, 255, 0.12) !important;
        border: 1px solid rgba(0, 217, 255, 0.4) !important;
    }

    .stMarkdown, .stCaption { color: #C9D6E8; }

    /* Architecture diagram nodes — numbered badges instead of emoji icons */
    .arch-flow {
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 8px; margin: 10px 0 6px 0;
    }
    .arch-node {
        flex: 1; min-width: 150px;
        background: linear-gradient(160deg, #0B1220 0%, #060A14 100%);
        border: 1px solid rgba(0, 217, 255, 0.3);
        border-radius: 10px; padding: 14px 12px; text-align: center;
        box-shadow: 0 0 12px rgba(0, 145, 255, 0.12);
    }
    .arch-node-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 24px; height: 24px; border-radius: 50%;
        background: rgba(0, 217, 255, 0.12); border: 1px solid rgba(0, 217, 255, 0.5);
        color: #00D9FF; font-family: 'Orbitron', sans-serif; font-size: 0.7rem; font-weight: 800;
    }
    .arch-node-title {
        font-family: 'Orbitron', sans-serif; color: #00D9FF;
        font-size: 0.76rem; font-weight: 700; margin: 8px 0 4px 0;
    }
    .arch-node-sub { color: #6E86A8; font-size: 0.68rem; line-height: 1.3; }
    .arch-arrow { color: #00D9FF; font-size: 1.2rem; flex: 0 0 auto; opacity: 0.7; }

    /* Cookie consent banner */
    .cookie-text { color: #C9D6E8; font-size: 0.85rem; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# Neon black/blue palette — one fixed color per zone, reused across every chart
ZONE_COLORS = {
    "Central Junction": "#00D9FF",
    "Tech Park Belt": "#39E6A6",
    "Outer Ring Road": "#7C4DFF",
    "Airport Corridor": "#2979FF",
    "Silk Board Junction": "#FF6EC7",
    "Whitefield Corridor": "#00FFC6",
    "Electronic City Link": "#5B8DEF",
    "Hebbal Flyover": "#B388FF",
}
STATUS_COLORS = {
    "HEAVY_CONGESTION": "#FF3860",
    "MODERATE_FLOW": "#FFB300",
    "SMOOTH_TRAFFIC": "#39E6A6",
}
DEFAULT_ZONE_COORDS = {
    "Central Junction": {"lat": 12.9716, "lon": 77.5946},
    "Tech Park Belt": {"lat": 12.9352, "lon": 77.6245},
    "Outer Ring Road": {"lat": 12.9698, "lon": 77.7500},
    "Airport Corridor": {"lat": 13.1986, "lon": 77.7066},
    "Silk Board Junction": {"lat": 12.9172, "lon": 77.6228},
    "Whitefield Corridor": {"lat": 12.9750, "lon": 77.7480},
    "Electronic City Link": {"lat": 12.8452, "lon": 77.6602},
    "Hebbal Flyover": {"lat": 13.0358, "lon": 77.5970},
}

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Rajdhani, sans-serif", color="#C9D6E8", size=13),
    title_font=dict(size=16, family="Orbitron, sans-serif", color="#00D9FF"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
CHART_MARGIN = dict(t=55, l=10, r=10, b=10)


def style_chart(fig, is_3d=False, **extra_layout):
    layout = {**BASE_LAYOUT, "margin": CHART_MARGIN}
    layout.update(extra_layout)
    fig.update_layout(**layout)
    if not is_3d:
        fig.update_xaxes(gridcolor="rgba(0,217,255,0.08)", zerolinecolor="rgba(0,217,255,0.15)")
        fig.update_yaxes(gridcolor="rgba(0,217,255,0.08)", zerolinecolor="rgba(0,217,255,0.15)")
    return fig


def style_dataframe(df, subset_col, color_map):
    def highlight(val):
        color = color_map.get(val, "#C9D6E8")
        return f"color: {color}; font-weight: 600;"
    styler = df.style
    if hasattr(styler, "map"):
        return styler.map(highlight, subset=[subset_col])
    return styler.applymap(highlight, subset=[subset_col])


def render_tab_safely(render_fn):
    try:
        render_fn()
    except Exception as tab_error:
        st.error("This view couldn't be rendered.")
        with st.expander("Technical details (for debugging)"):
            st.code(f"{type(tab_error).__name__}: {tab_error}\n\n{traceback.format_exc()}")


# 3. Cookie consent banner — shown once per session, purely a UI convention for this
# demo (the app sets no tracking cookies), included because a real production
# dashboard would have one.
if "cookie_choice" not in st.session_state:
    st.session_state.cookie_choice = None

if st.session_state.cookie_choice is None:
    with st.container(border=True):
        st.markdown(
            '<div class="cookie-text">This dashboard uses only session-level state to '
            'manage filters and preferences while you browse. No personal data is collected '
            'or shared with third parties.</div>',
            unsafe_allow_html=True
        )
        spacer, col_reject, col_accept = st.columns([6, 1, 1])
        with col_reject:
            if st.button("Reject", key="cookie_reject", use_container_width=True):
                st.session_state.cookie_choice = "rejected"
                st.rerun()
        with col_accept:
            if st.button("Accept", key="cookie_accept", use_container_width=True):
                st.session_state.cookie_choice = "accepted"
                st.rerun()

# 4. Database Connection
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv("DATABASE_URL", ""))

@st.cache_data(ttl=15)
def fetch_data(query):
    if not DATABASE_URL:
        st.error("DATABASE_URL secret is not configured.")
        st.stop()
    conn = psycopg2.connect(DATABASE_URL)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def fetch_zone_coords():
    try:
        coords_df = fetch_data("SELECT zone_name, latitude, longitude FROM zone_dimension;")
        coords = {
            row["zone_name"]: {"lat": row["latitude"], "lon": row["longitude"]}
            for _, row in coords_df.iterrows()
        }
        return coords if coords else DEFAULT_ZONE_COORDS
    except Exception:
        return DEFAULT_ZONE_COORDS


# 5. Sidebar — Control Panel
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">UT</div>
            <span class="sidebar-brand-text">CONTROL PANEL</span>
        </div>
        <div class="status-pill"><span class="status-dot"></span> PIPELINE ACTIVE</div>
    """, unsafe_allow_html=True)

try:
    raw_df = fetch_data("SELECT * FROM raw_traffic_fact ORDER BY timestamp DESC, id DESC;")
    raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])
    raw_df["hour_of_day"] = raw_df["timestamp"].dt.hour
except Exception as e:
    st.error("Couldn't load telemetry data from the warehouse. The dashboard will retry on the next refresh.")
    with st.expander("Technical details (for debugging)"):
        st.code(f"{type(e).__name__}: {e}")
    st.stop()

all_zones = sorted(raw_df['zone_name'].dropna().unique().tolist())

with st.sidebar:
    st.markdown('<div class="sidebar-section-label">Filter Monitored Zones</div>', unsafe_allow_html=True)
    selected_zones = st.multiselect("Zones", all_zones, default=all_zones, label_visibility="collapsed")

    st.markdown('<div class="sidebar-section-label">Data Source</div>', unsafe_allow_html=True)
    st.info("Auto-refreshed from the Neon PostgreSQL data warehouse every 15 seconds.", icon=None)

    st.markdown('<div class="sidebar-section-label">Note</div>', unsafe_allow_html=True)
    st.caption("Telemetry values are simulated with realistic rush-hour patterns. This project demonstrates a real, automated ETL pipeline, not a live sensor feed.")

df = raw_df[raw_df['zone_name'].isin(selected_zones)].copy() if selected_zones else raw_df.copy()

# 6. Header Section
st.title("Urban Transit Telemetry & Analytics Platform")
st.caption("Real-Time ETL Data Pipeline · Cloud Data Warehouse (Neon PostgreSQL) · Automated GitHub Actions Ingestion")

with st.expander("About this project / Architecture", expanded=False):
    st.markdown("""
        <div class="arch-flow">
            <div class="arch-node">
                <div class="arch-node-badge">1</div>
                <div class="arch-node-title">GITHUB ACTIONS</div>
                <div class="arch-node-sub">Hourly cron trigger<br>runs etl_pipeline.py</div>
            </div>
            <div class="arch-arrow">&#8594;</div>
            <div class="arch-node">
                <div class="arch-node-badge">2</div>
                <div class="arch-node-title">EXTRACT / TRANSFORM</div>
                <div class="arch-node-sub">Generates telemetry,<br>derives congestion status</div>
            </div>
            <div class="arch-arrow">&#8594;</div>
            <div class="arch-node">
                <div class="arch-node-badge">3</div>
                <div class="arch-node-title">NEON POSTGRESQL</div>
                <div class="arch-node-sub">Fact table + zone<br>dimension table</div>
            </div>
            <div class="arch-arrow">&#8594;</div>
            <div class="arch-node">
                <div class="arch-node-badge">4</div>
                <div class="arch-node-title">STREAMLIT APP</div>
                <div class="arch-node-sub">Live queries,<br>renders this dashboard</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    **Stack:** Python, GitHub Actions, Neon (serverless Postgres), Streamlit, Plotly, Folium

    **Data note:** telemetry values are simulated with time-of-day rush-hour patterns
    (heavier 8-10am / 5-8pm, lighter overnight) rather than a live sensor feed. The
    pipeline automation, storage, and serving layer are all genuinely live and running.

    **Source:** [github.com/viniska13/traffic-etl-pipeline](https://github.com/viniska13/traffic-etl-pipeline)
    """)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# 7. Executive Metric Cards
total_records = len(df)
avg_density = df['vehicle_count'].mean() if not df.empty else 0
avg_speed = df['avg_speed_kmh'].mean() if not df.empty else 0

last_sync = raw_df['timestamp'].max() if not raw_df.empty else None
if last_sync is not None:
    minutes_ago = max(0, int((pd.Timestamp.now() - last_sync).total_seconds() // 60))
    freshness_label = f"{minutes_ago} min ago" if minutes_ago >= 1 else "just now"
else:
    freshness_label = "N/A"

batch_times = sorted(df['timestamp'].unique()) if not df.empty else []
speed_delta = None
if len(batch_times) >= 2:
    last_batch_speed = df[df['timestamp'] == batch_times[-1]]['avg_speed_kmh'].mean()
    prev_batch_speed = df[df['timestamp'] == batch_times[-2]]['avg_speed_kmh'].mean()
    speed_delta = last_batch_speed - prev_batch_speed

if speed_delta is None:
    delta_html = "Network Speed"
elif speed_delta >= 0:
    delta_html = f"UP {speed_delta:.1f} km/h vs last sync"
else:
    delta_html = f"DOWN {abs(speed_delta):.1f} km/h vs last sync"

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
            <div class="metric-value">{avg_speed:.1f} <span style="font-size: 1rem;">km/h</span></div>
            <div class="metric-sub">{delta_html}</div>
        </div>
    ''', unsafe_allow_html=True)
with m4:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-title">LAST SYNCED</div>
            <div class="metric-value" style="font-size: 1.3rem;">{freshness_label}</div>
            <div class="metric-sub">From GitHub Actions cron</div>
        </div>
    ''', unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# 8. Tabbed Navigation View — plain text labels, each isolated via render_tab_safely
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Zone Overview",
    "Speed vs Volume Correlation",
    "Trends Over Time",
    "3D Density Explorer",
    "Zone Map",
    "Raw Telemetry Explorer",
])


def render_zone_overview():
    st.subheader("Zone Performance Breakdown")
    zone_summary = df.groupby('zone_name').agg({
        'vehicle_count': 'mean', 'avg_speed_kmh': 'mean'
    }).reset_index()

    col_left, col_right = st.columns(2)
    with col_left:
        fig_vol = px.bar(
            zone_summary, x="zone_name", y="vehicle_count",
            title="<b>Average Traffic Volume by Zone</b>",
            labels={"zone_name": "Zone", "vehicle_count": "Avg Vehicles"},
            color="zone_name", color_discrete_map=ZONE_COLORS, template="plotly_dark"
        )
        style_chart(fig_vol, showlegend=False)
        fig_vol.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_vol, use_container_width=True)
    with col_right:
        fig_speed = px.bar(
            zone_summary, x="zone_name", y="avg_speed_kmh",
            title="<b>Average Transit Speed (km/h) by Zone</b>",
            labels={"zone_name": "Zone", "avg_speed_kmh": "Avg Speed (km/h)"},
            color="zone_name", color_discrete_map=ZONE_COLORS, template="plotly_dark"
        )
        style_chart(fig_speed, showlegend=False)
        fig_speed.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_speed, use_container_width=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("Congestion Status Distribution")
    status_counts = df.groupby(['zone_name', 'congestion_status']).size().reset_index(name='count')
    fig_status = px.bar(
        status_counts, x="zone_name", y="count", color="congestion_status",
        color_discrete_map=STATUS_COLORS, barmode="stack",
        title="<b>Congestion Status Mix by Zone</b>",
        labels={"zone_name": "Zone", "count": "Log Count", "congestion_status": "Status"},
        template="plotly_dark"
    )
    style_chart(fig_status)
    fig_status.update_xaxes(tickangle=-30)
    st.plotly_chart(fig_status, use_container_width=True)


def render_correlation():
    st.subheader("Congestion & Speed Correlation")
    fig_scatter = px.scatter(
        df, x="vehicle_count", y="avg_speed_kmh", color="zone_name", size="vehicle_count",
        hover_data=["timestamp", "congestion_status"],
        title="<b>Vehicle Density vs Speed Distribution</b>",
        labels={"vehicle_count": "Vehicle Count", "avg_speed_kmh": "Speed (km/h)", "zone_name": "Zone"},
        color_discrete_map=ZONE_COLORS, template="plotly_dark"
    )
    style_chart(fig_scatter)
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("Speed trends downward as vehicle count rises — that inverse relationship is the core signal this pipeline is built to surface.")


def render_trends():
    st.subheader("Trends Across Pipeline Runs")
    batch_trend = df.groupby(['timestamp', 'zone_name']).agg({
        'vehicle_count': 'mean', 'avg_speed_kmh': 'mean'
    }).reset_index().sort_values('timestamp')

    fig_trend_speed = px.line(
        batch_trend, x="timestamp", y="avg_speed_kmh", color="zone_name",
        markers=True, color_discrete_map=ZONE_COLORS,
        title="<b>Average Speed Across Ingestion Runs</b>",
        labels={"timestamp": "Pipeline Run", "avg_speed_kmh": "Avg Speed (km/h)", "zone_name": "Zone"},
        template="plotly_dark"
    )
    style_chart(fig_trend_speed)
    st.plotly_chart(fig_trend_speed, use_container_width=True)

    fig_trend_vol = px.line(
        batch_trend, x="timestamp", y="vehicle_count", color="zone_name",
        markers=True, color_discrete_map=ZONE_COLORS,
        title="<b>Vehicle Count Across Ingestion Runs</b>",
        labels={"timestamp": "Pipeline Run", "vehicle_count": "Avg Vehicles", "zone_name": "Zone"},
        template="plotly_dark"
    )
    style_chart(fig_trend_vol)
    st.plotly_chart(fig_trend_vol, use_container_width=True)


def render_3d():
    st.subheader("3D Density Explorer")
    st.caption("Vehicle count, speed, and hour-of-day — rotate and zoom to spot patterns a flat chart can't show.")
    fig_3d = px.scatter_3d(
        df, x="vehicle_count", y="avg_speed_kmh", z="hour_of_day",
        color="zone_name", size="vehicle_count", opacity=0.85,
        color_discrete_map=ZONE_COLORS,
        labels={
            "vehicle_count": "Vehicle Count", "avg_speed_kmh": "Speed (km/h)",
            "hour_of_day": "Hour of Day", "zone_name": "Zone",
        },
        title="<b>Density, Speed, Time-of-Day</b>",
        template="plotly_dark"
    )
    fig_3d.update_scenes(
        xaxis_backgroundcolor="rgba(0,0,0,0)",
        yaxis_backgroundcolor="rgba(0,0,0,0)",
        zaxis_backgroundcolor="rgba(0,0,0,0)",
        xaxis_gridcolor="rgba(0,217,255,0.12)",
        yaxis_gridcolor="rgba(0,217,255,0.12)",
        zaxis_gridcolor="rgba(0,217,255,0.12)",
    )
    style_chart(fig_3d, is_3d=True, height=560, margin=dict(t=55, l=0, r=0, b=0))
    st.plotly_chart(fig_3d, use_container_width=True)


def render_map():
    st.subheader("Live Zone Map")
    zone_coords = fetch_zone_coords()

    latest_snapshot = df.sort_values('timestamp').groupby('zone_name').tail(1).copy()
    latest_snapshot['lat'] = latest_snapshot['zone_name'].map(lambda z: zone_coords.get(z, {}).get('lat'))
    latest_snapshot['lon'] = latest_snapshot['zone_name'].map(lambda z: zone_coords.get(z, {}).get('lon'))
    latest_snapshot = latest_snapshot.dropna(subset=['lat', 'lon'])

    if latest_snapshot.empty:
        st.info("No zone data available for the current filter.")
        return

    center_lat = latest_snapshot['lat'].mean()
    center_lon = latest_snapshot['lon'].mean()

    # Plain OpenStreetMap tiles — the original, always-free, no-API-key-ever tile
    # source (unlike CartoDB's basemap styles, which now require registration and
    # broke this exact map once already). A CSS filter darkens it to match the theme.
    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    dark_filter_css = """
    <style>
    .leaflet-tile-pane {
        filter: invert(1) hue-rotate(200deg) brightness(0.85) contrast(0.9) saturate(0.6);
    }
    .leaflet-container { background: #05070D !important; }
    </style>
    """
    fmap.get_root().html.add_child(folium.Element(dark_filter_css))

    for _, row in latest_snapshot.iterrows():
        color = STATUS_COLORS.get(row['congestion_status'], "#C9D6E8")
        radius = 8 + (row['vehicle_count'] / 1200) * 14
        popup_html = (
            f"<b>{row['zone_name']}</b><br>"
            f"Vehicles: {row['vehicle_count']}<br>"
            f"Speed: {row['avg_speed_kmh']:.1f} km/h<br>"
            f"Status: {row['congestion_status']}"
        )
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=radius,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=row['zone_name'],
        ).add_to(fmap)

    bounds = [[latest_snapshot['lat'].min(), latest_snapshot['lon'].min()],
              [latest_snapshot['lat'].max(), latest_snapshot['lon'].max()]]
    fmap.fit_bounds(bounds, padding=(40, 40))

    st_folium(fmap, use_container_width=True, height=520, returned_objects=[])
    st.caption("Zone coordinates are sourced from the zone_dimension table in Neon. Positions are approximate placements for this demo dataset.")


def render_raw_table():
    st.subheader("Live Telemetry Fact Table")
    styled_df = style_dataframe(df, "congestion_status", STATUS_COLORS)
    st.dataframe(styled_df, use_container_width=True, height=400)


with tab1:
    render_tab_safely(render_zone_overview)
with tab2:
    render_tab_safely(render_correlation)
with tab3:
    render_tab_safely(render_trends)
with tab4:
    render_tab_safely(render_3d)
with tab5:
    render_tab_safely(render_map)
with tab6:
    render_tab_safely(render_raw_table)
