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

ast_kirim = '["Or", ["In", ["Attr", ["Name", "user"], "Access"], ["List", ["Name", "OWNER"]]], ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Dari_Departemen"], ["Const", "ALL"]]]]'

# Step 1: Add ACL Resource for sender columns
res = apply_actions([
    ["AddRecord", "_grist_ACLResources", None, {
        "tableId": "MUTASI_ANTAR_DEPARTEMEN",
        "colIds": "Qty_Kirim,Admin_Kirim,Tanggal,Kode_Barang,Dari_Departemen,Ke_Departemen"
    }]
])
res_id = res['retValues'][0]
print("Created Resource 3 for sender columns with ID:", res_id)

# Step 2: Add rules for sender columns
rules = [
    ["AddRecord", "_grist_ACLRules", None, {
        "resource": res_id,
        "rulePos": 1.0,
        "aclFormula": 'user.Access in [OWNER] or user.Departemen in [rec.Dari_Departemen, "ALL"]',
        "aclFormulaParsed": ast_kirim,
        "permissionsText": "+U",
        "memo": "Hanya departemen pengirim yang boleh mengubah Qty Kirim"
    }],
    ["AddRecord", "_grist_ACLRules", None, {
        "resource": res_id,
        "rulePos": 2.0,
        "aclFormula": "",
        "aclFormulaParsed": "",
        "permissionsText": "-U",
        "memo": "Penerima/departemen lain tidak boleh mengubah Qty Kirim pengirim"
    }]
]
res2 = apply_actions(rules)
print("Added sender protection rules:", res2)
