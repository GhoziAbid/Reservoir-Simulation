# Reservoir Simulation

Model sederhana ini menyiapkan kerangka simulasi reservoir panas bumi berbasis neraca massa dan energi.
Meski tidak menggantikan simulator komersial, script ini membantu eksplorasi awal skenario produksi dan injeksi.

## Cara kerja
- Reservoir dimodelkan sebagai volume tunggal dengan porositas, kompresibilitas total, massa fluida, dan massa batuan.
- Langkah waktu diskret menghitung perubahan tekanan akibat perubahan massa fluida.
- Neraca energi memperhitungkan panas yang dibawa fluida injeksi dan panas yang ikut terproduksi.

## Menjalankan simulasi
Python standar sudah cukup (tidak ada dependensi eksternal). Contoh menjalankan 180 hari dengan time step 5 hari:

```bash
python geothermal_sim.py \
  --duration-days 180 \
  --dt-days 5 \
  --production-kgps 80 \
  --injection-kgps 70 \
  --injection-temperature 80
```

Hasil dapat langsung tampil di terminal atau disimpan sebagai CSV:

```bash
python geothermal_sim.py --duration-days 90 --dt-days 1 --production-kgps 60 --injection-kgps 60 --output hasil.csv
```

Kolom CSV: `time_days`, `pressure_pa`, `temperature_c`, `fluid_mass_kg`.

## Membaca hasil
- **Tekanan** meningkat bila injeksi lebih besar dari produksi; sebaliknya menurun ketika produksi mendominasi.
- **Suhu** akan turun jika fluida injeksi lebih dingin dari reservoir karena energi termal terbawa keluar bersama fluida produksi.
- **Massa fluida** membantu mengevaluasi perubahan saturasi/volume efektif akibat strategi injeksi-produksi.

## Keterbatasan model
- Tidak memodelkan aliran multiphase, konduksi batuan ke sekeliling, atau distribusi spasial (hanya satu sel kontrol volume).
- Sifat fluida dianggap konstan; pada kondisi nyata densitas/viskositas bisa berubah terhadap tekanan/suhu.
- Tidak memasukkan batasan sumur (productivity index, wellbore/skin) maupun batas reservoir (aquifer/border influx).

## Melanjutkan pengembangan
Untuk keperluan lomba atau studi lebih lanjut, Anda dapat:
- Menambahkan grid multi-sel untuk menangkap heterogenitas dan transien spasial.
- Memisahkan brine dan steam (model dua fasa) dengan properti termodinamika lebih detail.
- Menghubungkan model ini ke antarmuka web atau dashboard untuk eksplorasi parameter secara interaktif.
