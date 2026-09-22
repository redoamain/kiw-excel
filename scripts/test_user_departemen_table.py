import urllib.request
import json

API_KEY = "citiplumb-admin-api-key-secret"
DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

# 1. Create USERS_DEPARTEMEN table if it does not exist
req = urllib.request.Request(f"{BASE_URL}/tables", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    tables = [t['id'] for t in json.loads(resp.read())['tables']]

if "USERS_DEPARTEMEN" not in tables:
    print("Creating USERS_DEPARTEMEN table...")
    table_data = {
        "tables": [{
            "id": "USERS_DEPARTEMEN",
            "columns": [
                {"id": "Email", "type": "Text", "label": "Email"},
                {"id": "Nama_Admin", "type": "Text", "label": "Nama Admin"},
                {"id": "Departemen", "type": "Choice", "label": "Departemen"},
                {"id": "Keterangan", "type": "Text", "label": "Keterangan"}
            ]
        }]
    }
    req = urllib.request.Request(
        f"{BASE_URL}/tables",
        data=json.dumps(table_data).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        print("Created USERS_DEPARTEMEN table:", resp.status)
else:
    print("USERS_DEPARTEMEN table already exists.")

# 2. Populate users
records = [
    {"fields": {"Email": "admin@citiplumb.local", "Nama_Admin": "Admin Citiplumb (Owner)", "Departemen": "ALL", "Keterangan": "Super Admin Semua Dept"}},
    {"fields": {"Email": "kepala.gudang@citiplumb.local", "Nama_Admin": "Kepala Gudang", "Departemen": "ALL", "Keterangan": "Pengawas Semua Gudang"}},
    {"fields": {"Email": "injeksi@citiplumb.local", "Nama_Admin": "Admin Injeksi", "Departemen": "INJEKSI", "Keterangan": "Admin Produksi Injeksi"}},
    {"fields": {"Email": "spray@citiplumb.local", "Nama_Admin": "Admin Spray", "Departemen": "SPRAY", "Keterangan": "Admin Painting & Spray"}},
    {"fields": {"Email": "plating@citiplumb.local", "Nama_Admin": "Admin Plating", "Departemen": "PLATING", "Keterangan": "Admin Plating & Chrome"}},
    {"fields": {"Email": "gudang.lokal@citiplumb.local", "Nama_Admin": "Admin Gudang Lokal", "Departemen": "GUDANG LOKAL", "Keterangan": "Admin Gudang Bahan Lokal"}},
    {"fields": {"Email": "gudang.impor@citiplumb.local", "Nama_Admin": "Admin Gudang Impor", "Departemen": "GUDANG IMPOR", "Keterangan": "Admin Bahan Impor China"}},
    {"fields": {"Email": "assembly@citiplumb.local", "Nama_Admin": "Admin Assembly", "Departemen": "ASSEMBLY", "Keterangan": "Admin Perakitan Akhir"}},
    {"fields": {"Email": "ppic@citiplumb.local", "Nama_Admin": "PPIC & QC", "Departemen": "PPIC", "Keterangan": "Perencanaan & Mutu Produksi"}},
]

req = urllib.request.Request(
    f"{BASE_URL}/tables/USERS_DEPARTEMEN/records",
    data=json.dumps({"records": records}).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    print("Populated USERS_DEPARTEMEN records:", resp.status)

