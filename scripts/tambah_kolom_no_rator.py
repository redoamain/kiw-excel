import urllib.request
import json

API_KEY = "citiplumb-admin-api-key-secret"
DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

def apply_actions(actions):
    req = urllib.request.Request(
        f"{BASE_URL}/apply",
        data=json.dumps(actions).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

print("1. Menambahkan kolom No_Rator ke tabel MUTASI_ANTAR_DEPARTEMEN...")
actions = [
    ["AddColumn", "MUTASI_ANTAR_DEPARTEMEN", "No_Rator", {
        "label": "No. Rator",
        "type": "Text",
        "untieColIdFromLabel": True
    }]
]
res = apply_actions(actions)
col_ref = res['retValues'][0]['colRef']
print(f"✅ Kolom No_Rator berhasil dibuat dengan colRef: {col_ref}")

# 2. Menambahkan ke tampilan Section 4 (grid mutasi) di posisi 1.5 (setelah Tanggal)
sec_field = {
    "records": [{
        "fields": {
            "parentId": 4,
            "colRef": col_ref,
            "parentPos": 1.5
        }
    }]
}
req = urllib.request.Request(
    f"{BASE_URL}/tables/_grist_Views_section_field/records",
    data=json.dumps(sec_field).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    print("✅ No. Rator berhasil disematkan di posisi grid setelah Tanggal:", resp.status)

# 3. Update Access Rules Resource 3 agar No_Rator masuk hak akses pengirim
req = urllib.request.Request(
    f"{BASE_URL}/tables/_grist_ACLResources/records",
    data=json.dumps({'records': [{
        'id': 3,
        'fields': {'colIds': 'Qty_Kirim,Admin_Kirim,Tanggal,Kode_Barang,Dari_Departemen,Ke_Departemen,Grade,No_Rator'}
    }]}).encode('utf-8'),
    headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    print("✅ Access Rules diperbarui mencakup No_Rator:", resp.status)

# 4. Beri contoh nomorator pada data sampel
req = urllib.request.Request(f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    recs = json.loads(resp.read())['records']

sample_rators = ["1082611", "3082611", "4082611", "5082611", "7082611", "8082611", "10082611"]
update_records = []
for i, r in enumerate(recs):
    update_records.append({
        "id": r['id'],
        "fields": {"No_Rator": sample_rators[i % len(sample_rators)]}
    })

if update_records:
    req = urllib.request.Request(
        f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records",
        data=json.dumps({"records": update_records}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        print("✅ Data sampel nomorator berhasil diisi:", resp.status)

