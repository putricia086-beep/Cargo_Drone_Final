import io, json, random, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image

ROOT = Path(__file__).resolve().parent
DB = ROOT / "cargo_drone.db"
MODEL_CANDIDATES = [ROOT/"models"/"best.pt", ROOT/"runs"/"cargo"/"yolov8n_helipad"/"weights"/"best.pt"]
st.set_page_config(page_title="CARGO | Ground Station", page_icon="🛰️", layout="wide")
st.markdown("""<style>
.stApp{background:radial-gradient(ellipse at 10% 0%,#102b45 0%,#081626 48%,#050b14 100%);color:#e8f4ff}
.block-container{padding-top:1.2rem;max-width:1500px}
section[data-testid="stSidebar"]{background:#071522;border-right:1px solid #18364e}
h1,h2,h3,p,label{color:#e8f4ff}
div[data-testid="stMetric"]{background:#0c2032;border:1px solid #1b405a;padding:12px;border-radius:12px}
div[data-testid="stMetricValue"]{color:#43d9f2}
.stButton>button{border:1px solid #26778d;border-radius:9px;background:#10344a;color:#eafaff}
.hero{padding:20px 24px;border:1px solid #1c4a63;border-radius:16px;background:linear-gradient(110deg,#102b43,#091b2b);margin-bottom:16px}
</style>""", unsafe_allow_html=True)

def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def db():
    c=sqlite3.connect(DB,check_same_thread=False); c.execute("PRAGMA foreign_keys=ON"); return c
def init():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS drone(drone_id INTEGER PRIMARY KEY, serial_number TEXT UNIQUE NOT NULL, model TEXT, firmware_version TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS mission(mission_id INTEGER PRIMARY KEY AUTOINCREMENT, drone_id INTEGER NOT NULL, mission_name TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT, status TEXT NOT NULL, planned_target_lat REAL, planned_target_lon REAL, landing_lat REAL, landing_lon REAL, landing_error_m REAL, notes TEXT, FOREIGN KEY(drone_id) REFERENCES drone(drone_id));
        CREATE TABLE IF NOT EXISTS telemetry(telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER NOT NULL, timestamp TEXT NOT NULL, latitude REAL, longitude REAL, altitude_m REAL, speed_mps REAL, roll_deg REAL, pitch_deg REAL, yaw_deg REAL, battery_voltage_v REAL, battery_percent REAL, connection_state TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'SIMULATION', FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
        CREATE TABLE IF NOT EXISTS flight_log(log_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER, timestamp TEXT NOT NULL, level TEXT NOT NULL, event_type TEXT NOT NULL, message TEXT NOT NULL, details_json TEXT, FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
        CREATE TABLE IF NOT EXISTS ai_detection(detection_id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id INTEGER NOT NULL, timestamp TEXT NOT NULL, class_name TEXT NOT NULL, confidence REAL NOT NULL, x1 REAL, y1 REAL, x2 REAL, y2 REAL, latency_ms REAL, status TEXT NOT NULL, source TEXT NOT NULL, FOREIGN KEY(mission_id) REFERENCES mission(mission_id));
        """)
        if not c.execute("SELECT 1 FROM drone LIMIT 1").fetchone():
            c.execute("INSERT INTO drone VALUES(1,'CARGO-001','Academic prototype','N/A',?)",(now(),))
        if not c.execute("SELECT 1 FROM mission LIMIT 1").fetchone():
            c.execute("INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,'Demo mission',?,'SIMULATION','Data sintetis; bukan penerbangan nyata')",(now(),))
def q(sql,params=()):
    with db() as c: return pd.read_sql_query(sql,c,params=params)
def active_mission():
    r=q("SELECT mission_id FROM mission WHERE status IN ('SIMULATION','ACTIVE') ORDER BY mission_id DESC LIMIT 1")
    if r.empty:
        with db() as c: c.execute("INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,'Demo mission',?,'SIMULATION','Simulation')",(now(),))
        return active_mission()
    return int(r.iloc[0,0])
def log(level,etype,msg,details=None):
    with db() as c: c.execute("INSERT INTO flight_log(mission_id,timestamp,level,event_type,message,details_json) VALUES(?,?,?,?,?,?)",(active_mission(),now(),level,etype,msg,json.dumps(details or {})))
def gen(n,state="ONLINE"):
    mid=active_mission()
    with db() as c:
        old=c.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
        for i in range(n):
            pct=max(0,96-(old+i)*random.uniform(.12,.24))
            c.execute("""INSERT INTO telemetry(mission_id,timestamp,latitude,longitude,altitude_m,speed_mps,roll_deg,pitch_deg,yaw_deg,battery_voltage_v,battery_percent,connection_state,source)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(mid,now(),-6.2+random.uniform(-.0005,.0005),106.8166+random.uniform(-.0005,.0005),round(random.uniform(10,35),2),round(random.uniform(0,8),2),round(random.uniform(-8,8),2),round(random.uniform(-8,8),2),round(random.uniform(0,360),2),round(11.1+3.3*pct/100,2),round(pct,1),state,"SIMULATION"))
    log("WARNING" if state=="OFFLINE" else "INFO","TELEMETRY_"+state,f"{n} sampel sintetis; koneksi {state}",{"source":"SIMULATION"})
def model_path():
    return next((p for p in MODEL_CANDIDATES if p.exists()),None)
init()
with st.sidebar:
    st.markdown("### CARGO / CONTROL")
    st.caption("GROUND STATION • SIMULATION")
    page=st.radio("NAVIGASI",["Overview","Telemetry & Logs","AI Landing Target","Mission History","System & Safety"])
    st.divider(); n=st.slider("Jumlah sampel telemetri",1,30,5)
    if st.button("Generate telemetri",use_container_width=True): gen(n); st.rerun()
    a,b=st.columns(2)
    if a.button("Simulasi OFFLINE",use_container_width=True): gen(1,"OFFLINE"); st.rerun()
    if b.button("Pulihkan ONLINE",use_container_width=True): gen(1,"ONLINE"); st.rerun()
    st.caption("Tidak terhubung ke drone nyata.")
st.markdown('<div class="hero"><small>UNMANNED SYSTEMS / MONITORING PLATFORM</small><h1>CARGO FLIGHT INTELLIGENCE</h1>Telemetry • Mission logging • YOLO helipad detection</div>',unsafe_allow_html=True)
tel=q("SELECT * FROM telemetry ORDER BY telemetry_id")
logs=q("SELECT * FROM flight_log ORDER BY log_id DESC LIMIT 200")
dets=q("SELECT * FROM ai_detection ORDER BY detection_id DESC LIMIT 100")
missions=q("SELECT * FROM mission ORDER BY mission_id DESC")
mid=active_mission(); latest=tel.iloc[-1] if not tel.empty else None
if latest is None: st.info("Belum ada telemetri. Gunakan Generate telemetri di sidebar.")
elif latest.connection_state=="OFFLINE": st.error("ALARM: koneksi OFFLINE. Data tidak boleh dianggap real-time.")
else: st.info("MODE SIMULASI: telemetri sintetis. Bukan data penerbangan nyata.")

if page=="Overview":
    cols=st.columns(4)
    cols[0].metric("MISSION",f"MSN-{mid:03d}")
    cols[1].metric("BATTERY",f"{latest.battery_percent:.1f}%" if latest is not None else "—")
    cols[2].metric("ALTITUDE",f"{latest.altitude_m:.1f} m" if latest is not None else "—")
    cols[3].metric("LINK",str(latest.connection_state) if latest is not None else "NO DATA")
    st.subheader("Tegangan baterai terhadap waktu")
    if tel.empty: st.write("Belum ada data.")
    else:
        chart=tel.copy(); chart["timestamp"]=pd.to_datetime(chart.timestamp,errors="coerce")
        st.line_chart(chart.set_index("timestamp")["battery_voltage_v"])
        st.subheader("Telemetri terbaru")
        st.dataframe(tel.tail(10).iloc[::-1],use_container_width=True,hide_index=True)
    left,right=st.columns(2)
    with left:
        st.subheader("Posisi drone")
        if latest is not None:
            st.write(f"GPS: {latest.latitude:.7f}, {latest.longitude:.7f}")
            st.write(f"Altitude {latest.altitude_m:.1f} m • Speed {latest.speed_mps:.1f} m/s")
            st.write(f"Roll {latest.roll_deg:.1f}° • Pitch {latest.pitch_deg:.1f}° • Yaw {latest.yaw_deg:.1f}°")
            st.map(pd.DataFrame([{"lat":latest.latitude,"lon":latest.longitude}]))
    with right:
        st.subheader("AI event terbaru")
        if dets.empty: st.write("Belum ada inferensi yang disimpan.")
        else: st.dataframe(dets.head(5),use_container_width=True,hide_index=True)
        st.subheader("Flight log")
        st.dataframe(logs.head(8),use_container_width=True,hide_index=True)
elif page=="Telemetry & Logs":
    st.subheader("Riwayat telemetri")
    st.dataframe(tel.iloc[::-1],use_container_width=True,hide_index=True)
    st.download_button("Ekspor telemetri CSV",tel.to_csv(index=False).encode(), "telemetry.csv","text/csv")
    st.subheader("Flight log")
    st.dataframe(logs,use_container_width=True,hide_index=True)
    st.download_button("Ekspor flight log CSV",logs.to_csv(index=False).encode(),"flight_log.csv","text/csv")
elif page=="AI Landing Target":
    st.subheader("Inferensi YOLOv8n — helipad")
    mp=model_path()
    if mp: st.success(f"Bobot model ditemukan: {mp.relative_to(ROOT)}")
    else: st.warning("Bobot model belum ditemukan. Tempatkan hasil training best.pt di models/best.pt. Model umum yolov8n.pt tidak otomatis mengenali kelas helipad.")
    up=st.file_uploader("Unggah gambar uji (JPG/PNG)",type=["jpg","jpeg","png"])
    conf=st.slider("Confidence threshold",0.1,0.9,0.25,0.05)
    if up and st.button("Jalankan inferensi YOLO"):
        if not mp:
            st.error("Inferensi dibatalkan: bobot custom helipad belum tersedia. Latih model terlebih dahulu sesuai TRAINING_AND_EVALUATION.md.")
        else:
            try:
                from ultralytics import YOLO
                im=Image.open(io.BytesIO(up.getvalue())).convert("RGB")
                model=YOLO(str(mp)); start=time.perf_counter()
                results=model.predict(source=im,conf=conf,verbose=False)
                latency=(time.perf_counter()-start)*1000
                res=results[0]; annotated=res.plot()[:,:,::-1]
                st.image(annotated,caption=f"Inferensi nyata • {latency:.1f} ms",use_container_width=True)
                boxes=res.boxes
                if boxes is None or len(boxes)==0:
                    st.warning("NO_DETECTION — minta pemeriksaan operator; jangan lanjutkan precision landing otomatis.")
                    log("WARNING","AI_NO_DETECTION","Model tidak mendeteksi target",{"latency_ms":latency,"source":"YOLO"})
                else:
                    rows=[]
                    names=res.names
                    for box in boxes:
                        xy=box.xyxy[0].cpu().tolist(); cf=float(box.conf[0].cpu())
                        cls=int(box.cls[0].cpu()); cname=str(names.get(cls,cls))
                        status="CANDIDATE" if cf>=0.60 else "LOW_CONFIDENCE"
                        rows.append({"class":cname,"confidence":cf,"x1":xy[0],"y1":xy[1],"x2":xy[2],"y2":xy[3],"latency_ms":latency,"status":status})
                        with db() as c:
                            c.execute("INSERT INTO ai_detection(mission_id,timestamp,class_name,confidence,x1,y1,x2,y2,latency_ms,status,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(mid,now(),cname,cf,*xy,latency,status,"YOLO_INFERENCE"))
                    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                    if any(r["status"]=="LOW_CONFIDENCE" for r in rows):
                        st.warning("LOW_CONFIDENCE — verifikasi operator diperlukan.")
                    log("INFO","AI_INFERENCE","Inferensi YOLO selesai",{"latency_ms":latency,"detections":len(rows),"source":"YOLO_INFERENCE"})
                if latency>=200: st.warning("Latensi mencapai/melebihi target 200 ms pada perangkat ini.")
                st.caption("Latensi ini adalah pengukuran satu inferensi pada komputer saat ini, bukan benchmark p95 atau bukti performa edge device.")
            except Exception as e:
                st.error(f"Inferensi gagal: {e}")
                log("ERROR","AI_INFERENCE_FAILED","Inferensi gagal",{"error":str(e)[:300]})
    st.caption("Hasil visual berada pada koordinat piksel; bukan koordinat geografis dan tidak mengendalikan drone.")
    if not dets.empty:
        st.subheader("Riwayat deteksi tersimpan")
        st.dataframe(dets,use_container_width=True,hide_index=True)
elif page=="Mission History":
    st.subheader("Riwayat misi")
    st.dataframe(missions,use_container_width=True,hide_index=True)
    if st.button("Buat misi simulasi baru"):
        with db() as c:
            c.execute("UPDATE mission SET status='COMPLETED',end_time=? WHERE status IN ('SIMULATION','ACTIVE')",(now(),))
            c.execute("INSERT INTO mission(drone_id,mission_name,start_time,status,notes) VALUES(1,?,?,'SIMULATION','Data sintetis; bukan penerbangan nyata')",(f"Mission {datetime.now().strftime('%H%M%S')}",now()))
        log("INFO","MISSION_CREATED","Misi simulasi baru dibuat"); st.rerun()
elif page=="System & Safety":
    st.subheader("Arsitektur")
    st.code("Drone sensors → Flight controller → MAVLink/JSON simulation → Python backend → SQLite → Streamlit dashboard\nCamera frame → YOLOv8n edge inference → bounding box/confidence/latency → SQLite → dashboard",language="text")
    st.subheader("Target proposal — belum terbukti")
    st.table(pd.DataFrame([
    {"Parameter":"Payload","Target":"2–5 kg","Status":"Perlu uji perangkat keras"},
    {"Parameter":"Durasi terbang","Target":"≥15 menit","Status":"Perlu uji penerbangan"},
    {"Parameter":"Akurasi pendaratan","Target":"≤0,5 m","Status":"Perlu ground truth lapangan"},
    {"Parameter":"AI latency","Target":"<200 ms","Status":"Ukur pada perangkat target"}]))
    st.subheader("Pengamanan dan fallback")
    st.markdown("- SQLite memakai parameterized query dan foreign key. Prototipe lokal belum menerapkan autentikasi/RBAC/TLS produksi.\n- Koneksi OFFLINE/data basi: tandai status, catat event, jangan tampilkan sebagai real-time.\n- AI NO_DETECTION, confidence rendah, hasil tidak konsisten, atau data stale: operator melakukan pemeriksaan; gunakan prosedur hold/abort/go-around yang telah divalidasi.\n- Bounding box visual tidak cukup untuk menentukan offset pendaratan. Diperlukan kalibrasi kamera, pose/altitude, geometri kamera, transformasi koordinat, dan ground truth.\n- Tidak ada perintah kendali drone otomatis pada prototipe ini.")
st.caption("CARGO Flight Intelligence • educational prototype • simulation data clearly labeled")
