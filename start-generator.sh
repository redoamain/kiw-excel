#!/usr/bin/env bash
# Menjalankan Web Generator di background (Port 8485)
pkill -f "web_generator.py" 2>/dev/null || true
nohup /usr/bin/python3 scripts/web_generator.py > /dev/null 2>&1 &
echo "✅ Web Generator aktif di: http://localhost:8485"
