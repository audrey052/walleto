# Walleto

Aplikasi web untuk mengatur keuangan pribadi: catat transaksi di beberapa dompet, atur budget bulanan, pantau target tabungan, dan tanya asisten AI tentang data keuanganmu sendiri.

> README ini masih ringkasan internal. Versi untuk publik (screenshot, demo, hasil evaluasi) ditulis di MVP terakhir.

## Fitur (rencana)

| Halaman | Isi |
|---|---|
| Wallets | Dompet (cash, bank, e-wallet), saldo, transfer antar dompet |
| Transactions | Catat, edit, hapus, filter; catat cepat dengan bahasa sehari-hari (AI) |
| Budget | Batas per kategori per bulan, progress, peringatan |
| Savings Goals | Target tabungan, setoran, status sesuai jalur atau tertinggal |
| Dashboard | Ringkasan bulanan dengan filter bulan dan grafik |
| Assistant | Tanya data, catat transaksi, rencana sisa bulan, laporan PDF (tool calling) |

## Stack

- **Django** (backend + halaman HTML), autentikasi bawaan Django
- **Tailwind CSS** (light mode saja), **HTMX** + **Alpine.js** untuk interaksi, **ApexCharts** untuk grafik
- **SQLite** saat development, **PostgreSQL** saat deploy
- **OpenAI API** (structured output + tool calling) untuk fitur AI
- **OpenSpec** untuk mencatat perubahan per MVP

## Prinsip desain

- UI sepenuhnya berbahasa Inggris, light mode saja.
- Desain dari Figma Make (`docs/design/`), aturan gaya di `docs/STYLE.md`.
- Angka selalu dihitung oleh kode dan database, bukan oleh LLM. LLM hanya menerjemahkan maksud pengguna, memilih tool, dan menjelaskan hasil.

## Menjalankan secara lokal

Butuh Python 3.11 dan Node.js (untuk build CSS Tailwind).

```powershell
# 1. Environment Python
python -m venv .venv --prompt walleto
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Settings: salin .env.example menjadi .env, lalu isi SECRET_KEY dan DEBUG=True
copy .env.example .env

# 3. Database dan akun admin
python manage.py migrate
python manage.py createsuperuser

# 4. CSS (sekali install, lalu biarkan watcher jalan di terminal terpisah)
npm install
npm run css:watch

# 5. Server (terminal lain)
python manage.py runserver
```

Data demo (akun `demo@walleto.app`, 3 bulan transaksi): jalankan `python manage.py seed_demo`, atau klik **Try demo account** di halaman login (data dibuat otomatis kalau belum ada). Jalankan ulang `seed_demo` untuk mereset data demo.

Buka http://127.0.0.1:8000, daftar akun baru, coba akun demo, atau masuk dengan akun superuser. Halaman semua komponen ada di `/styleguide/` (hanya saat `DEBUG=True`).

Menjalankan test:

```powershell
python manage.py test
```

Rencana kerja ada di [WORKPLAN.md](WORKPLAN.md).
