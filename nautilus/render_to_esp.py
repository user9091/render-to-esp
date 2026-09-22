"""Nautilus extension providing a direct 'Render to ESP' image context action."""

import subprocess
import sys
from pathlib import Path

import gi

for version in ("4.1", "4.0"):
    try:
        gi.require_version("Nautilus", version)
        break
    except ValueError:
        continue
else:
    raise ImportError("Nautilus 4.x introspection data is required")
from gi.repository import GObject, Nautilus

SENDER = Path(__file__).resolve().parents[1] / "sender" / "send.py"


class RenderToESP(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, files):
        if len(files) != 1:
            return []
        file = files[0]
        if file.get_uri_scheme() != "file" or not (file.get_mime_type() or "").startswith("image/"):
            return []
        item = Nautilus.MenuItem(
            name="RenderToESP::send",
            label="Render to ESP",
            tip="Show this image on the network e-paper display",
        )
        item.connect("activate", self._send, file.get_location().get_path())
        return [item]

    def _send(self, _item, path):
        subprocess.Popen([sys.executable, str(SENDER), "--notify", path], start_new_session=True)
