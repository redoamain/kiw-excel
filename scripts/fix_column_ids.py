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

print("1. Renaming column IDs cleanly to Qty_Kirim and Admin_Kirim...")
actions = [
    ["RenameColumn", "MUTASI_ANTAR_DEPARTEMEN", "Qty_Kirim_Pengirim_", "Qty_Kirim"],
    ["RenameColumn", "MUTASI_ANTAR_DEPARTEMEN", "Admin_Kirim_Pengirim_", "Admin_Kirim"],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Qty_Kirim", {"label": "Qty_Kirim (Pengirim)", "type": "Numeric"}],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Admin_Kirim", {"label": "Admin_Kirim (Pengirim)", "type": "Text"}],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Selisih_Qty", {
        "formula": "(float($Qty_Terima or 0) - float($Qty_Kirim or 0)) if $Qty_Terima is not None else 0",
        "isFormula": True
    }],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Status_Penerimaan", {
        "formula": "'PROSES KIRIM' if $Qty_Terima is None else ('DITERIMA (COCOK)' if float($Qty_Terima or 0) == float($Qty_Kirim or 0) else 'SELISIH (DISPUTE)')",
        "isFormula": True,
        "type": "Choice",
        "widgetOptions": json.dumps({
            "choices": ["DITERIMA (COCOK)", "PROSES KIRIM", "SELISIH (DISPUTE)"],
            "choiceOptions": {
                "DITERIMA (COCOK)": {"fillColor": "#D1E7DD", "textColor": "#0F5132", "fontBold": True},
                "PROSES KIRIM": {"fillColor": "#FFF3CD", "textColor": "#664D03", "fontBold": True},
                "SELISIH (DISPUTE)": {"fillColor": "#F8D7DA", "textColor": "#842029", "fontBold": True}
            }
        })
    }]
]

res = apply_actions(actions)
print("Result of apply:", res)

# Update existing records so Qty_Terima = Qty_Kirim
req = urllib.request.Request(f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    recs = json.loads(resp.read())['records']

update_records = []
for r in recs:
    rid = r['id']
    f = r['fields']
    qty_kirim = f.get('Qty_Kirim', 0)
    update_records.append({
        "id": rid,
        "fields": {
            "Qty_Terima": qty_kirim,
            "Admin_Terima": "Admin Penerima (Verified)",
            "Tgl_Terima": f.get("Tanggal")
        }
    })

req = urllib.request.Request(
    f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records",
    data=json.dumps({"records": update_records}).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="PATCH"
)
with urllib.request.urlopen(req) as resp:
    print("Updated Qty_Terima in records:", resp.status)

