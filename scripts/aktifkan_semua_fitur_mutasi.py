import urllib.request
import json

API_KEY = "citiplumb-admin-api-key-secret"
DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

print("==================================================================")
print("⚡ MENGAKTIFKAN SEMUA FORMULA DINAMIS DI SELURUH TABEL DEPARTEMEN")
print("==================================================================")

actions = [
    # --- 1. MUTASI_ANTAR_DEPARTEMEN ---
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Satuan", {
        "formula": "$Kode_Barang.Satuan if $Kode_Barang else 'PCS'",
        "isFormula": True
    }],

    # --- 2. INJEKSI_LOKAL ---
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Hasil_Produksi", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='HASIL PRODUKSI'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Pembelian", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='PEMBELIAN VENDOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Retur", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='RETUR', Ke_Departemen='INJEKSI'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Total_IN", {
        "formula": "float($IN_Hasil_Produksi or 0) + float($IN_Pembelian or 0) + float($IN_Retur or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Plating", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='PLATING'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Spray", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_QC_PPIC", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='QC & RND'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Reject", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Total_OUT", {
        "formula": "float($OUT_Ke_Plating or 0) + float($OUT_Ke_Spray or 0) + float($OUT_Ke_Assembly or 0) + float($OUT_Ke_QC_PPIC or 0) + float($OUT_Reject or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Stok_Akhir", {
        "formula": "float($Stok_Awal or 0) + float($Total_IN or 0) - float($Total_OUT or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Status_Stok", {
        "formula": "'AMAN' if $Stok_Akhir > 500 else ('MENIPIS' if $Stok_Akhir > 0 else 'HABIS (0)')",
        "isFormula": True
    }],

    # --- 3. PLATING_WIP ---
    ["ModifyColumn", "PLATING_WIP", "IN_Barang_Masuk", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='PLATING'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Total_IN", {
        "formula": "float($IN_Barang_Masuk or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_Spray", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_QC_RND", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='QC & RND'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Reject", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Total_OUT", {
        "formula": "float($OUT_Ke_Spray or 0) + float($OUT_Ke_Assembly or 0) + float($OUT_Ke_QC_RND or 0) + float($OUT_Reject or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Stok_Akhir_WIP", {
        "formula": "float($Stok_Awal or 0) + float($Total_IN or 0) - float($Total_OUT or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Status_Stok", {
        "formula": "'WIP READY' if $Stok_Akhir_WIP > 0 else 'KOSONG'",
        "isFormula": True
    }],

    # --- 4. SPRAY_WIP ---
    ["ModifyColumn", "SPRAY_WIP", "IN_Barang_Masuk", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Total_IN", {
        "formula": "float($IN_Barang_Masuk or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Ke_Plating", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Ke_Departemen='PLATING'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Pengganti_Assembly", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Kategori_Mutasi='RETUR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Reject", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Total_OUT", {
        "formula": "float($OUT_Ke_Assembly or 0) + float($OUT_Ke_Plating or 0) + float($OUT_Pengganti_Assembly or 0) + float($OUT_Reject or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Stok_Akhir_WIP", {
        "formula": "float($Stok_Awal or 0) + float($Total_IN or 0) - float($Total_OUT or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Status_Stok", {
        "formula": "'WIP READY' if $Stok_Akhir_WIP > 0 else 'KOSONG'",
        "isFormula": True
    }],

    # --- 5. GUDANG_IMPOR_CHINA ---
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "IN_Kedatangan_Impor", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='GUDANG IMPOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Total_IN", {
        "formula": "float($IN_Kedatangan_Impor or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG IMPOR', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "OUT_Ke_Plating_Spray", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG IMPOR', Ke_Departemen='PLATING')) + sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG IMPOR', Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Total_OUT", {
        "formula": "float($OUT_Ke_Assembly or 0) + float($OUT_Ke_Plating_Spray or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Stok_Akhir", {
        "formula": "float($Stok_Awal or 0) + float($Total_IN or 0) - float($Total_OUT or 0)",
        "isFormula": True
    }],

    # --- 6. GUDANG_KARTON ---
    ["ModifyColumn", "GUDANG_KARTON", "IN_Kedatangan", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='GUDANG KARTON'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "Total_IN", {
        "formula": "float($IN_Kedatangan or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "OUT_Pemakaian", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG KARTON'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "Total_OUT", {
        "formula": "float($OUT_Pemakaian or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "Stok_Akhir", {
        "formula": "float($Stok_Awal or 0) + float($Total_IN or 0) - float($Total_OUT or 0)",
        "isFormula": True
    }],

    # --- 7. BAHAN_BAKU_RESIN ---
    ["ModifyColumn", "BAHAN_BAKU_RESIN", "IN_Pemasukan_Kg", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Bahan, Ke_Departemen='INJEKSI', Kategori_Mutasi='PEMBELIAN VENDOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "BAHAN_BAKU_RESIN", "Total_IN_Kg", {
        "formula": "float($IN_Pemasukan_Kg or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "BAHAN_BAKU_RESIN", "OUT_Pemakaian_Kg", {
        "formula": "sum(r.Qty_Mutasi for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Bahan, Dari_Departemen='INJEKSI', Kategori_Mutasi='HASIL PRODUKSI'))",
        "isFormula": True
    }],
    ["ModifyColumn", "BAHAN_BAKU_RESIN", "Total_OUT_Kg", {
        "formula": "float($OUT_Pemakaian_Kg or 0)",
        "isFormula": True
    }],
    ["ModifyColumn", "BAHAN_BAKU_RESIN", "Stok_Akhir_Kg", {
        "formula": "float($Stok_Awal_Kg or 0) + float($Total_IN_Kg or 0) - float($Total_OUT_Kg or 0)",
        "isFormula": True
    }]
]

req = urllib.request.Request(
    f"{BASE_URL}/apply",
    data=json.dumps(actions).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    print(f"✅ BERHASIL! Status update formula: {resp.status}")

print("Seluruh tabel departemen (INJEKSI, PLATING, SPRAY, IMPOR, KARTON, RESIN) sekarang 100% dinamis dan otomatis terhubung!")
