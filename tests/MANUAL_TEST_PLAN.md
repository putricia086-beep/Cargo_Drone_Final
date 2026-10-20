# Rencana uji manual

1. Instal `requirements.txt`; jalankan `streamlit run app.py`; pastikan dashboard terbuka.
2. Generate telemetri; periksa sampel baru di Overview dan Telemetry & Logs.
3. Klik Simulasi OFFLINE; pastikan alarm merah dan flight_log memuat `TELEMETRY_OFFLINE`.
4. Klik Pulihkan ONLINE; pastikan sampel terbaru ONLINE dan event pemulihan tercatat.
5. Periksa grafik tegangan baterai terhadap timestamp dan ekspor CSV.
6. Buat misi baru; pastikan status misi sebelumnya COMPLETED dan misi baru tersimpan.
7. Tanpa `models/best.pt`, unggah gambar dan jalankan inferensi: aplikasi harus menjelaskan model belum tersedia, bukan mengarang deteksi.
8. Dengan bobot hasil training, uji gambar helipad dan non-helipad; periksa bounding box, confidence, latensi, database dan log.
9. Uji gambar rusak/tidak didukung, confidence rendah, tanpa deteksi, serta latensi >=200 ms.
10. Catat hasil aktual, screenshot, versi perangkat lunak, perangkat, dan setiap kegagalan. Uji keselamatan dilakukan di simulasi, bukan dengan kendali penerbangan nyata.
