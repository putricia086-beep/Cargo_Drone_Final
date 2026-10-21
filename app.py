import io, json, random, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent
DB = ROOT / "cargo_drone.db"
MODEL_CANDIDATES = [ROOT / "models" / "best.pt", ROOT / "runs" / "cargo" / "yolov8n_helipad" / "weights" / "best.pt"]

st.set_page_config(page_title="CARGO | Ground Station", page_icon="🛰️", layout="wide")
st.markdown(
    """
    <style>
        :root {
            --bg: #07111F;
            --bg-strong: #050B14;
            --sidebar: #091827;
            --panel: #0E2033;
            --card: #12283D;
            --border: #243B53;
            --primary: #3B82F6;
            --cyan: #22D3EE;
            --green: #22C55E;
            --amber: #F59E0B;
            --red: #EF4444;
            --text: #F1F5F9;
            --muted: #94A3B8;
        }

        .stApp {
            background: radial-gradient(circle at top left, rgba(59,130,246,0.18), transparent 28%),
                        linear-gradient(180deg, #081827 0%, #07111F 40%, #050b14 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.3rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1600px;
        }

        section[data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--border);
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.02);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem !important;
        }

        h1, h2, h3, h4, p, label, div, span, .stMarkdown {
            color: var(--text);
        }

        .brand-block {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.35rem 0.25rem 1rem;
            margin-bottom: 0.5rem;
        }

        .brand-mark {
            width: 2.7rem;
            height: 2.7rem;
            border-radius: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(34,211,238,0.16));
            border: 1px solid rgba(59,130,246,0.5);
            color: var(--cyan);
            font-weight: 800;
            letter-spacing: 0.08em;
        }

        .brand-title {
            font-size: 0.96rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            line-height: 1.2;
            color: var(--text);
        }

        .brand-subtitle {
            font-size: 0.64rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--muted);
            margin-top: 0.18rem;
        }

        .sidebar-section-title {
            font-size: 0.68rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--muted);
            margin: 1rem 0 0.5rem;
        }

        .signal-status {
            margin-top: 0.8rem;
            padding: 0.7rem 0.8rem;
            border: 1px solid var(--border);
            border-radius: 0.9rem;
            background: rgba(14, 32, 51, 0.75);
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .signal-dot {
            width: 0.52rem;
            height: 0.52rem;
            border-radius: 50%;
            display: inline-block;
            background: var(--green);
            box-shadow: 0 0 0 4px rgba(34,197,94,0.12);
        }

        .signal-status.offline .signal-dot { background: var(--red); box-shadow: 0 0 0 4px rgba(239,68,68,0.12); }
        .signal-status.offline { border-color: rgba(239,68,68,0.35); }

        .stRadio {
            margin-top: 0.25rem;
        }

        .stRadio > div {
            gap: 0.35rem;
        }

        .stRadio label {
            background: rgba(18, 40, 61, 0.7);
            border: 1px solid rgba(36, 59, 83, 0.9);
            border-radius: 0.8rem;
            padding: 0.78rem 0.85rem;
            margin-bottom: 0.38rem;
            transition: all 0.2s ease;
        }

        .stRadio label:hover {
            border-color: rgba(59,130,246,0.6);
            background: rgba(21, 50, 72, 0.95);
        }

        .stRadio [data-baseweb="radio"] > div {
            background: transparent;
        }

        .stRadio [data-baseweb="radio"] span {
            color: var(--text);
        }

        .stButton > button {
            border: 1px solid rgba(59,130,246,0.3);
            border-radius: 0.9rem;
            background: linear-gradient(180deg, rgba(59,130,246,0.18), rgba(14,32,51,0.95));
            color: var(--text);
            font-weight: 600;
            letter-spacing: 0.01em;
            padding: 0.72rem 0.8rem;
            min-height: 2.8rem;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            border-color: rgba(34,211,238,0.7);
            box-shadow: 0 0 0 0.08rem rgba(34,211,238,0.2), 0 12px 18px rgba(2, 6, 23, 0.18);
        }

        .stButton > button:focus {
            box-shadow: 0 0 0 0.12rem rgba(59,130,246,0.35);
        }

        .primary-button {
            background: linear-gradient(135deg, rgba(59,130,246,0.3), rgba(34,211,238,0.17)) !important;
        }

        .warning-button {
            border-color: rgba(245,158,11,0.38) !important;
            background: linear-gradient(180deg, rgba(245,158,11,0.16), rgba(14,32,51,0.98)) !important;
        }

        .success-button {
            border-color: rgba(34,197,94,0.36) !important;
            background: linear-gradient(180deg, rgba(34,197,94,0.16), rgba(14,32,51,0.96)) !important;
        }

        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.2rem 1.4rem 1rem;
            border: 1px solid var(--border);
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(18,40,61,0.94), rgba(9,24,39,0.94));
            margin: 0 0 1.15rem;
            box-shadow: 0 12px 28px rgba(2,6,23,0.2);
        }

        .eyebrow {
            font-size: 0.68rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--cyan);
            margin-bottom: 0.35rem;
        }

        .app-header h1 {
            margin: 0;
            font-size: clamp(1.7rem, 2vw, 2.55rem);
            line-height: 1.1;
            letter-spacing: -0.04em;
        }

        .app-header-sub {
            color: var(--muted);
            font-size: 0.87rem;
            max-width: 52rem;
            margin-top: 0.35rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 10.5rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            border: 1px solid var(--border);
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            background: rgba(14,32,51,0.8);
        }

        .status-online {
            color: var(--green);
            border-color: rgba(34,197,94,0.38);
            background: rgba(34,197,94,0.08);
        }

        .status-offline {
            color: var(--red);
            border-color: rgba(239,68,68,0.38);
            background: rgba(239,68,68,0.08);
        }

        .status-warning {
            color: var(--amber);
            border-color: rgba(245,158,11,0.38);
            background: rgba(245,158,11,0.08);
        }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.5rem 0 1rem;
        }

        .page-header h2 {
            margin: 0;
            font-size: clamp(1.2rem, 1.8vw, 1.7rem);
            letter-spacing: -0.03em;
        }

        .page-subtitle {
            color: var(--muted);
            margin: -0.3rem 0 1.2rem;
            font-size: 0.9rem;
        }

        .panel {
            background: rgba(14,32,51,0.9);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 22px rgba(2,6,23,0.15);
        }

        .metric-card {
            background: linear-gradient(180deg, rgba(18,40,61,0.9), rgba(11,28,40,0.9));
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1rem 1.1rem;
            height: 100%;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(18,40,61,0.92), rgba(11,28,40,0.92));
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 18px rgba(2,6,23,0.12);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        div[data-testid="stMetricValue"] {
            color: var(--cyan) !important;
            font-weight: 700;
            font-size: clamp(1.1rem, 1.6vw, 1.6rem) !important;
        }

        div[data-testid="stMetricDelta"] {
            color: var(--muted) !important;
        }

        .info-callout {
            border-left: 4px solid var(--primary);
            background: rgba(59,130,246,0.1);
            border-radius: 0.9rem;
            padding: 0.9rem 1rem;
            color: var(--text);
        }

        .warning-callout {
            border-left: 4px solid var(--amber);
            background: rgba(245,158,11,0.08);
            border-radius: 0.9rem;
            padding: 0.9rem 1rem;
            color: var(--text);
        }

        .error-callout {
            border-left: 4px solid var(--red);
            background: rgba(239,68,68,0.08);
            border-radius: 0.9rem;
            padding: 0.9rem 1rem;
            color: var(--text);
        }

        .system-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(180px, 1fr));
            gap: 1rem;
            margin: 1rem 0 1.5rem;
        }

        .arch-node {
            background: linear-gradient(180deg, rgba(18,40,61,0.96), rgba(12,31,47,0.96));
            border: 1px solid var(--border);
            border-radius: 1rem;
            min-height: 5.8rem;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 0.9rem 0.8rem;
            color: var(--text);
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        .arch-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--cyan);
            font-size: 1.8rem;
            opacity: 0.8;
        }

        .arch-row {
            display: grid;
            grid-template-columns: 1fr 30px 1fr 30px 1fr;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 0.85rem;
        }

        .arch-row.single {
            grid-template-columns: 1fr;
            max-width: 21rem;
            margin: 0 auto 0.75rem;
        }

        .arch-row.mid {
            grid-template-columns: 1fr 30px 1fr 30px 1fr;
        }

        .arch-row .arch-node:nth-child(1) { border-color: rgba(59,130,246,0.52); }
        .arch-row .arch-node:nth-child(3) { border-color: rgba(34,211,238,0.52); }
        .arch-row .arch-node:nth-child(5) { border-color: rgba(34,197,94,0.42); }

        .compact-panel {
            border: 1px solid var(--border);
            border-radius: 0.9rem;
            background: rgba(18,40,61,0.7);
            padding: 0.8rem 0.9rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 0.9rem;
            overflow: hidden;
        }

        table {
            border-collapse: collapse;
        }

        th {
            background: rgba(18,40,61,0.85);
            color: var(--text) !important;
        }

        td {
            border-top: 1px solid var(--border);
            color: var(--text) !important;
        }

        .stTabs [role="tablist"] {
            border-bottom: 1px solid var(--border);
            gap: 0.5rem;
        }

        .stTabs [role="tab"] {
            background: rgba(18,40,61,0.7);
            border: 1px solid var(--border);
            border-bottom: none;
            border-radius: 0.8rem 0.8rem 0 0;
            color: var(--muted);
            padding: 0.55rem 0.9rem;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            color: var(--text);
            background: rgba(14,32,51,0.96);
            border-color: rgba(34,211,238,0.35);
        }

        .stAlert {
            border-radius: 0.9rem;
            border: 1px solid var(--border);
        }

        .stInfo, .stWarning, .stError, .stSuccess {
            background: rgba(14,32,51,0.75);
            color: var(--text);
        }

        @media (max-width: 990px) {
            .app-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .page-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .arch-row {
                grid-template-columns: 1fr 18px 1fr;
            }
            .arch-row .arch-arrow:nth-child(2),
            .arch-row .arch-arrow:nth-child(4) {
                display: flex;
            }
            .arch-row .arch-arrow:nth-child(2) {
                grid-column: 2;
            }
            .arch-row .arch-node {
                min-height: 4.5rem;
            }
        }

        @media (max-width: 680px) {
            .block-container {
                padding-left: 0.7rem !important;
                padding-right: 0.7rem !important;
            }
            .system-grid {
                grid-template-columns: 1fr;
            }
            .arch-row {
                grid-template-columns: 1fr;
            }
            .arch-arrow {
                display: none;
            }
            .status-pill {
                min-width: auto;
                letter-spacing: 0.08em;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init():
    with db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS drone(drone_id INTEGER PRIMARY KEY, serial_number TEXT UNIQUE NOT NULL, model TEXT, firmware_version TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS mission(mission_id INTEGER PRIMARY KEY AUTOINCREMENT, drone_id INTEGER NOT NULL, mission_name TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT, status TEXT NOT NULL, planned_target_lat REAL, planned_target_lon REAL, landing_lat REAL, landing_lon REAL, landing_error_m REAL, notes TEXT, FOREIGN KEY(drone_id) REFERENCES drone(drone_id));
            CREATE TABLE IF NOT EXISTS telemetry(telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER NOT NULL, timestamp TEXT NOT NULL, latitude REAL, longitude REAL, altitude_m REAL, speed_mps REAL, roll_deg REAL, pitch_deg REAL, yaw_deg REAL, battery_voltage_v REAL, battery_percent REAL, connection_state TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'SIMULATION', FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
            CREATE TABLE IF NOT EXISTS flight_log(log_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER, timestamp TEXT NOT NULL, level TEXT NOT NULL, event_type TEXT NOT NULL, message TEXT NOT NULL, details_json TEXT, FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
            CREATE TABLE IF NOT EXISTS ai_detection(detection_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER NOT NULL, timestamp TEXT NOT NULL, class_name TEXT NOT NULL, confidence REAL NOT NULL, x1 REAL, y1 REAL, x2 REAL, y2 REAL, latency_ms REAL, status TEXT NOT NULL, source TEXT NOT NULL, FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
            """
        )
        if not c.execute("SELECT 1 FROM drone LIMIT 1").fetchone():
            c.execute(
                "INSERT INTO drone VALUES(1,'CARGO-001','Academic prototype','N/A',?)",
                (now(),),
            )
        if not c.execute("SELECT 1 FROM mission LIMIT 1").fetchone():
            c.execute(
                "INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,'Demo mission',?,'SIMULATION','Data sintetis; bukan penerbangan nyata')",
                (now(),),
            )


def q(sql, params=()):
    with db() as c:
        return pd.read_sql_query(sql, c, params=params)


def active_mission():
    r = q("SELECT mission_id FROM mission WHERE status IN ('SIMULATION','ACTIVE') ORDER BY mission_id DESC LIMIT 1")
    if r.empty:
        with db() as c:
            c.execute(
                "INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,'Demo mission',?,'SIMULATION','Simulation')",
                (now(),),
            )
        return active_mission()
    return int(r.iloc[0, 0])


def log(level, etype, msg, details=None):
    with db() as c:
        c.execute(
            "INSERT INTO flight_log(mission_id,timestamp,level,event_type,message,details_json) VALUES(?,?,?,?,?,?)",
            (active_mission(), now(), level, etype, msg, json.dumps(details or {})),
        )


def gen(n, state="ONLINE"):
    mid = active_mission()
    with db() as c:
        old = c.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
        for i in range(n):
            pct = max(0, 96 - (old + i) * random.uniform(0.12, 0.24))
            c.execute(
                """INSERT INTO telemetry(mission_id,timestamp,latitude,longitude,altitude_m,speed_mps,roll_deg,pitch_deg,yaw_deg,battery_voltage_v,battery_percent,connection_state,source)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    mid,
                    now(),
                    -6.2 + random.uniform(-0.0005, 0.0005),
                    106.8166 + random.uniform(-0.0005, 0.0005),
                    round(random.uniform(10, 35), 2),
                    round(random.uniform(0, 8), 2),
                    round(random.uniform(-8, 8), 2),
                    round(random.uniform(-8, 8), 2),
                    round(random.uniform(0, 360), 2),
                    round(11.1 + 3.3 * pct / 100, 2),
                    round(pct, 1),
                    state,
                    "SIMULATION",
                ),
            )
    log("WARNING" if state == "OFFLINE" else "INFO", "TELEMETRY_" + state, f"{n} sampel sintetis; koneksi {state}", {"source": "SIMULATION"})


def model_path():
    return next((p for p in MODEL_CANDIDATES if p.exists()), None)


def render_status_badge(status):
    status_text = str(status).upper() if status is not None else "NO DATA"
    if status_text in {"OFFLINE", "CRITICAL"}:
        badge_class = "status-offline"
    elif status_text in {"ONLINE", "SIMULATION", "SIMULATION ONLINE", "ACTIVE"}:
        badge_class = "status-online"
    else:
        badge_class = "status-warning"
    return f"<span class='status-pill {badge_class}'>{status_text}</span>"


def render_page_header(title, subtitle, status):
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="eyebrow">Cargo Flight Intelligence</div>
                <h2>{title}</h2>
            </div>
            <div>{render_status_badge(status)}</div>
        </div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


init()

tel = q("SELECT * FROM telemetry ORDER BY telemetry_id")
logs = q("SELECT * FROM flight_log ORDER BY log_id DESC LIMIT 200")
dets = q("SELECT * FROM ai_detection ORDER BY detection_id DESC LIMIT 100")
missions = q("SELECT * FROM mission ORDER BY mission_id DESC")
mid = active_mission()
latest = tel.iloc[-1] if not tel.empty else None

with st.sidebar:
    st.markdown(
        """
        <div class="brand-block">
            <div class="brand-mark">CF</div>
            <div>
                <div class="brand-title">Cargo Flight Intelligence</div>
                <div class="brand-subtitle">GROUND STATION • SIMULATION</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio("NAVIGASI", ["Overview", "Telemetry & Logs", "AI Landing Target", "Mission History", "System & Safety"])
    st.markdown('<div class="sidebar-section-title">Telemetry Controls</div>', unsafe_allow_html=True)
    n = st.slider("Jumlah sampel telemetri", 1, 30, 5)
    if st.button("Generate telemetri", use_container_width=True):
        gen(n)
        st.rerun()

    a, b = st.columns(2)
    if a.button("Simulasi OFFLINE", use_container_width=True, type="secondary"):
        gen(1, "OFFLINE")
        st.rerun()
    if b.button("Pulihkan ONLINE", use_container_width=True, type="primary"):
        gen(1, "ONLINE")
        st.rerun()

    status_text = "SIMULATION ONLINE" if latest is not None and latest.connection_state != "OFFLINE" else "SIMULATION OFFLINE"
    status_cls = "offline" if latest is not None and latest.connection_state == "OFFLINE" else ""
    st.markdown(
        f"<div class='signal-status {status_cls}'><span class='signal-dot'></span>{status_text}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Tidak terhubung ke drone nyata.")

status_for_header = latest.connection_state if latest is not None else "NO DATA"

st.markdown(
    """
    <div class="app-header">
        <div>
            <div class="eyebrow">UNMANNED SYSTEMS / MONITORING PLATFORM</div>
            <h1>Cargo Flight Intelligence</h1>
            <div class="app-header-sub">Telemetry • Mission logging • YOLO helipad detection • Ground control simulation</div>
        </div>
        <div>
            <div class="status-pill status-online">Simulation Overview</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if latest is None:
    st.info("Belum ada telemetri. Gunakan Generate telemetri di sidebar.")
elif latest.connection_state == "OFFLINE":
    st.error("ALARM: koneksi OFFLINE. Data tidak boleh dianggap real-time.")
else:
    st.info("MODE SIMULASI: telemetri sintetis. Bukan data penerbangan nyata.")

if page == "Overview":
    render_page_header("Overview", "Ringkasan sistem, kondisi telemetri, dan status misi saat ini.", status_for_header)
    cols = st.columns(4)
    cols[0].metric("Mission", f"MSN-{mid:03d}")
    cols[1].metric("Battery", f"{latest.battery_percent:.1f}%" if latest is not None else "—")
    cols[2].metric("Altitude", f"{latest.altitude_m:.1f} m" if latest is not None else "—")
    cols[3].metric("Link", str(latest.connection_state) if latest is not None else "NO DATA")

    if tel.empty:
        st.markdown("<div class='panel'><h3>Telemetri belum tersedia</h3><p>Belum ada data yang dapat ditampilkan. Gunakan tombol Generate telemetri dari sidebar untuk menghasilkan sampel simulasi.</p></div>", unsafe_allow_html=True)
    else:
        chart = tel.copy()
        chart["timestamp"] = pd.to_datetime(chart["timestamp"], errors="coerce")
        st.subheader("Tegangan baterai terhadap waktu")
        st.line_chart(chart.set_index("timestamp")["battery_voltage_v"])

        st.subheader("Telemetri terbaru")
        st.dataframe(tel.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Posisi drone")
        if latest is not None:
            st.write(f"GPS: {latest.latitude:.7f}, {latest.longitude:.7f}")
            st.write(f"Altitude {latest.altitude_m:.1f} m • Speed {latest.speed_mps:.1f} m/s")
            st.write(f"Roll {latest.roll_deg:.1f}° • Pitch {latest.pitch_deg:.1f}° • Yaw {latest.yaw_deg:.1f}°")
            st.map(pd.DataFrame([{"lat": latest.latitude, "lon": latest.longitude}]))
        else:
            st.write("Belum ada koordinat yang tersedia.")
    with right:
        st.subheader("AI event terbaru")
        if dets.empty:
            st.write("Belum ada inferensi yang disimpan.")
        else:
            st.dataframe(dets.head(5), use_container_width=True, hide_index=True)
        st.subheader("Flight log")
        st.dataframe(logs.head(8), use_container_width=True, hide_index=True)

elif page == "Telemetry & Logs":
    render_page_header("Telemetry & Logs", "Pemantauan data real-time simulasi dan rekam jejak aktivitas sistem.", status_for_header)
    st.subheader("Riwayat telemetri")
    st.dataframe(tel.iloc[::-1], use_container_width=True, hide_index=True)
    st.download_button("Ekspor telemetri CSV", tel.to_csv(index=False).encode(), "telemetry.csv", "text/csv")
    st.subheader("Flight log")
    st.dataframe(logs, use_container_width=True, hide_index=True)
    st.download_button("Ekspor flight log CSV", logs.to_csv(index=False).encode(), "flight_log.csv", "text/csv")

elif page == "AI Landing Target":
    render_page_header("AI Landing Target", "Inferensi visual untuk target pendaratan helipad dan hasil deteksi yang disimpan.", status_for_header)
    st.subheader("Inferensi YOLOv8n — helipad")
    mp = model_path()
    if mp:
        st.success(f"Bobot model ditemukan: {mp.relative_to(ROOT)}")
    else:
        st.warning("Bobot model belum ditemukan. Tempatkan hasil training best.pt di models/best.pt. Model umum yolov8n.pt tidak otomatis mengenali kelas helipad.")
    up = st.file_uploader("Unggah gambar uji (JPG/PNG)", type=["jpg", "jpeg", "png"])
    conf = st.slider("Confidence threshold", 0.1, 0.9, 0.25, 0.05)
    if up and st.button("Jalankan inferensi YOLO"):
        if not mp:
            st.error("Inferensi dibatalkan: bobot custom helipad belum tersedia. Latih model terlebih dahulu sesuai TRAINING_AND_EVALUATION.md.")
        else:
            try:
                from ultralytics import YOLO

                im = Image.open(io.BytesIO(up.getvalue())).convert("RGB")
                model = YOLO(str(mp))
                start = time.perf_counter()
                results = model.predict(source=im, conf=conf, verbose=False)
                latency = (time.perf_counter() - start) * 1000
                res = results[0]
                annotated = res.plot()[:, :, ::-1]
                st.image(annotated, caption=f"Inferensi nyata • {latency:.1f} ms", use_container_width=True)
                boxes = res.boxes
                if boxes is None or len(boxes) == 0:
                    st.warning("NO_DETECTION — minta pemeriksaan operator; jangan lanjutkan precision landing otomatis.")
                    log("WARNING", "AI_NO_DETECTION", "Model tidak mendeteksi target", {"latency_ms": latency, "source": "YOLO"})
                else:
                    rows = []
                    names = res.names
                    for box in boxes:
                        xy = box.xyxy[0].cpu().tolist()
                        cf = float(box.conf[0].cpu())
                        cls = int(box.cls[0].cpu())
                        cname = str(names.get(cls, cls))
                        status = "CANDIDATE" if cf >= 0.60 else "LOW_CONFIDENCE"
                        rows.append(
                            {
                                "class": cname,
                                "confidence": cf,
                                "x1": xy[0],
                                "y1": xy[1],
                                "x2": xy[2],
                                "y2": xy[3],
                                "latency_ms": latency,
                                "status": status,
                            }
                        )
                        with db() as c:
                            c.execute(
                                "INSERT INTO ai_detection(mission_id,timestamp,class_name,confidence,x1,y1,x2,y2,latency_ms,status,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                (mid, now(), cname, cf, *xy, latency, status, "YOLO_INFERENCE"),
                            )
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    if any(r["status"] == "LOW_CONFIDENCE" for r in rows):
                        st.warning("LOW_CONFIDENCE — verifikasi operator diperlukan.")
                    log("INFO", "AI_INFERENCE", "Inferensi YOLO selesai", {"latency_ms": latency, "detections": len(rows), "source": "YOLO_INFERENCE"})
                if latency >= 200:
                    st.warning("Latensi mencapai/melebihi target 200 ms pada perangkat ini.")
                st.caption("Latensi ini adalah pengukuran satu inferensi pada komputer saat ini, bukan benchmark p95 atau bukti performa edge device.")
            except Exception as e:
                st.error(f"Inferensi gagal: {e}")
                log("ERROR", "AI_INFERENCE_FAILED", "Inferensi gagal", {"error": str(e)[:300]})
    st.caption("Hasil visual berada pada koordinat piksel; bukan koordinat geografis dan tidak mengendalikan drone.")
    if not dets.empty:
        st.subheader("Riwayat deteksi tersimpan")
        st.dataframe(dets, use_container_width=True, hide_index=True)

elif page == "Mission History":
    render_page_header("Mission History", "Daftar misi simulasi dan statusnya yang tersimpan di sistem lokal.", status_for_header)
    st.subheader("Riwayat misi")
    st.dataframe(missions, use_container_width=True, hide_index=True)
    if st.button("Buat misi simulasi baru"):
        with db() as c:
            c.execute("UPDATE mission SET status='COMPLETED',end_time=? WHERE status IN ('SIMULATION','ACTIVE')", (now(),))
            c.execute(
                "INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,?,?,'SIMULATION','Data sintetis; bukan penerbangan nyata')",
                (f"Mission {datetime.now().strftime('%H%M%S')}", now()),
            )
        log("INFO", "MISSION_CREATED", "Misi simulasi baru dibuat")
        st.rerun()

elif page == "System & Safety":
    render_page_header("System & Safety", "Status peralatan, arsitektur data, dan langkah pengamanan prototipe yang sedang dipantau.", status_for_header)
    st.subheader("Arsitektur sistem")
    st.markdown(
        """
        <div class="panel">
            <div class="arch-row">
                <div class="arch-node">Drone Sensors</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">Flight Controller</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">MAVLink / JSON Simulation</div>
            </div>
            <div class="arch-row mid">
                <div class="arch-node">Python Backend</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">SQLite Storage</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">Streamlit Dashboard</div>
            </div>
            <div class="arch-row">
                <div class="arch-node">Camera Frame</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">YOLOv8n Edge Inference</div>
                <div class="arch-arrow">→</div>
                <div class="arch-node">Detection Output</div>
            </div>
            <div class="arch-row single">
                <div class="arch-node">Dashboard / Logs</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Target proposal — belum terbukti")
    st.table(
        pd.DataFrame(
            [
                {"Parameter": "Payload", "Target": "2–5 kg", "Status": "Perlu uji perangkat keras"},
                {"Parameter": "Durasi terbang", "Target": "≥15 menit", "Status": "Perlu uji penerbangan"},
                {"Parameter": "Akurasi pendaratan", "Target": "≤0,5 m", "Status": "Perlu ground truth lapangan"},
                {"Parameter": "AI latency", "Target": "<200 ms", "Status": "Ukur pada perangkat target"},
            ]
        )
    )

    st.subheader("Pengamanan dan fallback")
    st.markdown(
        "- SQLite memakai parameterized query dan foreign key. Prototipe lokal belum menerapkan autentikasi/RBAC/TLS produksi.\n- Koneksi OFFLINE/data basi: tandai status, catat event, jangan tampilkan sebagai real-time.\n- AI NO_DETECTION, confidence rendah, hasil tidak konsisten, atau data stale: operator melakukan pemeriksaan; gunakan prosedur hold/abort/go-around yang telah divalidasi.\n- Bounding box visual tidak cukup untuk menentukan offset pendaratan. Diperlukan kalibrasi kamera, pose/altitude, geometri kamera, transformasi koordinat, dan ground truth.\n- Tidak ada perintah kendali drone otomatis pada prototipe ini."
    )

st.caption("CARGO Flight Intelligence • educational prototype • simulation data clearly labeled")
