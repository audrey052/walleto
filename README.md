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

Rencana kerja ada di [WORKPLAN.md](WORKPLAN.md).
