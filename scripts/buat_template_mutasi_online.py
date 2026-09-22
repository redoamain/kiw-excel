import os
import zipfile
import xml.etree.ElementTree as ET
import urllib.request
import json
import re

DOC_ID = "pnPY9D1FA4hsBGaBtdbVz2"
API_KEY = "citiplumb-admin-api-key-secret"
BASE_URL = f"http://localhost:8484/api/docs/{DOC_ID}"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'_x[0-9a-fA-F]{4}_', '', str(text))
    return "".join(ch for ch in text if ord(ch) >= 32 or ch == '\n' or ch == '\t').strip()

def send_records_batch(table_id, records, batch_size=500):
    total = len(records)
    if total == 0:
        return
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

def get_shared_strings(z):
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for si in root.findall('m:si', ns):
            t = si.find('m:t', ns)
            ss.append(t.text if (t is not None and t.text) else ''.join(e.text for e in si.findall('.//m:t', ns) if e.text))
    return ss

def get_cell_val(c, ss):
    t_attr = c.attrib.get('t')
    v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
    if v is None or not v.text: return ''
    if t_attr == 's' and int(v.text) < len(ss): return ss[int(v.text)].strip()
    return v.text.strip()

print("==================================================================")
print("🚀 MEMBUAT TEMPLATE MUTASI & STOK ANTAR DEPARTEMEN ONLINE DI GRIST")
print(f"   Dokumen Target ID: {DOC_ID}")
print("==================================================================")

# 1. SETUP STRUKTUR TABEL LENGKAP
print("1. Menyiapkan skema tabel untuk semua departemen...")
tables_def = [
    {
        "id": "MUTASI_ANTAR_DEPARTEMEN",
        "columns": [
            {"id": "Tanggal", "type": "Date", "label": "Tanggal Transaksi"},
            {"id": "No_Form_SJ", "type": "Text", "label": "No Surat Jalan / Form"},
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Barang"},
            {"id": "Nama_Barang", "type": "Text", "label": "Nama Barang"},
            {"id": "Dari_Departemen", "type": "Choice", "label": "Dari Dept (OUT)"},
            {"id": "Ke_Departemen", "type": "Choice", "label": "Ke Dept (IN)"},
            {"id": "Qty_Mutasi", "type": "Numeric", "label": "Qty Mutasi"},
            {"id": "Satuan", "type": "Choice", "label": "Satuan"},
            {"id": "Kategori_Mutasi", "type": "Choice", "label": "Kategori Mutasi"},
            {"id": "Admin_PIC", "type": "Text", "label": "Admin PIC"},
            {"id": "Status_Penerimaan", "type": "Choice", "label": "Status Penerimaan"},
            {"id": "Keterangan", "type": "Text", "label": "Keterangan"}
        ]
    },
    {
        "id": "INJEKSI_LOKAL",
        "columns": [
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Produk"},
            {"id": "Nama_Barang", "type": "Text", "label": "Nama Produk"},
            {"id": "Lokasi_Rak", "type": "Text", "label": "Lokasi Rak"},
            {"id": "Warna", "type": "Text", "label": "Warna"},
            {"id": "Bahan", "type": "Text", "label": "Bahan"},
            {"id": "Stok_Awal", "type": "Numeric", "label": "Stok Awal (Q Awal)"},
            {"id": "IN_Hasil_Produksi", "type": "Numeric", "label": "IN: Hasil Cetak Injeksi"},
            {"id": "IN_Pembelian", "type": "Numeric", "label": "IN: Pembelian Luar"},
            {"id": "IN_Retur", "type": "Numeric", "label": "IN: Retur Masuk"},
            {"id": "Total_IN", "type": "Numeric", "label": "Total Masuk (IN)"},
            {"id": "OUT_Ke_Plating", "type": "Numeric", "label": "OUT: Kirim ke Plating"},
            {"id": "OUT_Ke_Spray", "type": "Numeric", "label": "OUT: Kirim ke Spray"},
            {"id": "OUT_Ke_Assembly", "type": "Numeric", "label": "OUT: Kirim ke Assembly"},
            {"id": "OUT_Ke_QC_PPIC", "type": "Numeric", "label": "OUT: Kirim ke QC & PPIC"},
            {"id": "OUT_Reject", "type": "Numeric", "label": "OUT: Reject Injeksi"},
            {"id": "Total_OUT", "type": "Numeric", "label": "Total Keluar (OUT)"},
            {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir Realtime"},
            {"id": "Status_Stok", "type": "Text", "label": "Status Stok"}
        ]
    },
    {
        "id": "PLATING_WIP",
        "columns": [
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Barang"},
            {"id": "Nama_Barang", "type": "Text", "label": "Nama Barang"},
            {"id": "Kategori", "type": "Text", "label": "Kategori WIP"},
            {"id": "Stok_Awal", "type": "Numeric", "label": "First Stock (Awal)"},
            {"id": "IN_Barang_Masuk", "type": "Numeric", "label": "IN: Terima Raw Part"},
            {"id": "Total_IN", "type": "Numeric", "label": "Total Masuk (IN)"},
            {"id": "OUT_Ke_Spray", "type": "Numeric", "label": "OUT: Kirim ke Spray"},
            {"id": "OUT_Ke_Assembly", "type": "Numeric", "label": "OUT: Kirim ke Assembly"},
            {"id": "OUT_Ke_QC_RND", "type": "Numeric", "label": "OUT: Kirim ke QC & RND"},
            {"id": "OUT_Reject", "type": "Numeric", "label": "OUT: Reject Plating"},
            {"id": "Total_OUT", "type": "Numeric", "label": "Total Keluar (OUT)"},
            {"id": "Stok_Akhir_WIP", "type": "Numeric", "label": "Sisa WIP (Stok Akhir)"},
            {"id": "Status_Stok", "type": "Text", "label": "Status Stok"}
        ]
    },
    {
        "id": "SPRAY_WIP",
        "columns": [
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Barang"},
            {"id": "Nama_Barang", "type": "Text", "label": "Nama Barang"},
            {"id": "Warna", "type": "Text", "label": "Warna Cat"},
            {"id": "Stok_Awal", "type": "Numeric", "label": "Saldo Awal"},
            {"id": "IN_Barang_Masuk", "type": "Numeric", "label": "IN: Terima dari Plating/China"},
            {"id": "Total_IN", "type": "Numeric", "label": "Total Masuk (IN)"},
            {"id": "OUT_Ke_Assembly", "type": "Numeric", "label": "OUT: Kirim ke Assembly"},
            {"id": "OUT_Ke_Plating", "type": "Numeric", "label": "OUT: Kirim ke Plating"},
            {"id": "OUT_Pengganti_Assembly", "type": "Numeric", "label": "OUT: Pengganti Assembly"},
            {"id": "OUT_Reject", "type": "Numeric", "label": "OUT: Reject Spray"},
            {"id": "Total_OUT", "type": "Numeric", "label": "Total Keluar (OUT)"},
            {"id": "Stok_Akhir_WIP", "type": "Numeric", "label": "Sisa WIP (Stok Akhir)"},
            {"id": "Status_Stok", "type": "Text", "label": "Status Stok"}
        ]
    },
    {
        "id": "GUDANG_IMPOR_CHINA",
        "columns": [
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Part Impor"},
            {"id": "Nama_Barang", "type": "Text", "label": "Nama Barang"},
            {"id": "Lokasi_Rak", "type": "Text", "label": "Lokasi Rak"},
            {"id": "Stok_Awal", "type": "Numeric", "label": "Stok Awal"},
            {"id": "IN_Kedatangan_Impor", "type": "Numeric", "label": "IN: Kedatangan China"},
            {"id": "Total_IN", "type": "Numeric", "label": "Total Masuk (IN)"},
            {"id": "OUT_Ke_Assembly", "type": "Numeric", "label": "OUT: Kirim ke Assembly"},
            {"id": "OUT_Ke_Plating_Spray", "type": "Numeric", "label": "OUT: Kirim ke Plating/Spray"},
            {"id": "Total_OUT", "type": "Numeric", "label": "Total Keluar (OUT)"},
            {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir"},
            {"id": "Status_Stok", "type": "Text", "label": "Status Stok"}
        ]
    },
    {
        "id": "GUDANG_KARTON",
        "columns": [
            {"id": "Kode_Barang", "type": "Text", "label": "Kode Dus / Karton"},
            {"id": "Nama_Barang", "type": "Text", "label": "Spesifikasi Karton"},
            {"id": "Lokasi_Rak", "type": "Text", "label": "Lokasi Rak"},
            {"id": "Stok_Awal", "type": "Numeric", "label": "Stok Awal"},
            {"id": "IN_Kedatangan", "type": "Numeric", "label": "IN: Kedatangan Karton"},
            {"id": "Total_IN", "type": "Numeric", "label": "Total Masuk (IN)"},
            {"id": "OUT_Pemakaian", "type": "Numeric", "label": "OUT: Pemakaian Packing"},
            {"id": "Total_OUT", "type": "Numeric", "label": "Total Keluar (OUT)"},
            {"id": "Stok_Akhir", "type": "Numeric", "label": "Stok Akhir"},
            {"id": "Status_Stok", "type": "Text", "label": "Status Stok"}
        ]
    },
    {
        "id": "BAHAN_BAKU_RESIN",
        "columns": [
            {"id": "Kode_Bahan", "type": "Text", "label": "Kode Bahan Baku"},
            {"id": "Nama_Bahan", "type": "Text", "label": "Nama Resin / Pewarna"},
            {"id": "Stok_Awal_Kg", "type": "Numeric", "label": "Stok Awal (KG)"},
            {"id": "IN_Pemasukan_Kg", "type": "Numeric", "label": "IN: Pemasukan (KG)"},
            {"id": "Total_IN_Kg", "type": "Numeric", "label": "Total Masuk (KG)"},
            {"id": "OUT_Pemakaian_Kg", "type": "Numeric", "label": "OUT: Pemakaian Mesin (KG)"},
            {"id": "Total_OUT_Kg", "type": "Numeric", "label": "Total Keluar (KG)"},
            {"id": "Stok_Akhir_Kg", "type": "Numeric", "label": "Stok Akhir (KG)"},
            {"id": "Stok_Akhir_Bag", "type": "Numeric", "label": "Stok Akhir (BAG)"}
        ]
    }
]

req = urllib.request.Request(
    f"{BASE_URL}/tables",
    data=json.dumps({"tables": tables_def}).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(req) as resp:
        print("  ✅ Seluruh 7 tabel departemen berhasil dibuat di Grist!")
except Exception as e:
    print("  Notice tabel:", e)

# 2. POPULATE INJEKSI LOKAL
print("\n2. Mengisi Data INJEKSI LOKAL (berdasarkan file 8 AGUSTUS)...")
injeksi_rows = []
p_injeksi = "8 AGUSTUS/LO/Laporan Harian 2026(1)/INJEKSI LOKAL 2026(2).xlsx"
with zipfile.ZipFile(p_injeksi, 'r') as z:
    ss = get_shared_strings(z)
    sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for r in sheet_xml.findall('.//m:row', ns)[3:]:
        row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
        kode = clean_text(row_map.get('I', ''))
        nama = clean_text(row_map.get('J', ''))
        if not kode or kode == '0':
            continue
        lokasi = clean_text(row_map.get('H', ''))
        warna = clean_text(row_map.get('M', ''))
        bahan = clean_text(row_map.get('N', ''))
        
        stok_awal = float(row_map.get('O') or 0)
        in_prod = float(row_map.get('CJ') or 0)
        in_beli = float(row_map.get('BD') or 0)
        in_retur = float(row_map.get('CU') or 0)
        tot_in = float(row_map.get('P') or 0)
        
        out_plat = float(row_map.get('EA') or 0)
        out_spray = float(row_map.get('FG') or 0)
        out_ass = float(row_map.get('GM') or 0)
        out_qc = float(row_map.get('GN') or 0) if 'GN' in row_map else 0.0
        out_rej = float(row_map.get('HS') or 0)
        tot_out = float(row_map.get('S') or 0)
        
        stok_akhir = float(row_map.get('C') or row_map.get('V') or 0)
        status = "AMAN" if stok_akhir > 500 else ("MENIPIS" if stok_akhir > 0 else "HABIS (0)")

        injeksi_rows.append({
            "Kode_Barang": kode, "Nama_Barang": nama, "Lokasi_Rak": lokasi, "Warna": warna, "Bahan": bahan,
            "Stok_Awal": stok_awal, "IN_Hasil_Produksi": in_prod, "IN_Pembelian": in_beli, "IN_Retur": in_retur,
            "Total_IN": tot_in, "OUT_Ke_Plating": out_plat, "OUT_Ke_Spray": out_spray, "OUT_Ke_Assembly": out_ass,
            "OUT_Ke_QC_PPIC": out_qc, "OUT_Reject": out_rej, "Total_OUT": tot_out, "Stok_Akhir": stok_akhir,
            "Status_Stok": status
        })

send_records_batch("INJEKSI_LOKAL", injeksi_rows)

# 3. POPULATE PLATING WIP
print("\n3. Mengisi Data PLATING WIP (berdasarkan file 8 AGUSTUS)...")
plating_rows = []
p_plat = "8 AGUSTUS/PL/08. Report Plating Agustus 2026 kirim IT/08. WIP AGUSTUS 2026.xlsx"
with zipfile.ZipFile(p_plat, 'r') as z:
    ss = get_shared_strings(z)
    sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for r in sheet_xml.findall('.//m:row', ns)[5:]:
        row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
        kode = clean_text(row_map.get('B', ''))
        nama = clean_text(row_map.get('E', '') or row_map.get('D', ''))
        if not kode or kode == '0':
            continue
        kategori = clean_text(row_map.get('FQ', 'Barang Setengah Jadi'))
        stok_awal = float(row_map.get('F') or 0)
        in_tot = float(row_map.get('AM') or 0)
        out_spray = float(row_map.get('BS') or 0)
        out_ass = float(row_map.get('CY') or 0)
        out_qc = float(row_map.get('EE') or 0)
        out_rej = float(row_map.get('FK') or 0)
        tot_out = out_spray + out_ass + out_qc + out_rej
        stok_akhir = float(row_map.get('FO') or 0)
        status = "WIP SIAP" if stok_akhir > 0 else "KOSONG"

        plating_rows.append({
            "Kode_Barang": kode, "Nama_Barang": nama, "Kategori": kategori, "Stok_Awal": stok_awal,
            "IN_Barang_Masuk": in_tot, "Total_IN": in_tot, "OUT_Ke_Spray": out_spray, "OUT_Ke_Assembly": out_ass,
            "OUT_Ke_QC_RND": out_qc, "OUT_Reject": out_rej, "Total_OUT": tot_out, "Stok_Akhir_WIP": stok_akhir,
            "Status_Stok": status
        })

send_records_batch("PLATING_WIP", plating_rows)

# 4. POPULATE SPRAY WIP
print("\n4. Mengisi Data SPRAY WIP (berdasarkan file 8 AGUSTUS)...")
spray_rows = []
p_spray = "8 AGUSTUS/SP/LAPORAN BULANAN SPRAY AGUSTUS 2026/8. Laporan WIP 2 Spray Bulan Agustus 2026.xlsx"
with zipfile.ZipFile(p_spray, 'r') as z:
    ss = get_shared_strings(z)
    sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for r in sheet_xml.findall('.//m:row', ns)[5:]:
        row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
        kode = clean_text(row_map.get('B', ''))
        nama = clean_text(row_map.get('C', ''))
        if not kode or kode == '0':
            continue
        warna = clean_text(row_map.get('E', ''))
        stok_awal = float(row_map.get('F') or 0)
        in_tot = float(row_map.get('AP') or 0)
        out_ass = float(row_map.get('CF') or 0)
        out_plat = float(row_map.get('CJ') or 0)
        out_pengganti = float(row_map.get('DP') or 0)
        tot_out = out_ass + out_plat + out_pengganti
        stok_akhir = float(row_map.get('DQ') or 0)
        status = "WIP SIAP" if stok_akhir > 0 else "KOSONG"

        spray_rows.append({
            "Kode_Barang": kode, "Nama_Barang": nama, "Warna": warna, "Stok_Awal": stok_awal,
            "IN_Barang_Masuk": in_tot, "Total_IN": in_tot, "OUT_Ke_Assembly": out_ass, "OUT_Ke_Plating": out_plat,
            "OUT_Pengganti_Assembly": out_pengganti, "OUT_Reject": 0.0, "Total_OUT": tot_out,
            "Stok_Akhir_WIP": stok_akhir, "Status_Stok": status
        })

send_records_batch("SPRAY_WIP", spray_rows)

# 5. POPULATE GUDANG IMPOR (PART CHINA)
print("\n5. Mengisi Data GUDANG IMPOR / PART CHINA...")
china_rows = []
p_china = "8 AGUSTUS/IM/LAPORAN HARIAN 2026(1)/PART CHINA 2026.xlsx"
with zipfile.ZipFile(p_china, 'r') as z:
    ss = get_shared_strings(z)
    sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for r in sheet_xml.findall('.//m:row', ns)[4:]:
        row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
        kode = clean_text(row_map.get('D', ''))
        nama = clean_text(row_map.get('E', ''))
        if not kode or kode == '0':
            continue
        lokasi = clean_text(row_map.get('H', ''))
        stok_akhir = float(row_map.get('B') or 0)
        status = "TERSEDIA" if stok_akhir > 500 else ("MENIPIS" if stok_akhir > 0 else "HABIS (0)")

        china_rows.append({
            "Kode_Barang": kode, "Nama_Barang": nama, "Lokasi_Rak": lokasi, "Stok_Awal": stok_akhir,
            "IN_Kedatangan_Impor": 0.0, "Total_IN": 0.0, "OUT_Ke_Assembly": 0.0, "OUT_Ke_Plating_Spray": 0.0,
            "Total_OUT": 0.0, "Stok_Akhir": stok_akhir, "Status_Stok": status
        })

send_records_batch("GUDANG_IMPOR_CHINA", china_rows)

# 6. POPULATE KARTON & PACKAGING
print("\n6. Mengisi Data GUDANG KARTON...")
karton_rows = []
p_karton = "8 AGUSTUS/IM/LAPORAN HARIAN 2026(1)/KARTON 2026.xlsx"
with zipfile.ZipFile(p_karton, 'r') as z:
    ss = get_shared_strings(z)
    sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    for r in sheet_xml.findall('.//m:row', ns)[4:]:
        row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
        kode = clean_text(row_map.get('D', ''))
        nama = clean_text(row_map.get('E', ''))
        if not kode or kode == '0':
            continue
        lokasi = clean_text(row_map.get('G', 'GUDANG KARTON'))
        stok_akhir = float(row_map.get('B') or 0)
        status = "TERSEDIA" if stok_akhir > 200 else ("MENIPIS" if stok_akhir > 0 else "HABIS (0)")

        karton_rows.append({
            "Kode_Barang": kode, "Nama_Barang": nama, "Lokasi_Rak": lokasi, "Stok_Awal": stok_akhir,
            "IN_Kedatangan": 0.0, "Total_IN": 0.0, "OUT_Pemakaian": 0.0, "Total_OUT": 0.0,
            "Stok_Akhir": stok_akhir, "Status_Stok": status
        })

send_records_batch("GUDANG_KARTON", karton_rows)

def safe_float(val, default=0.0):
    if not val:
        return default
    try:
        return float(str(val).replace(',', '').strip())
    except:
        return default

# 7. POPULATE BAHAN BAKU RESIN
print("\n7. Mengisi Data BAHAN BAKU RESIN...")
resin_rows = []
p_bb = "8 AGUSTUS/IN/LAPORAN BAHAN BAKU AGUSTUS.xlsx"
with zipfile.ZipFile(p_bb, 'r') as z:
    ss = get_shared_strings(z)
    wb_xml = ET.fromstring(z.read('xl/workbook.xml'))
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    s_id = None
    for s in wb_xml.findall('.//m:sheet', ns):
        if s.attrib.get('name') == '31-08':
            s_id = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            break
    if s_id:
        rels_xml = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        ns_rel = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
        path = 'xl/' + [r.attrib.get('Target') for r in rels_xml.findall('.//r:Relationship', ns_rel) if r.attrib.get('Id') == s_id][0].lstrip('/')
        sheet_xml = ET.fromstring(z.read(path))
        for r in sheet_xml.findall('.//m:row', ns)[9:]:
            row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
            kode = clean_text(row_map.get('B', ''))
            nama = clean_text(row_map.get('C', ''))
            if not kode or kode == '0':
                continue
            stok_awal_bag = safe_float(row_map.get('D'))
            stok_awal_kg = safe_float(row_map.get('E'))
            in_kg = safe_float(row_map.get('I')) + safe_float(row_map.get('J')) + safe_float(row_map.get('K'))
            out_kg = safe_float(row_map.get('F')) + safe_float(row_map.get('G')) + safe_float(row_map.get('H'))
            stok_akhir_bag = safe_float(row_map.get('L'))
            stok_akhir_kg = safe_float(row_map.get('M'))

            resin_rows.append({
                "Kode_Bahan": kode, "Nama_Bahan": nama, "Stok_Awal_Kg": stok_awal_kg, "IN_Pemasukan_Kg": in_kg,
                "Total_IN_Kg": in_kg, "OUT_Pemakaian_Kg": out_kg, "Total_OUT_Kg": out_kg,
                "Stok_Akhir_Kg": stok_akhir_kg, "Stok_Akhir_Bag": stok_akhir_bag
            })

send_records_batch("BAHAN_BAKU_RESIN", resin_rows)

# 8. POPULATE CONTOH TRANSAKSI MUTASI ANTAR DEPARTEMEN RIIL
print("\n8. Mengisi Contoh Transaksi Mutasi Antar Departemen Riil...")
mutasi_sample = [
    {
        "Tanggal": "2026-08-01", "No_Form_SJ": "SJ-INJ-080101", "Kode_Barang": "LC-07A043",
        "Nama_Barang": "712-BS NATURAL", "Dari_Departemen": "INJEKSI", "Ke_Departemen": "PLATING",
        "Qty_Mutasi": 3038.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Andre (Injeksi)", "Status_Penerimaan": "DITERIMA", "Keterangan": "Kirim untuk plating nikel chrome"
    },
    {
        "Tanggal": "2026-08-02", "No_Form_SJ": "SJ-INJ-080205", "Kode_Barang": "09A007",
        "Nama_Barang": "HS-GJ NATURAL", "Dari_Departemen": "INJEKSI", "Ke_Departemen": "PLATING",
        "Qty_Mutasi": 602.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Andre (Injeksi)", "Status_Penerimaan": "DITERIMA", "Keterangan": "Kirim proses plating"
    },
    {
        "Tanggal": "2026-08-03", "No_Form_SJ": "SJ-INJ-080312", "Kode_Barang": "LC-02B019",
        "Nama_Barang": "CQSZHF WK NATURAL", "Dari_Departemen": "INJEKSI", "Ke_Departemen": "ASSEMBLY",
        "Qty_Mutasi": 7681.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Adnan (Gudang Lokal)", "Status_Penerimaan": "DITERIMA", "Keterangan": "Pengambilan perakitan PO 2026"
    },
    {
        "Tanggal": "2026-08-04", "No_Form_SJ": "SJ-INJ-080408", "Kode_Barang": "03B097",
        "Nama_Barang": "BD-DJ NATURAL", "Dari_Departemen": "INJEKSI", "Ke_Departemen": "ASSEMBLY",
        "Qty_Mutasi": 841.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Adnan (Gudang Lokal)", "Status_Penerimaan": "DITERIMA", "Keterangan": "Pengambilan perakitan PO 2026"
    },
    {
        "Tanggal": "2026-08-05", "No_Form_SJ": "SJ-PLT-080501", "Kode_Barang": "00A001BN",
        "Nama_Barang": "HS-LGT BN", "Dari_Departemen": "PLATING", "Ke_Departemen": "SPRAY",
        "Qty_Mutasi": 253.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Admin Plating", "Status_Penerimaan": "DITERIMA", "Keterangan": "Lanjut cat black matte"
    },
    {
        "Tanggal": "2026-08-06", "No_Form_SJ": "SJ-SP-080602", "Kode_Barang": "00A001BN",
        "Nama_Barang": "HS-LGT BN", "Dari_Departemen": "SPRAY", "Ke_Departemen": "ASSEMBLY",
        "Qty_Mutasi": 253.0, "Satuan": "PCS", "Kategori_Mutasi": "TRANSFER ANTAR DEPT",
        "Admin_PIC": "Admin Spray", "Status_Penerimaan": "DITERIMA", "Keterangan": "Siap rakit kran"
    }
]

send_records_batch("MUTASI_ANTAR_DEPARTEMEN", mutasi_sample)

print("\n🎉 SUKSES! TEMPLATE LAPORAN MUTASI & STOK ANTAR DEPARTEMEN ONLINE TELAH AKTIF!")
print(f"🌐 Buka di Browser: http://localhost:8484/o/citiplumb/doc/{DOC_ID}")
print(f"🌐 Akses LAN (Komputer Lain): http://192.168.12.101:8484/o/citiplumb/doc/{DOC_ID}")
