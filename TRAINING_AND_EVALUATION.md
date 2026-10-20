# Training dan evaluasi YOLOv8n

## Lingkungan
Disarankan Python 3.11 atau 3.12 karena dukungan PyTorch pada versi Python yang sangat baru dapat tertinggal.
Windows PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-ai.txt
```
Letakkan gambar dan label YOLO pada `dataset/images/{train,val,test}` dan `dataset/labels/{train,val,test}`.
Edit `dataset/data.yaml` jika struktur berubah.

## Training
Jalankan dari folder proyek:
```powershell
yolo detect train model=yolov8n.pt data=dataset/data.yaml imgsz=640 epochs=100 batch=8 project=runs/cargo name=yolov8n_helipad seed=42
```
Batch dapat dikurangi bila RAM/VRAM tidak cukup. Setelah training, salin `runs/cargo/yolov8n_helipad/weights/best.pt` ke `models/best.pt`.
Model pretrained `yolov8n.pt` bukan detektor helipad khusus sampai fine-tuning dataset helipad dilakukan.

## Validasi dan test independen
```powershell
yolo detect val model=models/best.pt data=dataset/data.yaml split=val imgsz=640
yolo detect val model=models/best.pt data=dataset/data.yaml split=test imgsz=640
```
Simpan output metrics dan konfigurasi. Jangan memakai test set untuk tuning berulang.
Precision = TP/(TP+FP), recall = TP/(TP+FN), mAP@50 = mean average precision pada IoU 0.50.
Ukur latensi setelah warm-up pada perangkat target; catat median dan p95 dari banyak frame, ukuran gambar,
perangkat, versi software, dan apakah waktu preprocessing/postprocessing disertakan. Target <200 ms
adalah sasaran, bukan hasil yang dijamin. Lakukan juga uji kondisi terang/redup, bayangan, sudut miring,
target kecil/jauh, occlusion dan objek mirip.

## Jalankan dashboard
```powershell
streamlit run app.py
```
Unggah gambar uji pada menu AI Landing Target. Hasil inferensi yang disimpan diberi sumber `YOLO_INFERENCE`.
Jika bobot tidak tersedia, dashboard tidak mengarang prediksi. Jangan gunakan prototipe ini untuk kendali
atau pendaratan drone sungguhan.
