# Dataset helipad

Folder train/val/test dan label disediakan sebagai struktur kosong, bukan dataset berisi.
Tambahkan gambar yang Anda miliki hak penggunaannya. Setiap gambar memiliki label `.txt`
dengan satu baris per objek: `class_id x_center y_center width height`; koordinat dinormalisasi
0–1 dan kelas `0` adalah `helipad`. Gambar tanpa objek boleh memiliki file label kosong.
Saran awal pembagian 70/20/10, tetapi pisahkan berdasarkan sesi/lokasi untuk mencegah
frame berdekatan masuk ke split berbeda. Audit semua anotasi sebelum training.
