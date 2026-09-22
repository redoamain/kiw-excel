#!/usr/bin/env bash
# ==============================================================================
# kiw-excel - Interactive PO Generator
# Mempermudah tim PPIC membuat dokumen Production Planning & Excel per PO
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/usr/bin/python3"

echo ""
echo "=================================================================="
echo "    🚀 KIW-EXCEL: GENERATOR PRODUCTION PLANNING & MRP (PER PO)   "
echo "=================================================================="
echo ""
echo "Pilih sumber data PO baru yang ingin Anda proses:"
echo ""
echo "  [1] Tarik langsung dari Database WinCP / MSSQL (seperti sveltekiw)"
echo "  [2] Impor dari File Excel PO Marketing (contoh: AB_PO#...xlsx)"
echo "  [3] Input Cepat Manual (No SPK, Kode Produk, Qty)"
echo "  [4] Keluar"
echo ""
read -p "Masukkan pilihan Anda [1-4]: " PILIHAN

case "$PILIHAN" in
  1)
    echo ""
    echo "--> Mengambil daftar SPK aktif dari database WinCP..."
    $PYTHON_BIN "$SCRIPT_DIR/scripts/tambah_po.py" --list-db
    echo ""
    read -p "Ketik Nomor SPK yang ingin diproses (contoh: AS-26/02/012): " SPK_INPUT
    if [ -z "$SPK_INPUT" ]; then
      echo "❌ Nomor SPK tidak boleh kosong."
      exit 1
    fi
    echo ""
    echo "--> Memproses SPK $SPK_INPUT..."
    $PYTHON_BIN "$SCRIPT_DIR/scripts/buat_po_dokumen.py" --spk-db "$SPK_INPUT"
    ;;

  2)
    echo ""
    read -p "Masukkan path/lokasi file Excel PO: " FILE_INPUT
    # Bersihkan kutip jika ada (drag and drop terminal)
    FILE_INPUT="${FILE_INPUT%\'}"
    FILE_INPUT="${FILE_INPUT#\'}"
    FILE_INPUT="${FILE_INPUT%\"}"
    FILE_INPUT="${FILE_INPUT#\"}"
    
    if [ ! -f "$FILE_INPUT" ]; then
      echo "❌ File tidak ditemukan: $FILE_INPUT"
      exit 1
    fi
    echo ""
    echo "--> Memproses file Excel $FILE_INPUT..."
    $PYTHON_BIN "$SCRIPT_DIR/scripts/buat_po_dokumen.py" --excel "$FILE_INPUT"
    ;;

  3)
    echo ""
    read -p "Nomor SPK (contoh: AS-26/09/001): " M_SPK
    read -p "Nama PO (contoh: NL PO#STK-99): " M_PO
    read -p "Kode Barang Jadi (contoh: AB-SPRY-SL2000): " M_PROD
    read -p "Target QTY Produksi (contoh: 1000): " M_QTY
    echo ""
    $PYTHON_BIN "$SCRIPT_DIR/scripts/tambah_po.py" --spk "$M_SPK" --po "$M_PO" --produk "$M_PROD" --qty "$M_QTY"
    ;;

  4)
    echo "Keluar."
    exit 0
    ;;

  *)
    echo "Pilihan tidak valid."
    exit 1
    ;;
esac
