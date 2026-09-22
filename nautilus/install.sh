#!/usr/bin/env bash
set -euo pipefail
if command -v rpm >/dev/null && ! rpm -q nautilus-python >/dev/null 2>&1; then
    echo "Install nautilus-python first: sudo dnf install nautilus-python" >&2
    exit 1
fi
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
extension_dir="${XDG_DATA_HOME:-$HOME/.local/share}/nautilus-python/extensions"
mkdir -p "$extension_dir"
ln -sfn "$project_dir/nautilus/render_to_esp.py" "$extension_dir/render_to_esp.py"
nautilus -q || true
echo "Installed Render to ESP. Reopen Files and right-click an image."
