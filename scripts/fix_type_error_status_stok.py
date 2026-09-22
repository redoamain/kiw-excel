import urllib.request
import json

API_KEY = "citiplumb-admin-api-key-secret"
DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

print("==================================================================")
print("🔧 MEMPERBAIKI TYPEERROR STATUS STOK DI SELURUH TABEL")
print("==================================================================")

actions = [
    # 1. INJEKSI_LOKAL: Ubah semua kolom angka jadi Numeric dan perbaiki formula Status_Stok
    ["ModifyColumn", "INJEKSI_LOKAL", "Stok_Awal", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Total_IN", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Total_OUT", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Stok_Akhir", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Adj_Masuk", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Adj_Keluar", {"type": "Numeric"}],
    ["ModifyColumn", "INJEKSI_LOKAL", "Status_Stok", {
        "type": "Choice",
        "formula": "'AMAN' if float($Stok_Akhir or 0) > 500 else ('MENIPIS' if float($Stok_Akhir or 0) > 0 else 'HABIS (0)')",
        "isFormula": True,
        "widgetOptions": json.dumps({"choices": ["AMAN", "MENIPIS", "HABIS (0)"]})
    }],

    # 2. PLATING_WIP
    ["ModifyColumn", "PLATING_WIP", "Stok_Awal", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Total_IN", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Total_OUT", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Stok_Akhir_WIP", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Adj_Masuk", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Adj_Keluar", {"type": "Numeric"}],
    ["ModifyColumn", "PLATING_WIP", "Status_Stok", {
        "type": "Choice",
        "formula": "'WIP READY' if float($Stok_Akhir_WIP or 0) > 0 else 'KOSONG'",
        "isFormula": True,
        "widgetOptions": json.dumps({"choices": ["WIP READY", "KOSONG"]})
    }],

    # 3. SPRAY_WIP
    ["ModifyColumn", "SPRAY_WIP", "Stok_Awal", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Total_IN", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Total_OUT", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Stok_Akhir_WIP", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Adj_Masuk", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Adj_Keluar", {"type": "Numeric"}],
    ["ModifyColumn", "SPRAY_WIP", "Status_Stok", {
        "type": "Choice",
        "formula": "'WIP READY' if float($Stok_Akhir_WIP or 0) > 0 else 'KOSONG'",
        "isFormula": True,
        "widgetOptions": json.dumps({"choices": ["WIP READY", "KOSONG"]})
    }],

    # 4. GUDANG_IMPOR_CHINA
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Stok_Awal", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Total_IN", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Total_OUT", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Stok_Akhir", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Adj_Masuk", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Adj_Keluar", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Status_Stok", {
        "type": "Choice",
        "formula": "'TERSEDIA' if float($Stok_Akhir or 0) > 500 else ('MENIPIS' if float($Stok_Akhir or 0) > 0 else 'HABIS (0)')",
        "isFormula": True,
        "widgetOptions": json.dumps({"choices": ["TERSEDIA", "MENIPIS", "HABIS (0)"]})
    }],

    # 5. GUDANG_KARTON
    ["ModifyColumn", "GUDANG_KARTON", "Stok_Awal", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Total_IN", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Total_OUT", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Stok_Akhir", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Adj_Masuk", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Adj_Keluar", {"type": "Numeric"}],
    ["ModifyColumn", "GUDANG_KARTON", "Status_Stok", {
        "type": "Choice",
        "formula": "'TERSEDIA' if float($Stok_Akhir or 0) > 200 else ('MENIPIS' if float($Stok_Akhir or 0) > 0 else 'HABIS (0)')",
        "isFormula": True,
        "widgetOptions": json.dumps({"choices": ["TERSEDIA", "MENIPIS", "HABIS (0)"]})
    }]
]

req = urllib.request.Request(
    f"{BASE_URL}/apply",
    data=json.dumps(actions).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    print(f"✅ Selesai! Status update: {resp.status}")

print("TypeError pada Status Stok berhasil diperbaiki di semua tabel!")
