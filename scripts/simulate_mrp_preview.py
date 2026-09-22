import zipfile
import xml.etree.ElementTree as ET
import re

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'_x[0-9a-fA-F]{4}_', '', text)
    text = "".join(ch for ch in text if ord(ch) >= 32 or ch == '\n' or ch == '\t')
    return text.strip()

# 1. Master barang
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
    pass

# 2. Get real stock for sample items from existing SQLite grist doc if available
import sqlite3
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
    pass

# 3. Parse BOM for AB-SPRY-SL2000
path = "ALL BOM EXCEL Update 2026.04.17.xlsx"
components = []
parent_info = {}

with zipfile.ZipFile(path, "r") as z:
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

    sheet_xml = ET.fromstring(z.read("xl/worksheets/sheet5.xml"))
    rows = sheet_xml.findall(".//m:row", ns)
    
    current_parent = ""
    for r in rows[6:150]:
        row_dict = {}
        for c in r.findall("m:c", ns):
            ref = c.attrib.get("r")
            col = "".join([ch for ch in ref if ch.isalpha()])
            t = c.attrib.get("t")
            v = c.find("m:v", ns)
            val = v.text if v is not None else ""
            if t == "s" and val.isdigit():
                val = ss[int(val)]
            row_dict[col] = clean_text(val)
            
        col_a = row_dict.get("A", "")
        col_d = row_dict.get("D", "")
        if "合" in col_a and "计" in col_a: continue
        if col_a:
            current_parent = col_a
            if current_parent == "AB-SPRY-SL2000":
                parent_info = {"code": col_a, "name": row_dict.get("B", ""), "spec": row_dict.get("C", "")}
        
        if current_parent == "AB-SPRY-SL2000" and col_d and "材料代号" not in col_d:
            try:
                qty = float(row_dict.get("H", 1))
            except:
                qty = 1.0
            mb = master_items.get(col_d, {})
            dept = mb.get("dept") or ("INJEKSI" if "ABS" in row_dict.get("I", "") or "POM" in row_dict.get("I", "") else "WAREHOUSE")
            components.append({
                "comp_code": col_d,
                "comp_name": mb.get("name") or row_dict.get("E", ""),
                "comp_name_cn": row_dict.get("E", ""),
                "dept": dept,
                "qty_bom": qty,
                "unit": row_dict.get("G", "PCS"),
                "material": row_dict.get("I", ""),
                "color": row_dict.get("J", "")
            })

# 4. Simulate Production Plan SPK: 1,000 PCS
TARGET_SPK_QTY = 1000
print(f"=== SIMULASI PRODUCTION PLANNING (MRP) ===")
print(f"SPK No          : SPK-2026/09/20-001")
print(f"PO Ref          : NL PO#STK020526-04")
print(f"Produk          : {parent_info.get('code')} ({parent_info.get('name')})")
print(f"Target Produksi : {TARGET_SPK_QTY:,} PCS\n")

print(f"{'DEPT':<11} | {'KODE PART':<18} | {'NAMA MATERIAL':<26} | {'QTY/UNIT':<8} | {'KEBUTUHAN':<10} | {'STOK':<10} | {'SISA':<10} | {'STATUS'}")
print("-" * 115)

dept_summary = {}

for c in components:
    dept = c["dept"]
    need = c["qty_bom"] * TARGET_SPK_QTY
    stock = stock_map.get(c["comp_code"], 500.0) # default demo stock if not in map
    sisa = stock - need
    if stock <= 0:
        status = "HABIS"
    elif sisa < 0:
        status = "KURANG"
    else:
        status = "AMAN"
    
    if dept not in dept_summary:
        dept_summary[dept] = {"total_items": 0, "total_need": 0, "shortage_items": 0}
    dept_summary[dept]["total_items"] += 1
    dept_summary[dept]["total_need"] += need
    if status != "AMAN":
        dept_summary[dept]["shortage_items"] += 1

    print(f"{dept:<11} | {c['comp_code']:<18} | {c['comp_name'][:26]:<26} | {c['qty_bom']:>8.2f} | {need:>10.1f} | {stock:>10.1f} | {sisa:>10.1f} | {status}")

print("\n=== REKAP PER DEPARTEMEN ===")
for d, s in dept_summary.items():
    print(f"- {d:<12}: Total {s['total_items']} material | Kebutuhan: {s['total_need']:,.1f} | Part Kurang/Habis: {s['shortage_items']} item")
