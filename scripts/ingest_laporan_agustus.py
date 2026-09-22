import os
import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import json
import urllib.request

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
    if v is None or not v.text:
        return ''
    if t_attr == 's' and int(v.text) < len(ss):
        return ss[int(v.text)].strip()
    return v.text.strip()

def extract_all_stocks(base_folder="8 AGUSTUS"):
    print(f"=== Menarik Data Stok Riil dari Folder: {base_folder} ===")
    stock_db = {}

    # 1. INJEKSI LOKAL
    p_injeksi = os.path.join(base_folder, "LO/Laporan Harian 2026(1)/INJEKSI LOKAL 2026(2).xlsx")
    if os.path.exists(p_injeksi):
        try:
            with zipfile.ZipFile(p_injeksi, 'r') as z:
                ss = get_shared_strings(z)
                sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
                ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for r in sheet_xml.findall('.//m:row', ns)[3:]:
                    row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
                    kode = row_map.get('I', '').strip()
                    nama = row_map.get('J', '').strip()
                    lokasi = row_map.get('H', '').strip()
                    stok_str = row_map.get('C', '0').strip()
                    if kode and kode != '0':
                        try: stok = float(stok_str) if stok_str else 0.0
                        except: stok = 0.0
                        stock_db[kode] = {
                            'kode': kode, 'nama': nama, 'dept': 'INJEKSI LOKAL', 'kategori': 'KOMPONEN INJEKSI',
                            'lokasi': lokasi, 'stok': stok, 'satuan': 'PCS', 'source': 'INJEKSI LOKAL'
                        }
            print(f"  [+] Injeksi Lokal berhasil dimuat: {len(stock_db)} items")
        except Exception as e:
            print("  [-] Error Injeksi Lokal:", e)

    # 2. PART CHINA (GUDANG IMPOR)
    p_china = os.path.join(base_folder, "IM/LAPORAN HARIAN 2026(1)/PART CHINA 2026.xlsx")
    if os.path.exists(p_china):
        try:
            count = 0
            with zipfile.ZipFile(p_china, 'r') as z:
                ss = get_shared_strings(z)
                sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
                ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for r in sheet_xml.findall('.//m:row', ns)[4:]:
                    row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
                    kode = row_map.get('D', '').strip()
                    nama = row_map.get('E', '').strip()
                    lokasi = row_map.get('H', '').strip()
                    stok_str = row_map.get('B', '0').strip()
                    if kode and kode != '0':
                        try: stok = float(stok_str) if stok_str else 0.0
                        except: stok = 0.0
                        if kode not in stock_db or stock_db[kode]['stok'] == 0:
                            stock_db[kode] = {
                                'kode': kode, 'nama': nama, 'dept': 'GUDANG IMPOR', 'kategori': 'PART IMPOR',
                                'lokasi': lokasi, 'stok': stok, 'satuan': 'PCS', 'source': 'PART CHINA'
                            }
                            count += 1
            print(f"  [+] Part China berhasil dimuat: +{count} items baru")
        except Exception as e:
            print("  [-] Error Part China:", e)

    # 3. KARTON & PACKAGING
    p_karton = os.path.join(base_folder, "IM/LAPORAN HARIAN 2026(1)/KARTON 2026.xlsx")
    if os.path.exists(p_karton):
        try:
            count = 0
            with zipfile.ZipFile(p_karton, 'r') as z:
                ss = get_shared_strings(z)
                sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet8.xml')) # AGUSTUS
                ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for r in sheet_xml.findall('.//m:row', ns)[4:]:
                    row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
                    kode = row_map.get('D', '').strip()
                    nama = row_map.get('E', '').strip()
                    stok_str = row_map.get('B', '0').strip()
                    if kode and kode != '0':
                        try: stok = float(stok_str) if stok_str else 0.0
                        except: stok = 0.0
                        if kode not in stock_db:
                            stock_db[kode] = {
                                'kode': kode, 'nama': nama, 'dept': 'PACKAGING', 'kategori': 'KARTON DUS',
                                'lokasi': 'GUDANG KARTON', 'stok': stok, 'satuan': 'PCS', 'source': 'KARTON'
                            }
                            count += 1
            print(f"  [+] Karton & Packaging berhasil dimuat: +{count} items baru")
        except Exception as e:
            print("  [-] Error Karton:", e)

    # 4. PLATING WIP
    p_plating = os.path.join(base_folder, "PL/08. Report Plating Agustus 2026 kirim IT/08. WIP AGUSTUS 2026.xlsx")
    if os.path.exists(p_plating):
        try:
            count = 0
            with zipfile.ZipFile(p_plating, 'r') as z:
                ss = get_shared_strings(z)
                sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for r in sheet_xml.findall('.//m:row', ns)[5:]:
                    row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
                    kode = row_map.get('B', '').strip()
                    nama = row_map.get('E', '').strip() or row_map.get('D', '').strip()
                    stok_str = row_map.get('FO', '0').strip()
                    if kode and kode != '0':
                        try: stok = float(stok_str) if stok_str else 0.0
                        except: stok = 0.0
                        if kode not in stock_db:
                            stock_db[kode] = {
                                'kode': kode, 'nama': nama, 'dept': 'PLATING', 'kategori': 'WIP PLATING',
                                'lokasi': 'LINE PLATING', 'stok': stok, 'satuan': 'PCS', 'source': 'WIP PLATING'
                            }
                            count += 1
            print(f"  [+] Plating WIP berhasil dimuat: +{count} items baru")
        except Exception as e:
            print("  [-] Error Plating WIP:", e)

    # 5. SPRAY WIP
    p_spray = os.path.join(base_folder, "SP/LAPORAN BULANAN SPRAY AGUSTUS 2026/8. Laporan WIP 2 Spray Bulan Agustus 2026.xlsx")
    if os.path.exists(p_spray):
        try:
            count = 0
            with zipfile.ZipFile(p_spray, 'r') as z:
                ss = get_shared_strings(z)
                sheet_xml = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                for r in sheet_xml.findall('.//m:row', ns)[5:]:
                    row_map = {''.join(ch for ch in c.attrib.get('r') if ch.isalpha()): get_cell_val(c, ss) for c in r.findall('m:c', ns)}
                    kode = row_map.get('B', '').strip()
                    nama = row_map.get('C', '').strip()
                    stok_str = row_map.get('DQ', '0').strip()
                    if kode and kode != '0':
                        try: stok = float(stok_str) if stok_str else 0.0
                        except: stok = 0.0
                        if kode not in stock_db:
                            stock_db[kode] = {
                                'kode': kode, 'nama': nama, 'dept': 'SPRAY', 'kategori': 'WIP SPRAY',
                                'lokasi': 'LINE SPRAY', 'stok': stok, 'satuan': 'PCS', 'source': 'WIP SPRAY'
                            }
                            count += 1
            print(f"  [+] Spray WIP berhasil dimuat: +{count} items baru")
        except Exception as e:
            print("  [-] Error Spray WIP:", e)

    # 6. BAHAN BAKU INJEKSI (RESIN / BIJI PLASTIK)
    p_bb = os.path.join(base_folder, "IN/LAPORAN BAHAN BAKU AGUSTUS.xlsx")
    if os.path.exists(p_bb):
        try:
            count = 0
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
                        kode = row_map.get('B', '').strip()
                        nama = row_map.get('C', '').strip()
                        stok_kg = row_map.get('M', '0').strip()
                        if kode and kode != '0':
                            try: stok = float(stok_kg) if stok_kg else 0.0
                            except: stok = 0.0
                            stock_db[kode] = {
                                'kode': kode, 'nama': nama, 'dept': 'BAHAN BAKU INJEKSI', 'kategori': 'RESIN BIJIH',
                                'lokasi': 'GUDANG RESIN', 'stok': stok, 'satuan': 'KG', 'source': 'BAHAN BAKU INJEKSI'
                            }
                            count += 1
            print(f"  [+] Bahan Baku Injeksi berhasil dimuat: +{count} items baru")
        except Exception as e:
            print("  [-] Error Bahan Baku Injeksi:", e)

    return stock_db

def save_to_sqlite(stock_db, db_path="grist-data/stok_real_master.sqlite3"):
    print(f"Menyimpan {len(stock_db)} data stok ke {db_path}...")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS STOK_MASTER (
            kode TEXT PRIMARY KEY,
            nama TEXT,
            dept TEXT,
            kategori TEXT,
            lokasi TEXT,
            stok REAL,
            satuan TEXT,
            source TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("DELETE FROM STOK_MASTER")
    for item in stock_db.values():
        c.execute("""
            INSERT OR REPLACE INTO STOK_MASTER (kode, nama, dept, kategori, lokasi, stok, satuan, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item['kode'], item['nama'], item['dept'], item['kategori'], item['lokasi'], item['stok'], item['satuan'], item['source']))
    conn.commit()
    conn.close()
    print(f"✅ Selesai menyimpan ke {db_path}!")

def sync_to_template_stok_grist(stock_db, doc_id="9p3aeTvGjrKZjqNGosgU52"):
    api_key = "citiplumb-admin-api-key-secret"
    base_url = f"http://localhost:8484/api/docs/{doc_id}"
    print(f"Sinkronisasi ke Grist Dokumen (Doc ID: {doc_id}) via REST API...")
    try:
        # 1. Hapus data lama di MASTER_STOK
        req = urllib.request.Request(
            f"{base_url}/tables/MASTER_STOK/records",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            existing_ids = [r["id"] for r in data.get("records", [])]
        
        if existing_ids:
            print(f"  Membersihkan {len(existing_ids)} data lama...")
            del_req = urllib.request.Request(
                f"{base_url}/tables/MASTER_STOK/data/delete",
                data=json.dumps(existing_ids).encode(),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(del_req) as resp:
                pass

        # 2. Siapkan records baru (prioritaskan stok > 0 dan master items)
        records = []
        for item in stock_db.values():
            stok = item['stok']
            status = "AMAN" if stok > 500 else ("MENIPIS" if stok > 0 else "HABIS (0)")
            records.append({
                "Kode_Barang": item['kode'],
                "Nama_Barang": item['nama'][:100],
                "Departemen": item['dept'],
                "Kategori": item['kategori'],
                "Satuan": item['satuan'],
                "Lokasi_Rak": item['lokasi'],
                "Saldo_Awal": stok,
                "Total_Masuk": 0.0,
                "Total_Keluar": 0.0,
                "Saldo_Akhir": stok,
                "Safety_Stock": 100.0,
                "Status_Stok": status,
                "Keterangan": f"Sync dari {item['source']}"
            })

        print(f"  Mengupload {len(records)} records ke MASTER_STOK...")
        batch_size = 500
        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            payload = {"records": [{"fields": r} for r in chunk]}
            post_req = urllib.request.Request(
                f"{base_url}/tables/MASTER_STOK/records",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(post_req) as resp:
                pass
            print(f"    Uploaded {min(i + batch_size, len(records))} / {len(records)}")

        print("✅ Berhasil upload seluruh data stok riil ke Grist Template Stok!")
    except Exception as e:
        print("[-] Gagal sinkronisasi ke Grist via API:", e)

if __name__ == "__main__":
    stocks = extract_all_stocks("8 AGUSTUS")
    save_to_sqlite(stocks)
    sync_to_template_stok_grist(stocks)
    print("\n🎉 SELURUH DATA STOK RIIL AGUSTUS BERHASIL DISINKRONKAN!")
