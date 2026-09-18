# kiw-excel (Citiplumb Spreadsheet & Relational Database)

Sistem database relasional modern berbasis spreadsheet **kiw-excel** (berbasis [Grist Core](https://github.com/gristlabs/grist-core)) yang telah disesuaikan dengan identitas nama **kiw-excel**, tema warna **biru (Blue Base Palette)**, akun departemen pabrik **Citiplumb**, dan sistem **Backup Eksternal Otomatis (Hot Backup SQLite & Cloud Sync)**.

---

## 📁 Struktur Direktori

```text
grist/
├── docker-compose.yml   # Definisi container (kiw-excel + backup service)
├── Dockerfile.backup    # Image container backup mandiri (Alpine + SQLite + Rclone)
├── .env                 # Konfigurasi aktif (port, secret, branding, akun, backup)
├── .env.example         # Template konfigurasi
├── .gitignore           # Menjaga data, arsip backup & file sensitif tidak ter-commit
├── custom.css           # Kustomisasi tema warna biru & UI kiw-excel
├── dex.yaml             # Konfigurasi branding IdP Dex (Issuer: kiw-excel)
├── dex-styles.css       # Tema biru untuk layar login Dex
├── logo.svg             # Logo vektor kustom kiw-excel
├── favicon.png          # Favicon kustom kiw-excel untuk tab browser
├── favicon.ico          # Favicon format ICO
├── scripts/             # Skrip automasi backup & restore
│   ├── backup.sh        # Hot-backup SQLite aman + rotasi otomatis + checksum
│   ├── entrypoint.sh    # Cron daemon scheduler backup
│   └── restore.sh       # Skrip pemulihan database & dokumen 1 langkah
├── backups/             # Direktori arsip backup (tar.gz + sha256)
├── grist-data/          # Data persisten (database SQLite, metadata, dokumen)
└── README.md            # Panduan penggunaan lengkap
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

4. Cek status container:
   ```bash
   docker compose ps
   ```

5. Untuk menghentikan:
   ```bash
   docker compose down
   ```

---

## 💾 Sistem Backup Eksternal (Automated Hot Backup)

Sistem telah dilengkapi dengan service backup otomatis (`kiw-excel-backup`) yang bekerja secara aman di latar belakang tanpa memutus akses pengguna:

### 1. Keunggulan Backup
- **Zero-Downtime Hot Backup**: Menggunakan perintah native SQLite `.backup` untuk `home.sqlite3`, `auth/dex.db`, dan setiap dokumen spreadsheet (`*.grist`), menjamin **integritas data 100% tanpa korupsi** meskipun sedang ada penulisan data aktif.
- **Jadwal Otomatis (Cron)**: Dijalankan otomatis sesuai jadwal di `.env` (default: setiap hari jam 02:00 WIB via `BACKUP_CRON="0 2 * * *"`).
- **Startup Backup**: Membuat backup instan otomatis saat container pertama kali dinyalakan.
- **Rotasi Otomatis**: Otomatis menghapus arsip lama yang melebihi batas retensi (default: 14 hari via `BACKUP_RETENTION_DAYS=14`).
- **Verifikasi SHA256**: Setiap arsip `.tar.gz` dilengkapi dengan berkas `.sha256` untuk verifikasi integritas data.

### 2. Menjalankan Backup Manual (Kapan Saja)
Anda dapat memicu pembuatan backup kapan saja tanpa menunggu jadwal cron:
```bash
docker compose exec backup /scripts/backup.sh
```

### 3. Menyimpan Backup ke Harddisk Eksternal / NAS
Jika ingin menyimpan arsip backup langsung ke flashdisk, external HDD, atau shared folder NAS:
Cukup ubah variabel `BACKUP_DIR` di file `.env`:
```env
BACKUP_DIR=/mnt/external_drive/kiw-excel-backups
```
Lalu jalankan `docker compose up -d`.

### 4. Sinkronisasi Cloud Eksternal (Google Drive / Wasabi / S3 / SFTP)
Service backup telah dilengkapi dengan utility `rclone`.
1. Letakkan konfigurasi remote rclone Anda di `./rclone.conf`.
2. Aktifkan destinasi pada `.env`:
   ```env
   RCLONE_REMOTE_DEST=gdrive:kiw-excel-backups
   ```
Setiap kali backup selesai dibuat, arsip akan otomatis disalin ke cloud offsite Anda.

### 5. Native S3 / MinIO / Cloudflare R2 Storage (Opsional)
Grist juga mendukung streaming snapshot dokumen langsung ke S3 bucket. Aktifkan pada `.env`:
```env
GRIST_DOCS_MINIO_BUCKET=nama-bucket
GRIST_DOCS_MINIO_ENDPOINT=s3.us-east-1.amazonaws.com
GRIST_DOCS_MINIO_PORT=443
GRIST_DOCS_MINIO_ACCESS_KEY=your-access-key
GRIST_DOCS_MINIO_SECRET_KEY=your-secret-key
GRIST_DOCS_MINIO_USE_SSL=true
GRIST_DOCS_MINIO_BUCKET_REGION=us-east-1
GRIST_DOCS_MINIO_PREFIX=docs/
```

---

## 🔄 Cara Melakukan Restore (Pemulihan Data)

Jika terjadi masalah atau ingin memulihkan data dari arsip backup tertentu:

1. Pilih berkas arsip dari folder `./backups/`.
2. Jalankan skrip restore:
   ```bash
   ./scripts/restore.sh ./backups/kiw-excel-backup-2026-09-18_13-19-25.tar.gz
   ```
3. Restart container agar Grist membaca database hasil restore:
   ```bash
   docker compose restart grist
   ```

---

## 🎨 Kustomisasi Branding & Tema (kiw-excel)

- **Nama Aplikasi**: Judul browser menampilkan akhiran **`- kiw-excel`**.
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
| `BACKUP_CRON` | Jadwal backup harian | `0 2 * * *` (Jam 02:00) |
| `BACKUP_RETENTION_DAYS` | Masa simpan arsip backup (hari) | `14` |
| `BACKUP_DIR` | Folder destinasi backup di host | `./backups` |
| `TZ` | Zona waktu backup scheduler | `Asia/Jakarta` |
