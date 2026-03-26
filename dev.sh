#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-5500}"

echo "Astro dev server en:"
echo "  http://localhost:${PORT}"
echo ""
echo "Para abrirlo desde el movil en la misma Wi-Fi:"
echo "  http://$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo TU-IP-LOCAL):${PORT}"
echo ""
echo "Pulsa Ctrl+C para parar."

npm run dev -- --port "${PORT}"
