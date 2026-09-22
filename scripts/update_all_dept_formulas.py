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

print("Updating formulas for Status_Penerimaan and Selisih_Qty in MUTASI_ANTAR_DEPARTEMEN...")

status_formula = """is_verified = bool($Admin_Terima) or ($Qty_Terima is not None and float($Qty_Terima or 0) > 0)
if not is_verified:
    return 'PROSES KIRIM'
elif float($Qty_Terima or 0) == float($Qty_Kirim or 0):
    return 'DITERIMA (COCOK)'
else:
    return 'SELISIH (DISPUTE)'"""

selisih_formula = """is_verified = bool($Admin_Terima) or ($Qty_Terima is not None and float($Qty_Terima or 0) > 0)
return (float($Qty_Terima or 0) - float($Qty_Kirim or 0)) if is_verified else 0"""

actions = [
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Status_Penerimaan", {
        "formula": status_formula,
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
    }],
    ["ModifyColumn", "MUTASI_ANTAR_DEPARTEMEN", "Selisih_Qty", {
        "formula": selisih_formula,
        "isFormula": True,
        "type": "Numeric"
    }],

    # 1. INJEKSI_LOKAL
    # IN: Menggunakan Qty_Terima (atau Qty_Kirim jika produksi mandiri)
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Hasil_Produksi", {
        "formula": "sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='HASIL PRODUKSI'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Pembelian", {
        "formula": "sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='PEMBELIAN VENDOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "IN_Retur", {
        "formula": "sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi='RETUR', Ke_Departemen='INJEKSI'))",
        "isFormula": True
    }],
    # OUT: Menggunakan Qty_Kirim (karena sudah keluar dari Injeksi)
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Plating", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='PLATING'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Spray", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Ke_QC_PPIC", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Ke_Departemen='QC & RND'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "OUT_Reject", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='INJEKSI', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Adj_Masuk", {
        "formula": 'sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT MASUK (+)") if r.Dari_Departemen == "INJEKSI" or r.Ke_Departemen == "INJEKSI")',
        "isFormula": True
    }],
    ["ModifyColumn", "INJEKSI_LOKAL", "Adj_Keluar", {
        "formula": 'sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT KELUAR (-)", Dari_Departemen="INJEKSI"))',
        "isFormula": True
    }],

    # 2. PLATING_WIP
    # IN: Hanya barang yang sudah diterima (Qty_Terima)
    ["ModifyColumn", "PLATING_WIP", "IN_Barang_Masuk", {
        "formula": "sum((r.Qty_Terima or 0) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='PLATING') if (bool(r.Admin_Terima) or (r.Qty_Terima is not None and r.Qty_Terima > 0)))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_Spray", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='SPRAY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Ke_QC_RND", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Ke_Departemen='QC & RND'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "OUT_Reject", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='PLATING', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Adj_Masuk", {
        "formula": 'sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT MASUK (+)") if r.Dari_Departemen == "PLATING" or r.Ke_Departemen == "PLATING")',
        "isFormula": True
    }],
    ["ModifyColumn", "PLATING_WIP", "Adj_Keluar", {
        "formula": 'sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT KELUAR (-)", Dari_Departemen="PLATING"))',
        "isFormula": True
    }],

    # 3. SPRAY_WIP
    # IN: Hanya barang yang sudah diverifikasi diterima fisik di SPRAY
    ["ModifyColumn", "SPRAY_WIP", "IN_Barang_Masuk", {
        "formula": "sum((r.Qty_Terima or 0) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='SPRAY') if (bool(r.Admin_Terima) or (r.Qty_Terima is not None and r.Qty_Terima > 0)))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Ke_Plating", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Ke_Departemen='PLATING'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Pengganti_Assembly", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Kategori_Mutasi='RETUR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "OUT_Reject", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='SPRAY', Kategori_Mutasi='REJECT / SCRAP'))",
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Adj_Masuk", {
        "formula": 'sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT MASUK (+)") if r.Dari_Departemen == "SPRAY" or r.Ke_Departemen == "SPRAY")',
        "isFormula": True
    }],
    ["ModifyColumn", "SPRAY_WIP", "Adj_Keluar", {
        "formula": 'sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT KELUAR (-)", Dari_Departemen="SPRAY"))',
        "isFormula": True
    }],

    # 4. GUDANG_IMPOR_CHINA
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "IN_Kedatangan_Impor", {
        "formula": "sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='GUDANG IMPOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "OUT_Ke_Assembly", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG IMPOR', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "OUT_Ke_Plating_Spray", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG IMPOR') if r.Ke_Departemen in ['PLATING', 'SPRAY'])",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Adj_Masuk", {
        "formula": 'sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT MASUK (+)") if r.Dari_Departemen == "GUDANG IMPOR" or r.Ke_Departemen == "GUDANG IMPOR")',
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_IMPOR_CHINA", "Adj_Keluar", {
        "formula": 'sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT KELUAR (-)", Dari_Departemen="GUDANG IMPOR"))',
        "isFormula": True
    }],

    # 5. GUDANG_KARTON
    ["ModifyColumn", "GUDANG_KARTON", "IN_Kedatangan", {
        "formula": "sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Ke_Departemen='GUDANG LOKAL', Kategori_Mutasi='PEMBELIAN VENDOR'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "OUT_Pemakaian", {
        "formula": "sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Dari_Departemen='GUDANG LOKAL', Ke_Departemen='ASSEMBLY'))",
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "Adj_Masuk", {
        "formula": 'sum((r.Qty_Terima if (r.Qty_Terima is not None and r.Qty_Terima > 0) else r.Qty_Kirim) for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT MASUK (+)") if r.Dari_Departemen == "GUDANG LOKAL" or r.Ke_Departemen == "GUDANG LOKAL")',
        "isFormula": True
    }],
    ["ModifyColumn", "GUDANG_KARTON", "Adj_Keluar", {
        "formula": 'sum(r.Qty_Kirim for r in MUTASI_ANTAR_DEPARTEMEN.lookupRecords(Kode_Str=$Kode_Barang, Kategori_Mutasi="ADJUSTMENT KELUAR (-)", Dari_Departemen="GUDANG LOKAL"))',
        "isFormula": True
    }]
]

res = apply_actions(actions)
print("✅ Seluruh formula departemen berhasil diselaraskan dengan Two-Way Handshake!")
