import zipfile
import xml.etree.ElementTree as ET
import re

def clean_text(text):
    if not text:
        return ""
    # remove control characters and hex escapes like _x0002_
    text = re.sub(r'_x[0-9a-fA-F]{4}_', '', text)
    text = "".join(ch for ch in text if ord(ch) >= 32 or ch == '\n' or ch == '\t')
    return text.strip()

# 1. Load master barang for clean names and departments
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
    print("Master barang error:", e)

print(f"Loaded {len(master_items)} Master Barang entries.")

# 2. Parse sample from ALL BOM EXCEL sheet 5 (A-M) and sheet 1 (00-05)
path = "ALL BOM EXCEL Update 2026.04.17.xlsx"
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
    
    current_parent = {"code": "", "name": "", "spec": ""}
    boms = {}
    
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
        col_b = row_dict.get("B", "")
        col_c = row_dict.get("C", "")
        col_d = row_dict.get("D", "")
        col_e = row_dict.get("E", "")
        col_f = row_dict.get("F", "")
        col_g = row_dict.get("G", "")
        col_h = row_dict.get("H", "")
        col_i = row_dict.get("I", "")
        col_j = row_dict.get("J", "")

        if "合" in col_a and "计" in col_a:
            continue
        if "母件代号" in col_a:
            continue

        if col_a != "":
            current_parent = {"code": col_a, "name": col_b, "spec": col_c}
            if col_a not in boms:
                boms[col_a] = {"parent": current_parent, "components": []}

        if col_d != "" and "材料代号" not in col_d and current_parent["code"]:
            try:
                qty = float(col_h)
            except:
                qty = 1.0
            mb = master_items.get(col_d, {})
            dept = mb.get("dept") or ("INJEKSI" if "ABS" in col_i or "POM" in col_i else "WAREHOUSE")
            clean_comp_name = mb.get("name") or col_e
            boms[current_parent["code"]]["components"].append({
                "comp_code": col_d,
                "comp_name": clean_comp_name,
                "comp_name_cn": col_e,
                "dept": dept,
                "qty": qty,
                "unit": col_g,
                "material": col_i,
                "color": col_j
            })

for pcode, data in list(boms.items())[:5]:
    p = data["parent"]
    comps = data["components"]
    if not comps:
        continue
    print("=" * 75)
    print(f"PRODUK INDUK : {p['code']} | {p['name']} {p['spec']}")
    print(f"TOTAL KOMPONEN: {len(comps)} item")
    print("-" * 75)
    for c in comps:
        dept_str = f"[{c['dept']}]"
        print(f"  {dept_str:13} {c['comp_code']:20} {c['comp_name']:28} {c['qty']:>7.2f} {c['unit']:4} ({c['material']})")
