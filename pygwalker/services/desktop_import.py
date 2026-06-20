import base64
import json
import os
import subprocess
import sys
import urllib.parse
import zlib
from typing import Any, Callable, Dict, List, Optional


class DesktopImportService:
    """Build and open pygwalker desktop import links."""

    def __init__(self, open_link: Optional[Callable[[str], None]] = None):
        self.open_link = open_link or self._open_platform_link

    def import_to_desktop(
        self,
        *,
        spec: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
        records: List[Dict[str, Any]],
    ) -> None:
        self.open_link(self.build_import_link(spec=spec, fields=fields, records=records))

    def build_import_link(
        self,
        *,
        spec: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
        records: List[Dict[str, Any]],
    ) -> str:
        data_payload = json.dumps(
            records,
            default=lambda obj: obj.isoformat() if hasattr(obj, "isoformat") else str(obj),
        )
        spec_payload = json.dumps(spec)
        fields_payload = json.dumps(fields)
        return (
            "gw://import?"
            f"data={self._compress_payload(data_payload)}"
            f"&spec={self._compress_payload(spec_payload)}"
            f"&fields={self._compress_payload(fields_payload)}"
        )

    @staticmethod
    def _open_platform_link(link: str) -> None:
        if sys.platform == "win32":
            os.startfile(link)
            return

        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, link])

    @staticmethod
    def _compress_payload(data: str) -> str:
        compress = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, 15, 8, 0)
        compressed_data = compress.compress(data.encode())
        compressed_data += compress.flush()
        return urllib.parse.quote(base64.b64encode(compressed_data).decode())
