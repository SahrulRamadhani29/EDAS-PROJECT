# Sistem Pendukung Keputusan Metode EDAS

Aplikasi web berbasis **Python + Streamlit** untuk menghitung perangkingan alternatif menggunakan metode **EDAS (Evaluation Based on Distance from Average Solution)**.

Seluruh data pada aplikasi bersifat **100% dinamis** dan harus diinput oleh pengguna (tanpa data contoh bawaan).

## Teknologi

- Python 3.11+
- Streamlit
- Pandas
- NumPy
- OpenPyXL / XlsxWriter (ekspor Excel)

## Instalasi

```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

## Cara Menggunakan

1. Buka tab **Input Data**.
2. Isi **Jumlah Kriteria** dan **Jumlah Alternatif**.
3. Isi tabel **Kriteria**:
   - Kode
   - Nama Kriteria
   - Jenis (Benefit/Cost)
   - Bobot
4. Isi tabel **Matriks Keputusan**:
   - Alternatif
   - Nilai setiap alternatif pada seluruh kriteria
   - Input nilai kriteria boleh berupa teks + angka (contoh: `5 KM`, `12 unit`, `7,5 liter`). Sistem otomatis mengambil angka untuk perhitungan.
5. Klik tombol **Hitung EDAS**.
6. Lihat hasil pada tab:
   - Matriks Keputusan
   - Perhitungan EDAS
   - Ranking Akhir
7. Klik **Download Hasil Excel** untuk mengunduh hasil lengkap.

## Ringkasan Metode EDAS

1. Bentuk matriks keputusan `X`.
2. Hitung `AV` (Average Solution) pada tiap kriteria.
3. Hitung `PDA` dan `NDA` berdasarkan jenis kriteria Benefit/Cost.
4. Hitung `SP` dan `SN` (jumlah terbobot).
5. Normalisasi menjadi `NSP` dan `NSN`.
6. Hitung `AS = (NSP + NSN) / 2`.
7. Urutkan `AS` tertinggi sebagai alternatif terbaik.

## Output Excel

File hasil ekspor berisi sheet:

1. `Kriteria`
2. `Matriks_Keputusan`
3. `AV`
4. `PDA`
5. `NDA`
6. `SP_SN`
7. `NSP_NSN_AS`
8. `Ranking`

Format angka hasil perhitungan menggunakan 4 angka desimal.

## Fitur Input Nilai Campuran (Angka + Teks)

- Pengguna dapat mengisi nilai kriteria tidak hanya angka murni, tetapi juga format campuran seperti `5 KM` atau `10 orang`.
- Aplikasi akan mengekstrak komponen angka untuk proses perhitungan EDAS.
- Teks satuan/keterangan tetap tersimpan dan ditampilkan pada tabel input matriks keputusan.
- Jika input tidak mengandung angka sama sekali (misalnya hanya `KM`), data dianggap tidak valid dan perhitungan akan ditolak.
