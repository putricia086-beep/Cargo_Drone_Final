# Cargo Drone Monitoring dan Deteksi Target Pendaratan Berbasis AI

Paket prototipe akademik untuk soal STI, AI, dan integrasi. Dashboard menggunakan Streamlit dan SQLite;
telemetri yang dihasilkan adalah data simulasi. Halaman AI menjalankan inferensi Ultralytics hanya jika
bobot custom helipad tersedia di `models/best.pt` atau lokasi hasil training yang ditentukan. Dataset sengaja
kosong: tambahkan data berizin dan anotasi nyata. Tidak ada klaim metrik AI atau hasil penerbangan yang dibuat-buat.

## Menjalankan (dashboard)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Buka URL lokal yang dicetak Streamlit. Gunakan perintah yang sama di terminal dari folder proyek.

## AI sesungguhnya
Ikuti `TRAINING_AND_EVALUATION.md`, install `requirements-ai.txt`, siapkan dataset YOLO, latih dan uji model,
lalu salin `best.pt` ke `models/best.pt`. Bobot pretrained COCO bukan model helipad khusus.

## Database dan pengujian
Database `cargo_drone.db` dibuat otomatis. Tabel: drone, mission, telemetry, flight_log, ai_detection.
Uji generator telemetri, OFFLINE/ONLINE, grafik baterai, ekspor CSV, dan inferensi gambar setelah model tersedia.
Prototipe belum memiliki autentikasi/RBAC/TLS produksi dan tidak mengirim perintah ke drone.
