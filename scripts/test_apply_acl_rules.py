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

print("Testing adding ACL rules...")

user_attr_json = json.dumps({
    "name": "Departemen",
    "tableId": "USERS_DEPARTEMEN",
    "lookupColId": "Email",
    "charId": "Departemen"
})

ast_terima = '["Or", ["In", ["Attr", ["Name", "user"], "Access"], ["List", ["Name", "OWNER"]]], ["In", ["Attr", ["Name", "user"], "Departemen"], ["List", ["Attr", ["Name", "rec"], "Ke_Departemen"], ["Const", "ALL"]]]]'

# Step 1: Check existing resources
req = urllib.request.Request(f"{BASE_URL}/tables/_grist_ACLResources/records", headers={"Authorization": f"Bearer {API_KEY}"})
with urllib.request.urlopen(req) as resp:
    res_list = json.loads(resp.read())['records']
    print("Existing resources:", res_list)

# Step 2: Apply user attribute rule on resource 1
actions = [
    # 1. Add userAttributes definition rule
    ["AddRecord", "_grist_ACLRules", None, {
        "resource": 1,
        "rulePos": 1.0,
        "userAttributes": user_attr_json,
        "memo": "Map user.Email to USERS_DEPARTEMEN.Departemen"
    }],
    # 2. Add ACL Resource for Qty_Terima columns
    ["AddRecord", "_grist_ACLResources", None, {
        "tableId": "MUTASI_ANTAR_DEPARTEMEN",
        "colIds": "Qty_Terima,Admin_Terima,Tgl_Terima,Catatan_Koreksi"
    }]
]

res = apply_actions(actions)
print("Step 1 result:", res)
res_id = res['retValues'][1]
print("New Resource ID:", res_id)

# Step 3: Add rules for resource_id
rule_actions = [
    ["AddRecord", "_grist_ACLRules", None, {
        "resource": res_id,
        "rulePos": 1.0,
        "aclFormula": 'user.Access in [OWNER] or user.Departemen in [rec.Ke_Departemen, "ALL"]',
        "aclFormulaParsed": ast_terima,
        "permissionsText": "+U",
        "memo": "Hanya departemen tujuan yang boleh mengisi Qty Terima"
    }],
    ["AddRecord", "_grist_ACLRules", None, {
        "resource": res_id,
        "rulePos": 2.0,
        "aclFormula": "",
        "aclFormulaParsed": "",
        "permissionsText": "-U",
        "memo": "Departemen lain dikunci (Read Only)"
    }]
]

res2 = apply_actions(rule_actions)
print("Step 2 result:", res2)

