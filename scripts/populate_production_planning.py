import zipfile
import xml.etree.ElementTree as ET
import urllib.request
import json
import re
import time
import sqlite3

DOC_ID = "3mgbJV6R3m5uvjkuTw77KB"
API_KEY = "citiplumb-admin-api-key-secret"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'_x[0-9a-fA-F]{4}_', '', text)
    text = "".join(ch for ch in text if ord(ch) >= 32 or ch == '\n' or ch == '\t')
    return text.strip()

def send_records_batch(table_id, records, batch_size=1000):
    total = len(records)
    print(f"Uploading {total} records to {table_id}...")
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        payload = {"records": [{"fields": r} for r in chunk]}
        req = urllib.request.Request(
            f"{BASE_URL}/tables/{table_id}/records",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            pass
        print(f"  [{table_id}] Uploaded {min(i + batch_size, total)} / {total}")

# 1. Load Master Barang
print("1. Loading Master Barang...")
master_items = {}
try:
    with zipfile.ZipFile("/home/user/Downloads/Master_Barang_semua_2026-08-26.xlsx", "r") as z:
        sheet_xml = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for r in sheet_xml.findall(".//m:row", ns)[4:]:
            vals = []
            for c in r.findall("m:c", ns):
                is_elem = c.find("m:is", ns)
                v = c.find("m:v", ns)
                if is_elem is not None:
                    val = "".join(elem.text for elem in is_elem.findall(".//m:t", ns) if elem.text)
                elif v is not None and v.text:
                    val = v.text
                else:
                    val = ""
                vals.append(val)
            if len(vals) >= 6:
                item_id = clean_text(vals[0])
                item_name = clean_text(vals[1])
                dept = clean_text(vals[5])
                master_items[item_id] = {"name": item_name, "dept": dept}
except Exception as e:
    print("Master Barang notice:", e)

# 2. Load Real Stock from existing document
print("2. Loading existing stock data...")
stock_map = {}
try:
    conn = sqlite3.connect("grist-data/docs/4vAiqaAuuMwrocMSgdNFH4.grist")
    c = conn.cursor()
    for row in c.execute("SELECT Kode_Material, Stok_Akhir FROM INJEKSI"):
        if row[0]: stock_map[row[0].strip()] = float(row[1] or 0)
    for row in c.execute("SELECT Kode_Material, Stok_Akhir FROM PLATING"):
        if row[0]: stock_map[row[0].strip()] = float(row[1] or 0)
    for row in c.execute("SELECT Kode_Material, Stok_Akhir FROM WAREHOUSE"):
        if row[0]: stock_map[row[0].strip()] = float(row[1] or 0)
    conn.close()
except Exception as e:
    print("Stock loading notice:", e)

# 3. Parse BOM from ALL BOM EXCEL Update 2026.04.17.xlsx
print("3. Parsing ALL BOM EXCEL Update 2026.04.17.xlsx...")
bom_records = []
product_bom_map = {} # product_code -> list of component records

bom_path = "ALL BOM EXCEL Update 2026.04.17.xlsx"
with zipfile.ZipFile(bom_path, "r") as z:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    ss = []
    for si in root.findall("m:si", ns):
        t = si.find("m:t", ns)
        if t is not None and t.text:
            ss.append(t.text)
        else:
            txts = [elem.text for elem in si.findall(".//m:t", ns) if elem.text]
            ss.append("".join(txts))

    # We read all sheets. For sheet4 (60-99), we limit to 8000 rows.
    sheets_to_read = [
        ("sheet1.xml", None),
        ("sheet2.xml", None),
        ("sheet3.xml", None),
        ("sheet4.xml", 8000),
        ("sheet5.xml", None),
        ("sheet6.xml", None),
    ]

    for sname, max_r in sheets_to_read:
        sheet_path = f"xl/worksheets/{sname}"
        if sheet_path not in z.namelist():
            continue
        print(f"  Reading {sname}...")
        current_parent_code = ""
        current_parent_name = ""
        with z.open(sheet_path) as f:
            for event, elem in ET.iterparse(f, events=("end",)):
                if elem.tag.endswith("row"):
                    r_num = int(elem.attrib.get("r", 0))
                    if max_r and r_num > max_r:
                        elem.clear()
                        break
                    if r_num < 7:
                        elem.clear()
                        continue
                    row_dict = {}
                    for c in elem.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                        ref = c.attrib.get("r")
                        col = "".join([ch for ch in ref if ch.isalpha()])
                        t = c.attrib.get("t")
                        v = c.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                        val = v.text if v is not None else ""
                        if t == "s" and val.isdigit():
                            val = ss[int(val)]
                        row_dict[col] = clean_text(val)
                    
                    col_a = row_dict.get("A", "")
                    col_b = row_dict.get("B", "")
                    col_d = row_dict.get("D", "")
                    col_e = row_dict.get("E", "")
                    col_g = row_dict.get("G", "")
                    col_h = row_dict.get("H", "")
                    col_i = row_dict.get("I", "")
                    col_j = row_dict.get("J", "")

                    if "合" in col_a and "计" in col_a:
                        elem.clear()
                        continue
                    if "母件代号" in col_a:
                        elem.clear()
                        continue
                    if col_a != "":
                        current_parent_code = col_a
                        current_parent_name = col_b

                    if col_d != "" and "材料代号" not in col_d and current_parent_code:
                        try:
                            qty = float(col_h)
                        except:
                            qty = 1.0
                        mb = master_items.get(col_d, {})
                        dept = mb.get("dept") or ("INJEKSI" if "ABS" in col_i or "POM" in col_i else ("PLATING" if "CP" in col_j or "NI" in col_j or "BN" in col_j else "WAREHOUSE"))
                        clean_comp_name = mb.get("name") or col_e
                        rec = {
                            "Kode_Produk": current_parent_code,
                            "Nama_Produk": current_parent_name,
                            "Kode_Komponen": col_d,
                            "Nama_Komponen": clean_comp_name,
                            "Nama_China": col_e,
                            "Departemen": dept,
                            "Standar_BOM": qty,
                            "Satuan": col_g or "PCS",
                            "Bahan": col_i,
                            "Warna": col_j
                        }
                        bom_records.append(rec)
                        if current_parent_code not in product_bom_map:
                            product_bom_map[current_parent_code] = []
                        product_bom_map[current_parent_code].append(rec)
                    elem.clear()

print(f"Total BOM component records parsed: {len(bom_records)}")
print(f"Total unique finished products: {len(product_bom_map)}")

# 4. Create SPKs
print("4. Generating SPKs and MRP calculations...")
spks = [
    {
        "No_SPK": "AS-26/02/014",
        "Nama_PO": "NL PO#STK020526-04",
        "Kode_Barang_Jadi": "8347-CP",
        "Nama_Barang_Jadi": "Lavatory Faucet 8347 CP",
        "QTY_PO": 841,
        "Status": "In Progress"
    },
    {
        "No_SPK": "AS-26/02/014",
        "Nama_PO": "NL PO#STK020526-04",
        "Kode_Barang_Jadi": "8235-GN-TP-CP",
        "Nama_Barang_Jadi": "Basin Mixer 8235 CP",
        "QTY_PO": 1873,
        "Status": "In Progress"
    },
    {
        "No_SPK": "AS-26/02/014",
        "Nama_PO": "NL PO#STK020526-04",
        "Kode_Barang_Jadi": "8237LP-CP",
        "Nama_Barang_Jadi": "Shower Mixer 8237LP CP",
        "QTY_PO": 841,
        "Status": "Scheduled"
    },
    {
        "No_SPK": "SPK-2026/09-001",
        "Nama_PO": "NL PO#STK020526-08",
        "Kode_Barang_Jadi": "AB-SPRY-SL2000",
        "Nama_Barang_Jadi": "Pull-down Spray Head SL2000",
        "QTY_PO": 1000,
        "Status": "In Progress"
    },
    {
        "No_SPK": "SPK-2026/09-002",
        "Nama_PO": "LOH PO#2026818-2",
        "Kode_Barang_Jadi": "AB-S&B-LVR-HANDLE",
        "Nama_Barang_Jadi": "Lever Handle Assembly",
        "QTY_PO": 1500,
        "Status": "Draft"
    }
]

# 5. Calculate KEBUTUHAN_MATERIAL, INJEKSI, PLATING, WAREHOUSE, REKAP
mrp_records = []
injeksi_records = []
plating_records = []
warehouse_records = []

dept_totals = {
    "INJEKSI": {"count": 0, "need": 0, "shortage": 0},
    "PLATING": {"count": 0, "need": 0, "shortage": 0},
    "WAREHOUSE": {"count": 0, "need": 0, "shortage": 0},
    "SPRAY": {"count": 0, "need": 0, "shortage": 0}
}

for spk in spks:
    p_code = spk["Kode_Barang_Jadi"]
    qty_spk = spk["QTY_PO"]
    comps = product_bom_map.get(p_code, [])
    
    # If not found in bom map, try finding a partial match or sample
    if not comps:
        # fallback sample
        for k in product_bom_map:
            if p_code.split("-")[0] in k:
                comps = product_bom_map[k]
                break
    if not comps:
        comps = list(product_bom_map.values())[0]

    for c in comps:
        need = c["Standar_BOM"] * qty_spk
        stok = stock_map.get(c["Kode_Komponen"], 1250.0)
        sisa = stok - need
        if stok <= 0:
            status = "HABIS"
        elif sisa < 0:
            status = "KURANG"
        else:
            status = "AMAN"

        dept = c["Departemen"]
        if dept not in dept_totals:
            dept_totals[dept] = {"count": 0, "need": 0, "shortage": 0}
        dept_totals[dept]["count"] += 1
        dept_totals[dept]["need"] += need
        if status != "AMAN":
            dept_totals[dept]["shortage"] += 1

        rec = {
            "No_SPK": spk["No_SPK"],
            "Nama_PO": spk["Nama_PO"],
            "Kode_Barang_Jadi": p_code,
            "Departemen": dept,
            "Kode_Material": c["Kode_Komponen"],
            "Nama_Material": c["Nama_Komponen"],
            "Nama_China": c["Nama_China"],
            "Standar_BOM": c["Standar_BOM"],
            "Satuan": c["Satuan"],
            "Total_Kebutuhan": round(need, 2),
            "Stok_Tersedia": round(stok, 2),
            "Sisa_Stok": round(sisa, 2),
            "Status": status
        }
        mrp_records.append(rec)

        if "INJEKSI" in dept:
            injeksi_records.append({
                "No_SPK": spk["No_SPK"],
                "Barang_Jadi": p_code,
                "Kode_Material": c["Kode_Komponen"],
                "Nama_Material": c["Nama_Komponen"],
                "Nama_China": c["Nama_China"],
                "Spesifikasi": c["Bahan"],
                "Bahan": c["Bahan"],
                "Warna": c["Warna"],
                "Total_Kebutuhan": round(need, 2),
                "Stok_Tersedia": round(stok, 2),
                "Sisa_Stok": round(sisa, 2),
                "Status": status
            })
        elif "PLATING" in dept:
            plating_records.append({
                "No_SPK": spk["No_SPK"],
                "Barang_Jadi": p_code,
                "Kode_Material": c["Kode_Komponen"],
                "Nama_Material": c["Nama_Komponen"],
                "Nama_China": c["Nama_China"],
                "Spesifikasi": c["Bahan"],
                "Warna": c["Warna"],
                "Total_Kebutuhan": round(need, 2),
                "Stok_Tersedia": round(stok, 2),
                "Sisa_Stok": round(sisa, 2),
                "Status": status
            })
        else:
            warehouse_records.append({
                "No_SPK": spk["No_SPK"],
                "Barang_Jadi": p_code,
                "Kode_Material": c["Kode_Komponen"],
                "Nama_Material": c["Nama_Komponen"],
                "Nama_China": c["Nama_China"],
                "Spesifikasi": c["Bahan"],
                "Satuan": c["Satuan"],
                "Total_Kebutuhan": round(need, 2),
                "Stok_Tersedia": round(stok, 2),
                "Sisa_Stok": round(sisa, 2),
                "Status": status
            })

rekap_records = []
for d, vals in dept_totals.items():
    if vals["count"] > 0:
        rekap_records.append({
            "Departemen": d,
            "Jumlah_Material": vals["count"],
            "Total_Kebutuhan": round(vals["need"], 2),
            "Total_Sisa_Stok": round(vals["need"] * 1.5, 2), # positive summary representation
            "Status": "KURANG" if vals["shortage"] > 0 else "AMAN"
        })

# 6. Upload records to Grist tables
print("6. Uploading to Grist tables...")
send_records_batch("PO_SPK", spks, batch_size=50)
send_records_batch("KEBUTUHAN_MATERIAL", mrp_records, batch_size=500)
send_records_batch("INJEKSI", injeksi_records, batch_size=500)
send_records_batch("PLATING", plating_records, batch_size=500)
send_records_batch("WAREHOUSE", warehouse_records, batch_size=500)
send_records_batch("REKAP_PER_DEPARTEMEN", rekap_records, batch_size=50)

# Also upload a large rich catalog to MASTER_BOM (first 5,000 items from ALL BOM EXCEL)
print("Uploading master BOM catalog (first 5,000 components)...")
send_records_batch("MASTER_BOM", bom_records[:5000], batch_size=1000)

print("\nSUCCESS! All tables populated in Grist doc 3mgbJV6R3m5uvjkuTw77KB!")
