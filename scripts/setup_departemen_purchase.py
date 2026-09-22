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

print("1. Menambahkan 'PURCHASE' ke pilihan Departemen di MUTASI_ANTAR_DEPARTEMEN...")

dept_choices = [
    "PURCHASE",
    "INJEKSI",
    "GUDANG LOKAL",
    "GUDANG IMPOR",
    "PLATING",
    "SPRAY",
    "ASSEMBLY",
    "GUDANG FG",
    "QC & RND",
    "VENDOR LUAR",
    "REJECT / SCRAP"
]

choice_options = {
    "PURCHASE": {"fillColor": "#CCFBF1", "textColor": "#0F766E", "fontBold": True},
    "INJEKSI": {"fillColor": "#E0E7FF", "textColor": "#3730A3", "fontBold": True},
    "GUDANG LOKAL": {"fillColor": "#E0F2FE", "textColor": "#0369A1", "fontBold": True},
    "GUDANG IMPOR": {"fillColor": "#FCE7F3", "textColor": "#9D174D", "fontBold": True},
    "PLATING": {"fillColor": "#FEF3C7", "textColor": "#92400E", "fontBold": True},
    "SPRAY": {"fillColor": "#F3E8FF", "textColor": "#6B21A8", "fontBold": True},
    "ASSEMBLY": {"fillColor": "#DCFCE7", "textColor": "#166534", "fontBold": True},
    "GUDANG FG": {"fillColor": "#D1FAE5", "textColor": "#065F46", "fontBold": True},
    "QC & RND": {"fillColor": "#FFEDD5", "textColor": "#9A3412", "fontBold": True},
    "VENDOR LUAR": {"fillColor": "#F1F5F9", "textColor": "#475569", "fontBold": True},
    "REJECT / SCRAP": {"fillColor": "#FEE2E2", "textColor": "#991B1B", "fontBold": True}
}

dept_widget_options = json.dumps({
    "choices": dept_choices,
    "choiceOptions": choice_options
})

actions = [
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Dari_Departemen", {
        "widgetOptions": dept_widget_options
    }],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Ke_Departemen", {
        "widgetOptions": dept_widget_options
    }]
]
res = apply_actions(actions)
print("✅ Departemen PURCHASE berhasil ditambahkan ke pilihan dropdown:", res)

# 2. Tambah akun purchase ke USERS_DEPARTEMEN
req = urllib.request.Request(f"{BASE_URL}/tables/USERS_DEPARTEMEN/records", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    users = json.loads(resp.read())['records']
    emails = [u['fields'].get('Email') for u in users]

if "purchase@citiplumb.local" not in emails:
    new_user = {
        "fields": {
            "Email": "purchase@citiplumb.local",
            "Nama_Admin": "Admin Purchase",
            "Departemen": "PURCHASE",
            "Keterangan": "Bagian Pengadaan & Pembelian Vendor (PO)"
        }
    }
    req = urllib.request.Request(
        f"{BASE_URL}/tables/USERS_DEPARTEMEN/records",
        data=json.dumps({"records": [new_user]}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        print("✅ Akun purchase@citiplumb.local ditambahkan ke USERS_DEPARTEMEN:", resp.status)
else:
    print("Akun purchase@citiplumb.local sudah ada di USERS_DEPARTEMEN.")

# 3. Update Access Rules Resource 3 agar Purchase dapat mengisi Qty Kirim (PO)
new_formula = 'user.Access in [OWNER] or user.Departemen in [rec.Dari_Departemen, "ALL", "PPIC", "PURCHASE"] or (rec.Kategori_Mutasi == "PEMBELIAN VENDOR" and user.Departemen in [rec.Ke_Departemen, "GUDANG LOKAL", "GUDANG IMPOR", "INJEKSI", "PURCHASE"])'

new_ast = json.dumps([
    "Or", 
    ["In", ["Attr", ["Name", "user"], "Access"], ["List", ["Name", "OWNER"]]], 
    ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Dari_Departemen"], ["Const", "ALL"], ["Const", "PPIC"], ["Const", "PURCHASE"]]], 
    ["And", 
        ["Eq", ["Attr", ["Name", "rec"], "Kategori_Mutasi"], ["Const", "PEMBELIAN VENDOR"]], 
        ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Ke_Departemen"], ["Const", "GUDANG LOKAL"], ["Const", "GUDANG IMPOR"], ["Const", "INJEKSI"], ["Const", "PURCHASE"]]]
    ]
])

req = urllib.request.Request(
    f"{BASE_URL}/tables/_grist_ACLRules/records",
    data=json.dumps({'records': [{
        'id': 5,
        'fields': {
            'aclFormula': new_formula,
            'aclFormulaParsed': new_ast,
            'memo': 'Admin Purchase, Pengirim, atau Gudang Penerima Pembelian boleh mengisi Qty Kirim'
        }
    }]}).encode('utf-8'),
    headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    print("✅ Access Rules diperbarui untuk hak akses Admin Purchase:", resp.status)

# 4. Ubah sampel pembelian id 8 dan 9 menjadi Dari_Departemen: PURCHASE
req = urllib.request.Request(
    f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records",
    data=json.dumps({'records': [
        {
            'id': 8,
            'fields': {
                'Dari_Departemen': 'PURCHASE',
                'Admin_Kirim': 'Admin Purchase (Rina) / Vendor: PT Inti Box',
                'Keterangan': 'PO 12661 Pembelian Karton Box'
            }
        },
        {
            'id': 9,
            'fields': {
                'Dari_Departemen': 'PURCHASE',
                'Admin_Kirim': 'Admin Purchase (Import) / Supplier: Ningbo',
                'Keterangan': 'PO Impor China Kontainer Part Kran'
            }
        }
    ]}).encode('utf-8'),
    headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    print("✅ Sampel mutasi diselaraskan dari departemen PURCHASE:", resp.status)

