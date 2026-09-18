# kiw-excel (Citiplumb Spreadsheet & Relational Database)

Sistem database relasional modern berbasis spreadsheet **kiw-excel** (berbasis [Grist Core](https://github.com/gristlabs/grist-core)) yang telah disesuaikan dengan identitas nama **kiw-excel**, tema warna **biru (Blue Base Palette)**, dan akun departemen pabrik **Citiplumb**.

---

## 📁 Struktur Direktori

```text
grist/
├── docker-compose.yml   # Definisi container dan volume mounting
├── .env                 # Konfigurasi aktif (port, secret, branding, akun)
├── .env.example         # Template konfigurasi
├── .gitignore           # Menjaga data & file sensitif tidak ter-commit
├── custom.css           # Kustomisasi tema warna biru & UI kiw-excel
├── logo.svg             # Logo vektor kustom kiw-excel (Spreadsheet grid & Blue style)
├── favicon.png          # Favicon kustom kiw-excel untuk tab browser
├── dex.yaml             # Konfigurasi branding IdP Dex (Issuer: kiw-excel)
├── dex-styles.css       # Tema biru untuk halaman login Dex
├── grist-data/          # Data persisten (database SQLite, metadata, auth)
└── README.md            # Panduan penggunaan
```

---

## 🚀 Cara Menjalankan (Quick Start)

1. Masuk ke direktori:
   ```bash
   cd grist
   ```

2. Jalankan container:
   ```bash
   docker compose up -d
   ```

3. Buka di browser:
   **[http://localhost:8484](http://localhost:8484)**

4. Cek log jika diperlukan:
   ```bash
   docker compose logs -f grist
   ```

5. Untuk menghentikan:
   ```bash
   docker compose down
   ```

---

## 🎨 Kustomisasi Branding & Tema (kiw-excel)

Aplikasi ini telah dikonfigurasi penuh dengan branding **kiw-excel**:
- **Nama Aplikasi**: Judul browser menampilkan `... - kiw-excel` (diatur via `GRIST_PAGE_TITLE_SUFFIX=" - kiw-excel"`).
- **Halaman Login**: Menampilkan judul *"Log in to kiw-excel"* lengkap dengan logo kustom dan tema tombol biru.
- **Warna Dasar Biru**:
  - Tombol aksi utama (Primary buttons): `#2563eb` (hover: `#1d4ed8`)
  - Tombol tambah data (+ Add New): `#2563eb`
  - Border cursor sel aktif & seleksi rentang sel: `#2563eb` dengan transparansi biru muda
  - Animasi startup loading: kombinasi gradasi biru `#2563eb`, `#3b82f6`, `#93c5fd`
  - Mendukung tema terang (Light) maupun gelap (Dark).
- **Logo Kustom**: Logo spreadsheet bergaya biru modern terintegrasi di pojok kiri atas, layar login Dex, dan favicon tab browser.

---

## 👥 Daftar Akun Departemen (Citiplumb)

Sistem autentikasi telah disiapkan dengan 9 akun (1 Admin + 8 Departemen) pada organisasi **citiplumb**:

| No | Departemen / Role | Email Login | Password Default | Akses Default |
|:---|:---|:---|:---|:---|
| 0 | **Admin / IT** | `admin@citiplumb.local` | `AdminPass123!` | Owner |
| 1 | **Gudang Lokal** | `gudang.lokal@citiplumb.local` | `GudangLokal123!` | Editor |
| 2 | **Gudang Impor** | `gudang.impor@citiplumb.local` | `GudangImpor123!` | Editor |
| 3 | **Kepala Gudang** | `kepala.gudang@citiplumb.local` | `KepalaGudang123!` | Editor |
| 4 | **PPIC** | `ppic@citiplumb.local` | `PpicPass123!` | Editor |
| 5 | **Plating** | `plating@citiplumb.local` | `PlatingPass123!` | Editor |
| 6 | **Injeksi** | `injeksi@citiplumb.local` | `InjeksiPass123!` | Editor |
| 7 | **Spray** | `spray@citiplumb.local` | `SprayPass123!` | Editor |
| 8 | **Assembly** | `assembly@citiplumb.local` | `AssemblyPass123!` | Editor |

> **Catatan:**
> - Semua akun dan password dapat disesuaikan pada file `.env`.
> - Pengguna dapat login dan berpindah akun melalui menu profil di pojok kanan atas.
> - Hak akses per dokumen atau workspace (Owner / Editor / Viewer) dapat diatur langsung oleh Admin.

---

## ⚙️ Variabel Konfigurasi Utama (`.env`)

| Variabel | Keterangan | Nilai Default |
|:---|:---|:---|
| `GRIST_PORT` | Port host HTTP | `8484` |
| `APP_HOME_URL` | URL dasar publik yang diakses user | `http://localhost:8484` |
| `TEAM` | Nama team / organisasi | `citiplumb` |
| `GRIST_PAGE_TITLE_SUFFIX` | Akhiran judul tab browser | ` - kiw-excel` |
| `APP_STATIC_INCLUDE_CUSTOM_CSS` | Memuat custom.css | `true` |
| `GRIST_HIDE_UI_ELEMENTS` | Menyembunyikan elemen promo bawaan | `helpCenter,billing,templates,supportGrist` |
| `GRIST_WIDGET_LIST_URL` | Galeri widget eksternal | Manifest resmi Grist |
| `GRIST_SANDBOX_FLAVOR` | Isolasi formula Python | `gvisor` |

---

## 🔒 Menjalankan di Production (HTTPS / Domain)

Jika ingin mengekspos `kiw-excel` ke domain publik:
1. Ubah `APP_HOME_URL=https://excel.domainanda.com` di file `.env`.
2. Gunakan reverse proxy (Nginx / Caddy / Traefik / Cloudflare Tunnel) yang mengarah ke `http://127.0.0.1:8484` dengan header forward:
   - `Host: $host`
   - `X-Forwarded-Proto: https`
   - `X-Forwarded-For: $remote_addr`
3. Restart container: `docker compose up -d`.

---

## 💾 Backup & Restore

Semua dokumen spreadsheet, database SQLite, konfigurasi metadata, dan user tersimpan dalam folder:
```
./grist-data/
```
- **Backup**: Cukup salin / arsipkan folder `./grist-data/`.
- **Restore**: Kembalikan folder `./grist-data/` sebelum menjalankan `docker compose up -d`.
