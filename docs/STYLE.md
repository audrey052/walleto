# Walleto: Style Guide

Patokan gaya untuk semua halaman. Sumber: desain Figma Make "Walleto Finance Dashboard" (kode referensi ada di `docs/design/figma-make-source/`).

**Kode Figma Make adalah referensi visual, bukan untuk disalin.** CSS aslinya memakai ±190 warna berbeda dan 30 ukuran font, banyak di antaranya 7–9px (terlalu kecil untuk dibaca). Panduan ini merangkumnya menjadi token yang sedikit dan konsisten. Kalau desain dan panduan ini berbeda, **panduan ini yang dipakai**.

Light mode saja. Semua teks UI dalam bahasa Inggris.

---

## 1. Warna

Hanya pakai warna di tabel ini. Kalau butuh warna baru, tambahkan dulu di sini beserta alasannya.

### Netral
| Token | Hex | Dipakai untuk |
|---|---|---|
| `paper` | `#FAFAF7` | Background halaman |
| `sidebar` | `#F6F6F1` | Background sidebar |
| `surface` | `#FFFFFF` | Panel, modal, input, tombol sekunder |
| `hover` | `#F3F3EC` | Hover tombol sekunder dan baris tabel |
| `border` | `#E7E5DF` | Garis tipis panel dan pemisah |
| `border-strong` | `#DDDFD4` | Border input, hover border |
| `track` | `#EAECE3` | Latar progress bar |
| `ink` | `#1C1B18` | Teks utama |
| `secondary` | `#6B6A64` | Teks pendukung, item nav tidak aktif |
| `muted` | `#92918A` | Caption, label kecil, tanggal |
| `placeholder` | `#A5A699` | Placeholder input |

### Aksen (satu warna utama)
| Token | Hex | Dipakai untuk |
|---|---|---|
| `forest` | `#1F5C4A` | Tombol utama, nav aktif, angka utama, pemasukan, progress normal |
| `forest-hover` | `#164C3C` | Hover tombol utama |
| `forest-soft` | `#E7ECE3` | Background nav aktif |
| `forest-tint` | `#F1F3EB` | Background ikon (empty state, ikon merchant) |
| `selection` | `#DBE9DD` | Seleksi teks |

### Status (hanya untuk makna status)
| Token | Hex | Dipakai untuk |
|---|---|---|
| `amber` | `#B7791F` | Budget 90–100%, data ambigu |
| `clay` | `#B4463A` | Budget lewat 100%, error, aksi hapus |

### Palet grafik dan kategori (urutan tetap, jangan acak)
| Urutan | Hex | Kategori bawaan |
|---|---|---|
| 1 | `#1F5C4A` | Food & drinks |
| 2 | `#688373` | Shopping |
| 3 | `#99AA99` | Transport |
| 4 | `#B8AD92` | Bills & utilities |
| 5 | `#D2CDBF` | Others |

Kategori tambahan memakai ulang palet ini secara berurutan.

---

## 2. Tipografi

Font: **Plus Jakarta Sans** (variable, 400–800). File font ada di Figma Make (`src/assets/fonts/plus-jakarta-sans-latin.woff2`, lisensi OFL). Simpan di `static/fonts/` sehingga tidak bergantung pada CDN.

Ukuran di bawah **sudah dinaikkan** dari desain Figma supaya terbaca. Batas minimal 11px, dan itu pun hanya untuk label huruf kapital.

| Peran | Ukuran / tebal | Catatan | Di Figma |
|---|---|---|---|
| Display amount | 40px / 500 | Angka utama per halaman, warna `forest`, tracking −1.5px | 39–40px |
| Page title (h1) | 28px / 600 | Tracking −1px | 28px |
| Modal title | 18px / 600 | | 17px |
| Section title (h2) | 15px / 600 | Warna `ink`, bukan abu-abu | 12px abu-abu |
| Body | 14px / 400 | Teks umum, isi tabel | 13px |
| Control | 13px / 500 | Tombol, input, item nav | 10–12px |
| Caption | 12px / 400 | Tanggal, catatan di bawah angka, warna `muted` | 8–9px |
| Overline | 11px / 600 | HURUF KAPITAL, tracking 0.12em, warna `muted` | 8px |

Tebal yang dipakai hanya 400, 500, 600, dan 800 (khusus logo).

### Angka
- Semua nominal memakai `tabular-nums` supaya kolom rata.
- Prefix "Rp" lebih kecil (±0.6em) dan lebih pudar (opacity ±0.75) dari angkanya.
- Format: **`Rp847.500`** (titik sebagai pemisah ribuan, sesuai desain dan kebiasaan Rupiah), tanpa desimal.
- Pengeluaran: tanda minus `−` (U+2212), warna `ink`. Pemasukan: tanda `+`, warna `forest`.
- Nominal di tabel selalu rata kanan.

---

## 3. Bentuk, jarak, bayangan

| Hal | Nilai |
|---|---|
| Radius | 4px (chip), 6px (tombol, input, item nav), 8px (panel, modal, kartu), bulat penuh (avatar, titik status) |
| Spacing | Kelipatan 4px. Padding panel 24px; jarak antar panel 24px |
| Tinggi kontrol | Tombol 36px, input 40px, item nav 44px |
| Garis | Selalu 1px `border` |
| Ikon | Garis 1.5px, ujung bulat, 16–20px, `currentColor` |

**Bayangan** hanya untuk elemen yang melayang. Panel tidak pernah memakai bayangan.
| Elemen | Bayangan |
|---|---|
| Popover / dropdown | `0 8px 30px rgb(36 41 26 / 0.07)` |
| Toast | `0 6px 25px rgb(28 40 21 / 0.08)` |
| Modal | `0 15px 60px rgb(29 40 24 / 0.14)`, backdrop `rgb(28 36 25 / 0.34)` dengan blur 2px |

---

## 4. Layout

```
┌──────────┬─────────────────────────────────────────────┐
│ Sidebar  │ Topbar: [collapse] My workspace › Page   date 🔔│
│ 224px    ├─────────────────────────────────────────────┤
│ fixed    │ Page heading: title + subtitle | actions    │
│          │                                             │
│ Logo     │ Konten (max-width 1272px, padding 36px 40px)│
│ Nav ×6   │                                             │
│          │                                             │
│ Profile  │                                             │
└──────────┴─────────────────────────────────────────────┘
```

- **Sidebar:** logo (kotak hijau 32px + "walleto."), 6 item nav, profil di bawah. Item aktif: background `forest-soft`, teks `forest`, garis 3px di kiri. Bisa diciutkan menjadi ikon saja.
- **Topbar:** tombol collapse, breadcrumb, tanggal hari ini, lonceng notifikasi (peringatan budget).
- **Page heading:** judul h1, satu kalimat subtitle, aksi di kanan (pemilih bulan, tombol utama).
- **Mobile (< 768px):** sidebar menjadi bottom navigation, page heading bertumpuk, tabel menjadi daftar.

---

## 5. Komponen

Setiap komponen menjadi satu template partial di `templates/components/`.

| Komponen | Spesifikasi |
|---|---|
| **Button (secondary)** | Tinggi 36px, background `surface`, border `border`, radius 6px, teks 13px/500. Hover: `hover` + `border-strong` |
| **Button (primary)** | Sama, background dan border `forest`, teks putih. Hover `forest-hover`. Maksimal satu per halaman |
| **Text button** | Tanpa border, teks `forest`, ikon panah kecil di kanan |
| **Icon button** | 36×36, tanpa border, hover `hover` |
| **Input / select** | Tinggi 40px, border `border-strong`, radius 6px, label di atas (13px/500 `secondary`). Focus: border `forest` + outline 2px |
| **Panel** | Background `surface`, border 1px `border`, radius 8px, tanpa bayangan. Header: section title + aksi kecil di kanan |
| **Category chip** | Radius 4px, padding 4px 8px, teks 12px, background warna kategori dengan transparansi tinggi, teks warna kategori yang lebih gelap, titik kecil di kiri |
| **Progress bar** | Tinggi 4px, radius 2px, latar `track`. Isi: `forest` (< 90%), `amber` (90–100%), `clay` (> 100%) |
| **Transaction row** | Ikon kategori dalam kotak `forest-tint` → nama merchant (14px/500) + catatan dan tanggal (caption) → chip kategori → wallet → nominal rata kanan |
| **Month picker** | Kotak 36px dengan ‹ › dan label "November 2026" |
| **Modal** | Lebar 480px, padding 28px, radius 8px. Header: judul + deskripsi + tombol tutup. Footer: garis atas, tombol rata kanan (Cancel, lalu aksi utama). Pakai `<dialog>` |
| **Toast** | Kanan bawah atau tengah bawah, ikon centang dalam lingkaran `forest-tint`, judul + satu kalimat, hilang sendiri setelah ±4 detik |
| **Empty state** | Ikon 48px dalam kotak `forest-tint`, judul 15px, satu kalimat, satu tombol aksi |
| **Status dot** | Lingkaran 6px, `forest` atau `clay`, di depan teks proyeksi |

---

## 6. Penulisan teks (copy)

Desain Figma memakai banyak kalimat puitis. Sebagian besar **dihapus**, karena kalimat seperti itulah yang membuat UI terasa ditulis AI.

**Hapus atau ganti:**
- Overline puitis di atas judul halaman: "A LITTLE CLARITY, EVERY DAY", "YOUR MONEY, WITH INTENTION", "A LITTLE PERSPECTIVE". Overline hanya dipakai untuk label data ("SPENT SO FAR", "TOTAL BALANCE").
- Kartu motivasi di sidebar ("A little today. A lot more tomorrow. Your future self will thank you.").
- Judul toast puitis ("A little more clarity."). Ganti dengan yang langsung: "Transaction added".
- Subtitle halaman yang terlalu manis. Buat informatif:
  - Dashboard: "Your money this month at a glance."
  - Transactions: "Every income and expense, by date."
  - Wallets: "Balances across your cash, bank and e-wallets."
  - Budget: "Monthly limits per category."
  - Savings goals: "Track progress toward what you're saving for."
  - Assistant: "Ask about your spending, or plan the rest of the month."
- Item nav "Design system" dan badge "NEW" di Assistant.
- Catatan "Preview only. Your changes last for this session."
- Nomor rekening palsu ("•••• 0821") di kartu wallet. Ganti dengan tipe wallet saja.

**Aturan umum:**
- Kalimat pendek, langsung, menyebut angka kalau ada.
- Label tombol berupa kata kerja: "Add transaction", "Save", "Transfer".
- Pesan error menjelaskan cara memperbaikinya: "Amount must be greater than 0."
- Tanpa emoji. Tanpa ikon sparkle untuk fitur AI.

---

## 7. Peta halaman dari desain

| Halaman | Elemen utama di desain | Penyesuaian |
|---|---|---|
| Dashboard | "Remaining this month" + proyeksi, total income/expense dengan sparkline, grafik pengeluaran harian dengan garis limit, spending by category, transaksi terbaru, satu baris insight | Filter wallet tetap ada. Baris insight diisi AI di MVP 7 |
| Transactions | Toolbar (search, filter wallet, filter kategori), ringkasan, tabel dikelompokkan per tanggal | Tambah input "quick add" di MVP 6 |
| Wallets | Total saldo sebagai angka utama, grid kartu wallet dengan monogram | Hapus nomor rekening palsu; tambah aksi Transfer |
| Budget | Ringkasan rencana bulanan + progress, daftar budget per kategori | Warna amber/clay sesuai status |
| Savings goals | Satu goal unggulan dengan ilustrasi garis, aksi "Add to savings" | Ditambah daftar beberapa goal (desain hanya menampilkan satu) |
| Assistant | Intro, prompt contoh bernomor, input, disclaimer | Kartu data, rencana, konfirmasi, dan file PDF dirancang di MVP 7 |
| Modal | Add transaction, edit budget, add to savings, help | Ikuti spesifikasi modal di atas |
