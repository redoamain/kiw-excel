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

grade_widget_options = json.dumps({
    "choices": ["GRADE A", "GRADE B", "GRADE C"],
    "choiceOptions": {
        "GRADE A": {"fillColor": "#D1E7DD", "textColor": "#0F5132", "fontBold": True},
        "GRADE B": {"fillColor": "#CFE2FF", "textColor": "#084298", "fontBold": True},
        "GRADE C": {"fillColor": "#FFE5D0", "textColor": "#A04000", "fontBold": True}
    }
})

print("1. Menambahkan kolom Grade di MUTASI_ANTAR_DEPARTEMEN...")
actions = [
    ["AddColumn", "MUTASI_ANTAR_DEPARTEMEN", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "MASTER_KODE_BARANG", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "INJEKSI_LOKAL", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "PLATING_WIP", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "SPRAY_WIP", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "GUDANG_IMPOR_CHINA", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }],
    ["AddColumn", "GUDANG_KARTON", "Grade", {
        "label": "Grade",
        "type": "Choice",
        "widgetOptions": grade_widget_options
    }]
]

res = apply_actions(actions)
print("Hasil AddColumn:", res)

# Update existing records in MUTASI_ANTAR_DEPARTEMEN to default GRADE A
req = urllib.request.Request(f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    recs = json.loads(resp.read())['records']

update_records = []
for r in recs:
    update_records.append({
        "id": r['id'],
        "fields": {"Grade": "GRADE A"}
    })

if update_records:
    req = urllib.request.Request(
        f"{BASE_URL}/tables/MUTASI_ANTAR_DEPARTEMEN/records",
        data=json.dumps({"records": update_records}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="PATCH"
    )
    with urllib.request.urlopen(req) as resp:
        print("Updated MUTASI records with default GRADE A:", resp.status)

