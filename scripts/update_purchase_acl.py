import urllib.request
import json

API_KEY = "citiplumb-admin-api-key-secret"
DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

new_formula = 'user.Access in [OWNER] or user.Departemen in [rec.Dari_Departemen, "ALL", "PPIC"] or (rec.Kategori_Mutasi == "PEMBELIAN VENDOR" and user.Departemen in [rec.Ke_Departemen, "GUDANG LOKAL", "GUDANG IMPOR", "INJEKSI"])'

new_ast = json.dumps([
    "Or", 
    ["In", ["Attr", ["Name", "user"], "Access"], ["List", ["Name", "OWNER"]]], 
    ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Dari_Departemen"], ["Const", "ALL"], ["Const", "PPIC"]]], 
    ["And", 
        ["Eq", ["Attr", ["Name", "rec"], "Kategori_Mutasi"], ["Const", "PEMBELIAN VENDOR"]], 
        ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Ke_Departemen"], ["Const", "GUDANG LOKAL"], ["Const", "GUDANG IMPOR"], ["Const", "INJEKSI"]]]
    ]
])

req = urllib.request.Request(
    f"{BASE_URL}/tables/_grist_ACLRules/records",
    data=json.dumps({'records': [{
        'id': 5,
        'fields': {
            'aclFormula': new_formula,
            'aclFormulaParsed': new_ast,
            'memo': 'Pengirim/PPIC atau Gudang Penerima Pembelian Vendor boleh mengisi Qty Kirim'
        }
    }]}).encode('utf-8'),
    headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
    method='PATCH'
)
with urllib.request.urlopen(req) as resp:
    print("✅ Access Rules untuk Pembelian Gudang Lokal & Impor berhasil diaktifkan:", resp.status)

