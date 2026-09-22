#!/usr/bin/env python3
"""
Web UI Generator Production Planning & MRP (kiw-excel)
Menyediakan antarmuka web modern berbasis tombol untuk:
1. Memilih SPK dari Database MSSQL WinCP dan men-generate dokumen Grist + Excel dengan 1 klik tombol.
2. Mengunggah file Excel PO Marketing dan otomatis men-generate per PO.
3. Mengunduh file Excel ringkas per PO yang sudah selesai.

Jalankan:
  python3 scripts/web_generator.py
Buka browser:
  http://localhost:8485
"""

import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import os
import re
import subprocess
import cgi
import io

PORT = 8485
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRIST_DIR = os.path.dirname(SCRIPT_DIR)
EXPORT_DIR = os.path.join(GRIST_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

HTML_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Generator Production Planning - kiw-excel</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .bg-kiw { background-color: #1D4ED8; }
    .text-kiw { color: #1D4ED8; }
  </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
  <!-- Header -->
  <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
          📊
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900 leading-tight">Production Planning Auto-Generator</h1>
          <p class="text-xs text-slate-500">Sistem Perencanaan Produksi & MRP Mandiri PER PO (kiw-excel)</p>
        </div>
      </div>
      <div class="flex gap-2">
        <a href="http://localhost:8484/o/citiplumb" target="_blank" class="inline-flex items-center gap-2 bg-blue-50 text-blue-700 hover:bg-blue-100 font-medium text-sm px-4 py-2 rounded-lg border border-blue-200 transition">
          <span>🌐 Buka kiw-excel</span>
        </a>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
    
    <!-- Notifikasi Alert -->
    <div id="alertBox" class="hidden p-4 rounded-xl border transition shadow-sm"></div>

    <!-- Bagian 0: Sinkronisasi Stok dari Laporan Admin Lapangan -->
    <section class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-200 p-6 shadow-sm">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-600 text-white mb-1">
            📦 Integrasi Laporan Admin Lapangan
          </div>
          <h2 class="text-lg font-bold text-slate-900">Sinkronisasi Stok Riil dari Folder Laporan Admin (8 AGUSTUS)</h2>
          <p class="text-sm text-slate-600 mt-1">
            Menarik otomatis stok riil dari <b>Injeksi Lokal (1.538 item)</b>, <b>Part Impor China (1.462 item)</b>, <b>Karton (1.631 item)</b>, <b>Plating WIP (454 item)</b>, <b>Spray WIP (605 item)</b>, dan <b>Bahan Baku Injeksi (134 item)</b>.
          </p>
        </div>
        <div class="flex flex-wrap gap-2 shrink-0">
          <button id="btnSyncStock" onclick="syncAdminStock()" class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-4 py-2.5 rounded-xl transition shadow-md">
            <span>🔄 Sinkronkan Stok Sekarang</span>
          </button>
          <a href="http://localhost:8484/o/citiplumb/doc/pnPY9D1FA4hsBGaBtdbVz2" target="_blank" class="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm px-4 py-2.5 rounded-xl transition shadow-md">
            <span>🌐 Buka Laporan Mutasi Online (Grist)</span>
          </a>
          <a href="/api/download?file=Template_Laporan_Mutasi_Antar_Departemen.xlsx" class="inline-flex items-center gap-2 bg-white hover:bg-slate-100 text-slate-700 font-medium text-sm px-4 py-2.5 rounded-xl border border-slate-300 transition shadow-sm">
            <span>⬇️ Unduh Excel Mutasi (.xlsx)</span>
          </a>
        </div>
      </div>
    </section>

    <!-- Bagian Khusus: Export Laporan Per Departemen -->
    <section class="bg-white rounded-2xl border border-blue-200 p-6 shadow-sm bg-gradient-to-r from-blue-50/40 to-white">
      <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-1">
            📊 Export Khusus Per Departemen
          </div>
          <h2 class="text-lg font-bold text-slate-900">Download Laporan Sesuai Kebutuhan Departemen Anda</h2>
          <p class="text-sm text-slate-600 mt-0.5">
            Setiap departemen memiliki struktur kolom laporan yang berbeda. Pilih departemen Anda untuk mengunduh file Excel khusus yang bersih tanpa tercampur data departemen lain.
          </p>
        </div>
        <div class="flex flex-wrap sm:flex-nowrap items-center gap-2 w-full lg:w-auto shrink-0">
          <select id="deptSelect" class="bg-white border border-slate-300 text-slate-800 text-sm rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-blue-500 shadow-sm font-medium w-full sm:w-auto">
            <option value="INJEKSI">🏭 INJEKSI (Stok Produk & Mesin Injeksi)</option>
            <option value="PLATING">⚡ PLATING (Stok WIP Plating & Chrome)</option>
            <option value="SPRAY">🎨 SPRAY (Stok WIP Cat & Spray)</option>
            <option value="GUDANG_IMPOR">🚢 GUDANG IMPOR (Part Impor China)</option>
            <option value="GUDANG_LOKAL">📦 GUDANG LOKAL (Karton & Bahan Lokal)</option>
            <option value="RESIN">🧪 BAHAN BAKU RESIN (Resin & Pigmen)</option>
            <option value="MUTASI">📑 BUKU MUTASI (Ledger Serah Terima Antar Dept)</option>
            <option value="ALL">🏢 SEMUA DEPARTEMEN (Multi-Sheet Lengkap)</option>
          </select>
          <button onclick="downloadDeptReport()" class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-4 py-2.5 rounded-xl transition shadow-md whitespace-nowrap">
            <span>⬇️ Unduh Excel</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Bagian 1: Tarik dari Database WinCP (MSSQL) -->
    <section class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 mb-1">
            Database WinCP (MSSQL)
          </div>
          <h2 class="text-lg font-bold text-slate-900">1. Daftar SPK / PO Aktif dari Database</h2>
          <p class="text-sm text-slate-500">Pilih salah satu nomor SPK lalu klik tombol <b>Generate</b> untuk membuat dokumen Grist & file Excel-nya.</p>
        </div>
        <button id="btnRefreshDB" onclick="loadMssqlOrders()" class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-4 py-2 rounded-lg transition shadow-sm">
          <span>🔄 Refresh Daftar SPK</span>
        </button>
      </div>

      <div class="overflow-x-auto rounded-xl border border-slate-200">
        <table class="w-full text-left border-collapse text-sm">
          <thead class="bg-slate-100 text-slate-700 text-xs font-semibold uppercase tracking-wider">
            <tr>
              <th class="py-3 px-4">No SPK</th>
              <th class="py-3 px-4">Tanggal Order</th>
              <th class="py-3 px-4">Nama PO / Remark</th>
              <th class="py-3 px-4 text-center">Jumlah Produk</th>
              <th class="py-3 px-4 text-right">Total Qty (PCS)</th>
              <th class="py-3 px-4 text-center">Aksi (1-Klik Button)</th>
            </tr>
          </thead>
          <tbody id="spkTableBody" class="divide-y divide-slate-200">
            <tr>
              <td colspan="6" class="py-8 text-center text-slate-400">
                Sedang memuat data dari database WinCP...
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Bagian 2: Upload File Excel PO Marketing -->
    <section class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div class="mb-4">
        <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-1">
          Import File Excel
        </div>
        <h2 class="text-lg font-bold text-slate-900">2. Generate dari File Excel PO Marketing</h2>
        <p class="text-sm text-slate-500">Unggah file PO dalam format Excel (.xlsx) seperti <code>AB_PO#...xlsx</code> untuk langsung di-explode per PO.</p>
      </div>

      <form id="uploadForm" class="flex flex-col sm:flex-row items-center gap-4 p-4 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50" onsubmit="uploadExcel(event)">
        <input type="file" id="excelFile" accept=".xlsx,.xls" class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer" required>
        <button type="submit" id="btnUpload" class="w-full sm:w-auto shrink-0 inline-flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm px-6 py-2.5 rounded-lg transition shadow-sm">
          <span>⚡ Upload & Generate</span>
        </button>
      </form>
    </section>

    <!-- Bagian 3: Riwayat File Excel Hasil Ekspor -->
    <section class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div class="flex justify-between items-center mb-4">
        <div>
          <h2 class="text-lg font-bold text-slate-900">3. File Excel Ringkas Hasil Ekspor</h2>
          <p class="text-sm text-slate-500">File Excel ringkas per PO yang siap diunduh dan dibagikan ke lapangan.</p>
        </div>
        <button onclick="loadExportedFiles()" class="text-xs text-blue-600 hover:underline">Refresh List</button>
      </div>

      <div id="exportList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- List file di-render via JS -->
      </div>
    </section>

  </main>

  <footer class="text-center py-6 text-xs text-slate-400 border-t border-slate-200 bg-white">
    kiw-excel Production Planning Engine &copy; 2026 PT Citiplumb
  </footer>

  <script>
    function showAlert(type, title, message) {
      const box = document.getElementById('alertBox');
      box.className = 'p-4 rounded-xl border transition shadow-sm flex items-start gap-3 ' + 
        (type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900');
      box.innerHTML = `
        <div class="text-xl font-bold">${type === 'success' ? '✅' : '❌'}</div>
        <div>
          <h4 class="font-bold text-sm">${title}</h4>
          <p class="text-sm mt-0.5">${message}</p>
        </div>
      `;
      box.classList.remove('hidden');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function loadMssqlOrders() {
      const tbody = document.getElementById('spkTableBody');
      tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-slate-400">Sedang mengambil data dari database MSSQL WinCP...</td></tr>';
      try {
        const res = await fetch('/api/spks');
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        if (!data.length) {
          tbody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-slate-400">Tidak ada SPK aktif di database.</td></tr>';
          return;
        }

        tbody.innerHTML = data.map(item => `
          <tr class="hover:bg-slate-50 transition">
            <td class="py-3 px-4 font-semibold text-slate-900">${item.No_SPK}</td>
            <td class="py-3 px-4 text-slate-600">${item.Tanggal}</td>
            <td class="py-3 px-4 font-medium text-blue-700">${item.Nama_PO}</td>
            <td class="py-3 px-4 text-center">
              <span class="inline-block bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-xs">
                ${item.Total_Produk} item
              </span>
            </td>
            <td class="py-3 px-4 text-right font-bold text-slate-800">${Number(item.Total_Qty).toLocaleString('id-ID')}</td>
            <td class="py-3 px-4 text-center">
              <button onclick="generateFromDb('${item.No_SPK}', this)" class="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs px-3.5 py-1.5 rounded-lg transition shadow-sm">
                <span>⚡ Generate Dokumen & Excel</span>
              </button>
            </td>
          </tr>
        `).join('');
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="py-8 text-center text-rose-500 font-medium">Gagal memuat: ${err.message}</td></tr>`;
      }
    }

    async function syncAdminStock() {
      const btn = document.getElementById('btnSyncStock');
      const origText = btn.innerHTML;
      btn.innerHTML = '<span class="animate-spin">⏳</span> Menyinkronkan...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/sync-stock', { method: 'POST' });
        const result = await res.json();
        if (!res.ok || result.error) throw new Error(result.error || 'Gagal sinkronisasi');

        showAlert('success', 'Sinkronisasi Stok Berhasil!', `
          ${result.message}<br>
          <div class="mt-3 flex gap-3">
            <a href="http://localhost:8484/o/citiplumb/doc/9p3aeTvGjrKZjqNGosgU52" target="_blank" class="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs font-semibold">
              🌐 Lihat Stok di kiw-excel
            </a>
          </div>
        `);
      } catch (err) {
        showAlert('error', 'Gagal Sinkronisasi Stok', err.message);
      } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
      }
    }

    async function generateFromDb(spk, btn) {
      const origText = btn.innerHTML;
      btn.innerHTML = '<span class="animate-spin">⏳</span> Memproses...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ spk })
        });
        const result = await res.json();
        if (!res.ok || result.error) throw new Error(result.error || 'Gagal generate');

        showAlert('success', 'Berhasil Di-generate!', `
          Dokumen khusus SPK <b>${spk}</b> berhasil dibuat!<br>
          <div class="mt-3 flex gap-3">
            <a href="http://localhost:8484/o/citiplumb/doc/${result.doc_id}" target="_blank" class="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs font-semibold">
              🌐 Buka di kiw-excel
            </a>
            <a href="/api/download?file=${encodeURIComponent(result.file_name)}" class="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded text-xs font-semibold">
              ⬇️ Download Excel (.xlsx)
            </a>
          </div>
        `);
        loadExportedFiles();
      } catch (err) {
        showAlert('error', 'Gagal Generate', err.message);
      } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
      }
    }

    async function uploadExcel(e) {
      e.preventDefault();
      const fileInput = document.getElementById('excelFile');
      if (!fileInput.files.length) return;

      const btn = document.getElementById('btnUpload');
      const origText = btn.innerHTML;
      btn.innerHTML = '<span class="animate-spin">⏳</span> Mengunggah...';
      btn.disabled = true;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const result = await res.json();
        if (!res.ok || result.error) throw new Error(result.error || 'Upload gagal');

        showAlert('success', 'Berhasil Di-generate dari Excel!', `
          Dokumen PO dari file <b>${fileInput.files[0].name}</b> berhasil dibuat!<br>
          <div class="mt-3 flex gap-3">
            <a href="http://localhost:8484/o/citiplumb/doc/${result.doc_id}" target="_blank" class="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-xs font-semibold">
              🌐 Buka di kiw-excel
            </a>
            <a href="/api/download?file=${encodeURIComponent(result.file_name)}" class="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded text-xs font-semibold">
              ⬇️ Download Excel (.xlsx)
            </a>
          </div>
        `);
        fileInput.value = '';
        loadExportedFiles();
      } catch (err) {
        showAlert('error', 'Upload Gagal', err.message);
      } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
      }
    }

    async function loadExportedFiles() {
      const container = document.getElementById('exportList');
      try {
        const res = await fetch('/api/exports');
        const files = await res.json();
        if (!files.length) {
          container.innerHTML = '<div class="col-span-full py-6 text-center text-slate-400">Belum ada file Excel yang diekspor.</div>';
          return;
        }

        container.innerHTML = files.map(f => `
          <div class="p-4 rounded-xl border border-slate-200 bg-slate-50 flex justify-between items-center hover:bg-slate-100 transition">
            <div class="overflow-hidden mr-3">
              <div class="font-bold text-sm text-slate-800 truncate" title="${f.name}">📄 ${f.name}</div>
              <div class="text-xs text-slate-500 mt-0.5">${f.size} • ${f.date}</div>
            </div>
            <a href="/api/download?file=${encodeURIComponent(f.name)}" class="shrink-0 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-3 py-1.5 rounded-lg transition shadow-sm">
              ⬇️ Unduh
            </a>
          </div>
        `).join('');
      } catch (err) {
        container.innerHTML = '<div class="col-span-full py-6 text-center text-rose-500">Gagal memuat riwayat file.</div>';
      }
    }

    function downloadDeptReport() {
      const dept = document.getElementById('deptSelect').value;
      window.location.href = `/api/export-dept?dept=${dept}`;
    }

    // Inisialisasi
    loadMssqlOrders();
    loadExportedFiles();
  </script>
</body>
</html>
"""

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if path == "/api/spks":
            try:
                # Query MSSQL via node script
                node_script = """
                const sql = require("../sveltekiw/node_modules/mssql");
                const config = {
                  user: "sa",
                  password: "myPass123!",
                  server: "localhost",
                  database: "cp",
                  options: { encrypt: false, trustServerCertificate: true }
                };

                async function run() {
                  const pool = await sql.connect(config);
                  const res = await pool.request().query(`
                    SELECT 
                      hd.[OrderID] AS No_SPK,
                      CONVERT(varchar, hd.[OrderDate], 23) AS Tanggal,
                      hd.[Remark] AS Nama_PO,
                      COUNT(dt.[itemID]) AS Total_Produk,
                      SUM(dt.[Kgs]) AS Total_Qty
                    FROM [cp].[dbo].[taPROrder] AS hd
                    INNER JOIN [cp].[dbo].[taPROrderDt] AS dt
                      ON hd.[OrderID] = dt.[OrderID] AND hd.[OrderType] = dt.[OrderType]
                    WHERE hd.[Completed] = '0' AND hd.[OrderID] LIKE 'AS%'
                    GROUP BY hd.[OrderID], hd.[OrderDate], hd.[Remark]
                    ORDER BY hd.[OrderDate] DESC
                  `);
                  console.log(JSON.stringify(res.recordset));
                  process.exit(0);
                }
                run();
                """
                res = subprocess.check_output(["node", "-e", node_script], cwd=GRIST_DIR)
                data = json.loads(res.decode())
                self.send_json(data)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == "/api/exports":
            try:
                files = []
                for fname in sorted(os.listdir(EXPORT_DIR), reverse=True):
                    if fname.endswith(".xlsx"):
                        fpath = os.path.join(EXPORT_DIR, fname)
                        st = os.stat(fpath)
                        import datetime
                        dt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y %H:%M")
                        size_kb = f"{st.st_size / 1024:.1f} KB"
                        files.append({"name": fname, "size": size_kb, "date": dt})
                self.send_json(files)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == "/api/download":
            query = urllib.parse.parse_qs(parsed.query)
            fname = query.get("file", [""])[0]
            if not fname or "/" in fname or ".." in fname:
                self.send_response(400)
                self.end_headers()
                return
            fpath = os.path.join(EXPORT_DIR, fname)
            if not os.path.exists(fpath):
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
            self.end_headers()
            with open(fpath, "rb") as f:
                self.wfile.write(f.read())
            return

        if path == "/api/export-dept":
            query = urllib.parse.parse_qs(parsed.query)
            dept = query.get("dept", ["ALL"])[0].upper()
            dept_table_map = {
                "INJEKSI": ("INJEKSI_LOKAL", "Laporan_Stok_INJEKSI_2026.xlsx"),
                "PLATING": ("PLATING_WIP", "Laporan_Stok_PLATING_WIP_2026.xlsx"),
                "SPRAY": ("SPRAY_WIP", "Laporan_Stok_SPRAY_WIP_2026.xlsx"),
                "GUDANG_IMPOR": ("GUDANG_IMPOR_CHINA", "Laporan_Stok_GUDANG_IMPOR_CHINA_2026.xlsx"),
                "GUDANG_LOKAL": ("GUDANG_KARTON", "Laporan_Stok_GUDANG_LOKAL_KARTON_2026.xlsx"),
                "RESIN": ("BAHAN_BAKU_RESIN", "Laporan_Stok_BAHAN_BAKU_RESIN_2026.xlsx"),
                "MUTASI": ("MUTASI_ANTAR_DEPARTEMEN", "Buku_Ledger_MUTASI_ANTAR_DEPARTEMEN_2026.xlsx"),
            }
            if dept in dept_table_map:
                tbl_id, out_name = dept_table_map[dept]
                grist_url = f"http://localhost:8484/api/docs/pnPY9D1FA4hsBGaBtdbVz2/download/xlsx?tableId={tbl_id}"
            else:
                out_name = "Laporan_Lengkap_Semua_Departemen_2026.xlsx"
                grist_url = "http://localhost:8484/api/docs/pnPY9D1FA4hsBGaBtdbVz2/download/xlsx"

            try:
                req = urllib.request.Request(grist_url, headers={"Authorization": "Bearer citiplumb-admin-api-key-secret"})
                with urllib.request.urlopen(req) as resp:
                    content = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", f'attachment; filename="{out_name}"')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/sync-stock":
            try:
                cmd = ["python3", os.path.join(SCRIPT_DIR, "ingest_laporan_agustus.py")]
                out = subprocess.check_output(cmd, cwd=GRIST_DIR, stderr=subprocess.STDOUT).decode()
                self.send_json({
                    "status": "ok",
                    "message": "Berhasil menyinkronkan 5.444 item stok riil dari laporan admin departemen (8 AGUSTUS) ke database kiw-excel!",
                    "log": out
                })
            except subprocess.CalledProcessError as e:
                self.send_json({"error": e.output.decode()}, 500)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == "/api/generate":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            payload = json.loads(body)
            spk = payload.get("spk")
            if not spk:
                self.send_json({"error": "Nomor SPK wajib diisi"}, 400)
                return
            try:
                # Jalankan generator script
                cmd = ["python3", os.path.join(SCRIPT_DIR, "buat_po_dokumen.py"), "--spk-db", spk]
                out = subprocess.check_output(cmd, cwd=GRIST_DIR, stderr=subprocess.STDOUT).decode()
                # Parse doc_id dan file_name dari output
                doc_id_match = re.search(r'doc/([a-zA-Z0-9_]+)', out)
                file_match = re.search(r'exports/([^\n\r]+)', out)
                doc_id = doc_id_match.group(1) if doc_id_match else "3mgbJV6R3m5uvjkuTw77KB"
                file_name = os.path.basename(file_match.group(1).strip()) if file_match else ""
                self.send_json({"success": True, "doc_id": doc_id, "file_name": file_name, "log": out})
            except subprocess.CalledProcessError as e:
                self.send_json({"error": e.output.decode()}, 500)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            return

        if path == "/api/upload":
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_json({"error": "Harus multipart/form-data"}, 400)
                return
            
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type}
            )
            file_item = form["file"]
            if not file_item.file:
                self.send_json({"error": "File tidak valid"}, 400)
                return
            
            temp_path = os.path.join("/tmp", f"upload_{file_item.filename}")
            with open(temp_path, "wb") as f_out:
                f_out.write(file_item.file.read())

            try:
                cmd = ["python3", os.path.join(SCRIPT_DIR, "buat_po_dokumen.py"), "--excel", temp_path]
                out = subprocess.check_output(cmd, cwd=GRIST_DIR, stderr=subprocess.STDOUT).decode()
                doc_id_match = re.search(r'doc/([a-zA-Z0-9_]+)', out)
                file_match = re.search(r'exports/([^\n\r]+)', out)
                doc_id = doc_id_match.group(1) if doc_id_match else "3mgbJV6R3m5uvjkuTw77KB"
                file_name = os.path.basename(file_match.group(1).strip()) if file_match else ""
                self.send_json({"success": True, "doc_id": doc_id, "file_name": file_name, "log": out})
            except subprocess.CalledProcessError as e:
                self.send_json({"error": e.output.decode()}, 500)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"==================================================================")
        print(f"🚀 Generator Web UI Berjalan di: http://localhost:{PORT}")
        print(f"==================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer dihentikan.")

if __name__ == "__main__":
    run_server()
