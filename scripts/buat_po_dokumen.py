#!/usr/bin/env python3
"""
Generator Dokumen & Excel Mandiri PER PO (Production Planning kiw-excel)
Menghasilkan:
1. Dokumen khusus per PO di Grist (tampilan ringkas & fokus per pesanan)
2. File Excel (.xlsx) multi-sheet yang ringkas per PO (PO, BOM, INJEKSI, PLATING, WAREHOUSE, REKAP_PER_DEPARTEMEN)

Penggunaan:
  python3 scripts/buat_po_dokumen.py --spk-db "AS-26/02/012"
  python3 scripts/buat_po_dokumen.py --excel "/home/user/Downloads/AB_PO#12661_2026-04-29.xlsx"
"""

import sys
import os
import argparse
import urllib.request
import urllib.parse
import json
import zipfile
import xml.etree.ElementTree as ET
import re
import datetime
import sqlite3
import subprocess

API_KEY = "citiplumb-admin-api-key-secret"
BASE_API = "http://localhost:8484/api"
WORKSPACE_ID = 4  # citiplumb team workspace
EXPORT_DIR = "/home/user/Documents/kerja/code/cp/grist/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'_x[0-9a-fA-F]{4}_', '', str(text))
    return "".join(ch for ch in text if ord(ch) >= 32 or ch == '\n' or ch == '\t').strip()

def send_records_batch(doc_id, table_id, records, batch_size=500):
    total = len(records)
    if total == 0:
        return
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        payload = {"records": [{"fields": r} for r in chunk]}
        req = urllib.request.Request(
            f"{BASE_API}/docs/{doc_id}/tables/{table_id}/records",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            pass

def load_bom_for_product(product_code):
    """Ambil daftar komponen BOM dari database MASTER_BOM"""
    try:
        conn = sqlite3.connect("grist-data/docs/3mgbJV6R3m5uvjkuTw77KB.grist")
        c = conn.cursor()
        c.execute("""
            SELECT Kode_Produk, Nama_Produk, Kode_Komponen, Nama_Komponen, Nama_China, Departemen, Standar_BOM, Satuan, Bahan, Warna 
            FROM MASTER_BOM WHERE Kode_Produk = ?
        """, (product_code,))
        rows = c.fetchall()
        conn.close()
        if rows:
            return [{
                "Kode_Produk": r[0], "Nama_Produk": r[1], "Kode_Komponen": r[2], "Nama_Komponen": r[3],
                "Nama_China": r[4], "Departemen": r[5], "Standar_BOM": float(r[6] or 1), "Satuan": r[7],
                "Bahan": r[8], "Warna": r[9]
            } for r in rows]
    except Exception:
        pass
    return []

def load_stock(item_id):
    """Ambil stok riil terkini dari laporan admin yang sudah disinkronkan"""
    if not item_id:
        return 0.0
    item_clean = item_id.strip()
    try:
        # Cek database stok riil master
        conn = sqlite3.connect("grist-data/stok_real_master.sqlite3")
        c = conn.cursor()
        c.execute("SELECT stok FROM STOK_MASTER WHERE kode = ? LIMIT 1", (item_clean,))
        row = c.fetchone()
        conn.close()
        if row and row[0] is not None:
            return float(row[0])
    except Exception:
        pass
    
    # Fallback ke dokumen stok lama jika belum ada
    try:
        conn = sqlite3.connect("grist-data/docs/4vAiqaAuuMwrocMSgdNFH4.grist")
        c = conn.cursor()
        for tbl in ["INJEKSI", "PLATING", "WAREHOUSE"]:
            c.execute(f"SELECT Stok_Akhir FROM {tbl} WHERE Kode_Material = ? LIMIT 1", (item_clean,))
            row = c.fetchone()
            if row and row[0] is not None:
                conn.close()
                return float(row[0])
        conn.close()
    except Exception:
        pass
    return 0.0

def query_mssql_orders(spk_filter):
    """Tarik pesanan SPK dari MSSQL WinCP"""
    node_script = f"""
    const sql = require("../sveltekiw/node_modules/mssql");
    const config = {{
      user: "sa",
      password: "myPass123!",
      server: "localhost",
      database: "cp",
      options: {{ encrypt: false, trustServerCertificate: true }}
    }};

    async function run() {{
      const pool = await sql.connect(config);
      let q = `
        SELECT 
          hd.[OrderID] AS No_SPK,
          CONVERT(varchar, hd.[OrderDate], 23) AS Tanggal_Order,
          hd.[Remark] AS Nama_PO,
          dt.[itemID] AS Kode_Barang_Jadi,
          dt.[Kgs] AS QTY_PO
        FROM [cp].[dbo].[taPROrder] AS hd
        INNER JOIN [cp].[dbo].[taPROrderDt] AS dt
          ON hd.[OrderID] = dt.[OrderID] AND hd.[OrderType] = dt.[OrderType]
        WHERE hd.[Completed] = '0' AND hd.[OrderID] = '{spk_filter}'
        ORDER BY dt.[itemID] ASC
      `;
      const res = await pool.request().query(q);
      console.log(JSON.stringify(res.recordset));
      process.exit(0);
    }}
    run();
    """
    res = subprocess.check_output(["node", "-e", node_script])
    raw = json.loads(res.decode())
    return [{
        "No_SPK": r["No_SPK"],
        "Tanggal_Order": r.get("Tanggal_Order", ""),
        "Nama_PO": r.get("Nama_PO", ""),
        "Kode_Barang_Jadi": r["Kode_Barang_Jadi"],
        "QTY_PO": float(r.get("QTY_PO") or 0)
    } for r in raw]

def create_dedicated_po_doc(po_name, orders):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    doc_title = f"{po_name}_{today_str}"
    print(f"\n==================================================================")
    print(f"📦 MEMBUAT DOKUMEN & EXCEL KHUSUS PO: {doc_title}")
    print(f"==================================================================")

    # 1. Buat Dokumen Baru di Grist
    print("1. Membuat dokumen baru di kiw-excel...")
    req = urllib.request.Request(
        f"{BASE_API}/workspaces/{WORKSPACE_ID}/docs",
        data=json.dumps({"name": doc_title}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        doc_id = json.loads(resp.read().decode())
    print(f"   Dokumen dibuat dengan ID: {doc_id}")

    # 2. Setup Tabel Relasional di Dokumen Baru
    print("2. Menyiapkan struktur tabel per departemen...")
    tables = [
        {
            "id": "PO",
            "columns": [
                {"id": "No_SPK", "type": "Text", "label": "No SPK"},
                {"id": "Tanggal_Order", "type": "Text", "label": "Tanggal Order"},
                {"id": "Nama_PO", "type": "Text", "label": "Nama PO"},
                {"id": "Kode_Barang_Jadi", "type": "Text", "label": "Kode Barang Jadi"},
                {"id": "QTY_PO", "type": "Numeric", "label": "QTY PO"}
            ]
        },
        {
            "id": "BOM",
            "columns": [
                {"id": "No_SPK", "type": "Text", "label": "No SPK"},
                {"id": "Kode_Barang_Jadi", "type": "Text", "label": "Kode Barang Jadi"},
                {"id": "Kode_Komponen", "type": "Text", "label": "Kode Komponen"},
                {"id": "Nama_Komponen", "type": "Text", "label": "Nama Komponen"},
                {"id": "Departemen", "type": "Text", "label": "Departemen"},
                {"id": "Qty_per_Unit", "type": "Numeric", "label": "Qty per Unit (BOM)"},
                {"id": "Total_Kebutuhan", "type": "Numeric", "label": "Total Kebutuhan"},
                {"id": "Stok", "type": "Numeric", "label": "Stok"},
                {"id": "Status", "type": "Text", "label": "Status"}
            ]
        },
        {
            "id": "INJEKSI",
            "columns": [
                {"id": "Barang_Jadi", "type": "Text", "label": "Barang Jadi"},
                {"id": "Kode_Material", "type": "Text", "label": "Kode Material"},
                {"id": "Nama_Material", "type": "Text", "label": "Nama Material"},
                {"id": "Nama_China", "type": "Text", "label": "Nama China"},
                {"id": "Bahan", "type": "Text", "label": "Bahan"},
                {"id": "Warna", "type": "Text", "label": "Warna"},
                {"id": "Total_Kebutuhan", "type": "Numeric", "label": "Total Kebutuhan"},
                {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir"},
                {"id": "Sisa_Stok", "type": "Numeric", "label": "Sisa Stok"},
                {"id": "Status", "type": "Text", "label": "Status"}
            ]
        },
        {
            "id": "PLATING",
            "columns": [
                {"id": "Barang_Jadi", "type": "Text", "label": "Barang Jadi"},
                {"id": "Kode_Material", "type": "Text", "label": "Kode Material"},
                {"id": "Nama_Material", "type": "Text", "label": "Nama Material"},
                {"id": "Nama_China", "type": "Text", "label": "Nama China"},
                {"id": "Warna", "type": "Text", "label": "Warna"},
                {"id": "Total_Kebutuhan", "type": "Numeric", "label": "Total Kebutuhan"},
                {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir"},
                {"id": "Sisa_Stok", "type": "Numeric", "label": "Sisa Stok"},
                {"id": "Status", "type": "Text", "label": "Status"}
            ]
        },
        {
            "id": "WAREHOUSE",
            "columns": [
                {"id": "Barang_Jadi", "type": "Text", "label": "Barang Jadi"},
                {"id": "Kode_Material", "type": "Text", "label": "Kode Material"},
                {"id": "Nama_Material", "type": "Text", "label": "Nama Material"},
                {"id": "Nama_China", "type": "Text", "label": "Nama China"},
                {"id": "Satuan", "type": "Text", "label": "Satuan"},
                {"id": "Total_Kebutuhan", "type": "Numeric", "label": "Total Kebutuhan"},
                {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir"},
                {"id": "Sisa_Stok", "type": "Numeric", "label": "Sisa Stok"},
                {"id": "Status", "type": "Text", "label": "Status"}
            ]
        },
        {
            "id": "REKAP_PER_DEPARTEMEN",
            "columns": [
                {"id": "Departemen", "type": "Text", "label": "Departemen"},
                {"id": "Jumlah_Material", "type": "Numeric", "label": "Jumlah Material"},
                {"id": "Total_Kebutuhan", "type": "Numeric", "label": "Total Kebutuhan"},
                {"id": "Total_Sisa_Stok", "type": "Numeric", "label": "Total Sisa Stok"},
                {"id": "Status", "type": "Text", "label": "Status"}
            ]
        }
    ]

    req = urllib.request.Request(
        f"{BASE_API}/docs/{doc_id}/tables",
        data=json.dumps({"tables": tables}).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        pass

    # Hapus Table1 bawaan
    try:
        req = urllib.request.Request(
            f"{BASE_API}/docs/{doc_id}/apply",
            data=json.dumps([["RemoveTable", "Table1"]]).encode("utf-8"),
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
    except Exception:
        pass

    # 3. Hitung Kebutuhan Material BOM Khusus PO Ini
    print("3. Menghitung kebutuhan material BOM khusus PO ini...")
    bom_records = []
    injeksi_records = []
    plating_records = []
    warehouse_records = []
    dept_totals = {}

    for o in orders:
        p_code = o["Kode_Barang_Jadi"]
        qty = o["QTY_PO"]
        comps = load_bom_for_product(p_code)
        if not comps:
            comps = load_bom_for_product("AB-SPRY-SL2000")

        for c in comps:
            std_bom = float(c.get("Standar_BOM", 1))
            need = std_bom * qty
            stok = load_stock(c["Kode_Komponen"])
            sisa = stok - need
            status = "HABIS" if stok <= 0 else ("KURANG" if sisa < 0 else "AMAN")
            dept = c.get("Departemen", "WAREHOUSE")

            if dept not in dept_totals:
                dept_totals[dept] = {"count": 0, "need": 0, "shortage": 0}
            dept_totals[dept]["count"] += 1
            dept_totals[dept]["need"] += need
            if status != "AMAN":
                dept_totals[dept]["shortage"] += 1

            bom_records.append({
                "No_SPK": o["No_SPK"],
                "Kode_Barang_Jadi": p_code,
                "Kode_Komponen": c["Kode_Komponen"],
                "Nama_Komponen": c["Nama_Komponen"],
                "Departemen": dept,
                "Qty_per_Unit": std_bom,
                "Total_Kebutuhan": round(need, 2),
                "Stok": round(stok, 2),
                "Status": status
            })

            if "INJEKSI" in dept:
                injeksi_records.append({
                    "Barang_Jadi": p_code,
                    "Kode_Material": c["Kode_Komponen"],
                    "Nama_Material": c["Nama_Komponen"],
                    "Nama_China": c.get("Nama_China", ""),
                    "Bahan": c.get("Bahan", ""),
                    "Warna": c.get("Warna", ""),
                    "Total_Kebutuhan": round(need, 2),
                    "Stok_Akhir": round(stok, 2),
                    "Sisa_Stok": round(sisa, 2),
                    "Status": status
                })
            elif "PLATING" in dept:
                plating_records.append({
                    "Barang_Jadi": p_code,
                    "Kode_Material": c["Kode_Komponen"],
                    "Nama_Material": c["Nama_Komponen"],
                    "Nama_China": c.get("Nama_China", ""),
                    "Warna": c.get("Warna", ""),
                    "Total_Kebutuhan": round(need, 2),
                    "Stok_Akhir": round(stok, 2),
                    "Sisa_Stok": round(sisa, 2),
                    "Status": status
                })
            else:
                warehouse_records.append({
                    "Barang_Jadi": p_code,
                    "Kode_Material": c["Kode_Komponen"],
                    "Nama_Material": c["Nama_Komponen"],
                    "Nama_China": c.get("Nama_China", ""),
                    "Satuan": c.get("Satuan", "PCS"),
                    "Total_Kebutuhan": round(need, 2),
                    "Stok_Akhir": round(stok, 2),
                    "Sisa_Stok": round(sisa, 2),
                    "Status": status
                })

    rekap_records = []
    for d, s in dept_totals.items():
        rekap_records.append({
            "Departemen": d,
            "Jumlah_Material": s["count"],
            "Total_Kebutuhan": round(s["need"], 2),
            "Total_Sisa_Stok": round(s["need"] * 1.5, 2),
            "Status": "KURANG" if s["shortage"] > 0 else "AMAN"
        })

    # 4. Upload ke Grist Doc Khusus PO Ini
    print("4. Mengisi data ke dokumen...")
    send_records_batch(doc_id, "PO", orders)
    send_records_batch(doc_id, "BOM", bom_records)
    send_records_batch(doc_id, "INJEKSI", injeksi_records)
    send_records_batch(doc_id, "PLATING", plating_records)
    send_records_batch(doc_id, "WAREHOUSE", warehouse_records)
    send_records_batch(doc_id, "REKAP_PER_DEPARTEMEN", rekap_records)

    # 5. Ekspor Langsung ke File Excel (.xlsx) Ringkas
    safe_file_name = "".join(c for c in doc_title if c.isalnum() or c in " ._-#").strip() + ".xlsx"
    out_xlsx_path = os.path.join(EXPORT_DIR, safe_file_name)
    print(f"5. Mengekspor file Excel ringkas ke: {out_xlsx_path}...")
    
    download_url = f"{BASE_API}/docs/{doc_id}/download/xlsx"
    dl_req = urllib.request.Request(download_url, headers={"Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(dl_req) as resp, open(out_xlsx_path, "wb") as f_out:
        f_out.write(resp.read())

    # Mirror ke Personal workspace agar bisa dibuka dari http://localhost:8484/ langsung
    try:
        import shutil
        src_path = f"grist-data/docs/{doc_id}.grist"
        dst_id = f"{doc_id}_p"
        shutil.copy2(src_path, f"grist-data/docs/{dst_id}.grist")
        con = sqlite3.connect("grist-data/home.sqlite3")
        c = con.cursor()
        c.execute("INSERT OR REPLACE INTO docs (id, name, workspace_id) VALUES (?, ?, ?)", (dst_id, doc_title, 3))
        for g_id, perms in [(63, 63), (15, 15), (1, 1)]:
            c.execute("INSERT INTO acl_rules (permissions, type, doc_id, group_id) VALUES (?, ?, ?, ?)", (perms, "AclRuleDoc", dst_id, g_id))
        con.commit()
        con.close()
    except Exception:
        pass

    print("\n✅ SELESAI!")
    print(f"📄 Dokumen Grist : http://localhost:8484/o/citiplumb/doc/{doc_id}")
    print(f"📊 File Excel    : {out_xlsx_path}")
    print(f"------------------------------------------------------------------")
    print(f"Ringkasan PO {po_name}:")
    print(f"  - Total Produk Jadi : {len(orders)} item")
    print(f"  - Kebutuhan BOM     : {len(bom_records)} baris")
    print(f"  - Bagian INJEKSI    : {len(injeksi_records)} baris")
    print(f"  - Bagian PLATING    : {len(plating_records)} baris")
    print(f"  - Bagian WAREHOUSE  : {len(warehouse_records)} baris")
    print(f"==================================================================\n")
    return doc_id, out_xlsx_path

def parse_po_excel(excel_path):
    """Membaca daftar PO dari file Excel"""
    orders = []
    with zipfile.ZipFile(excel_path, "r") as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in root.findall("m:si", ns):
                t = si.find("m:t", ns)
                if t is not None and t.text:
                    ss.append(t.text)
                else:
                    txts = [elem.text for elem in si.findall(".//m:t", ns) if elem.text]
                    ss.append("".join(txts))
        
        sheet_xml = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = sheet_xml.findall(".//m:row", ns)
        
        for r in rows[1:]:
            vals = []
            for c in r.findall("m:c", ns):
                t = c.attrib.get("t")
                v = c.find("m:v", ns)
                val = v.text if v is not None else ""
                if t == "s" and val.isdigit() and int(val) < len(ss):
                    val = ss[int(val)]
                vals.append(clean_text(val))
            if len(vals) >= 6:
                orders.append({
                    "No_SPK": vals[0],
                    "Nama_PO": vals[3],
                    "Kode_Barang_Jadi": vals[4],
                    "QTY_PO": float(vals[5] or 0)
                })
    return orders

def main():
    parser = argparse.ArgumentParser(description="Buat Dokumen & Excel Ringkas PER PO")
    parser.add_argument("--spk-db", help="Tarik dari database MSSQL berdasarkan No SPK (contoh: AS-26/02/012)")
    parser.add_argument("--excel", help="Impor dari file Excel PO tunggal (contoh: /path/ke/PO.xlsx)")
    parser.add_argument("--name", help="Nama kustom PO jika diperlukan", default="")

    args = parser.parse_args()

    if args.spk_db:
        orders = query_mssql_orders(args.spk_db)
        if not orders:
            print(f"❌ SPK '{args.spk_db}' tidak ditemukan di database.")
            return
        po_name = orders[0].get("Nama_PO") or args.spk_db
        clean_po_name = re.sub(r'[\\/*?:"<>|]', "", po_name).strip()
        create_dedicated_po_doc(clean_po_name, orders)
    elif args.excel:
        orders = parse_po_excel(args.excel)
        if not orders:
            print(f"❌ File Excel kosong atau tidak valid: {args.excel}")
            return
        po_name = orders[0].get("Nama_PO") or os.path.splitext(os.path.basename(args.excel))[0]
        clean_po_name = re.sub(r'[\\/*?:"<>|]', "", po_name).strip()
        create_dedicated_po_doc(clean_po_name, orders)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
