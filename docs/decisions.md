# Keputusan

Catatan singkat keputusan penting: apa yang dipilih dan kenapa.

| Tanggal | Keputusan | Alasan |
|---|---|---|
| 2026-11-16 | Django saja (bukan Next.js + FastAPI) | Fokus portofolio ada di fitur AI. Django sudah menyediakan auth, ORM, dan admin, dan semuanya tetap Python. |
| 2026-11-16 | Tailwind + HTMX + Alpine.js + ApexCharts | UI modern tanpa framework JavaScript terpisah. |
| 2026-11-16 | UI bahasa Inggris, light mode saja | Menyederhanakan styling, dan UI bisa dibaca recruiter di luar Indonesia. |
| 2026-11-16 | SQLite saat development, PostgreSQL saat deploy | Setup awal paling ringan; Django memudahkan pindah database. |
| 2026-11-16 | Urutan: wallets → transactions → budget → savings goals → dashboard → AI | Fitur inti dulu supaya aplikasi sudah berguna sebelum ada AI. |
| 2026-11-16 | Angka selalu dihitung oleh kode, bukan LLM | LLM tidak andal menghitung; nominal uang harus 100% benar. |
| 2026-11-16 | `.venv` + pip (bukan conda), Python 3.11, Django 5.2 LTS | Cara paling umum di ekosistem Django; `requirements.txt` langsung bisa dipakai saat deploy. Node.js memakai instalasi global. |
| 2026-11-16 | Satu OpenSpec change per MVP | Setiap MVP punya catatan jelas tentang apa yang berubah. |
