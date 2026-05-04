#!/usr/bin/env python3
"""Local preview server with auto-rebuild.

Serves rendered HTML from _site/ and routes any /assets/* request to the
project's source ./assets/ directory. Rebuilds the site automatically when
any source file under content/, _data/, _layouts/, _includes/, or
_config.yml has changed since the last build, so editing markdown and
hitting reload always shows fresh output.

Usage:
    python3 scripts/serve.py [port]
"""

from __future__ import annotations

import http.server
import importlib
import socketserver
import sys
import threading
from pathlib import Path

import build_site

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
DEFAULT_PORT = 8000

WATCH_PATHS = [
    ROOT / "content",
    ROOT / "_data",
    ROOT / "_layouts",
    ROOT / "_includes",
    ROOT / "_config.yml",
    ROOT / "scripts" / "build_site.py",
]
SKIP_REBUILD_PREFIXES = ("/assets/",)

_build_lock = threading.Lock()
_last_built_at = 0.0
_build_script_mtime = (ROOT / "scripts" / "build_site.py").stat().st_mtime


def latest_source_mtime() -> float:
    latest = 0.0
    for path in WATCH_PATHS:
        if path.is_file():
            latest = max(latest, path.stat().st_mtime)
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    latest = max(latest, child.stat().st_mtime)
    return latest


def maybe_rebuild() -> None:
    global _last_built_at, _build_script_mtime
    with _build_lock:
        # Hot-reload build_site itself if its source changed, so edits to
        # the renderer take effect without a serve.py restart.
        script_mtime = (ROOT / "scripts" / "build_site.py").stat().st_mtime
        if script_mtime > _build_script_mtime:
            print("  ↻ scripts/build_site.py changed — reloading module")
            importlib.reload(build_site)
            _build_script_mtime = script_mtime
            _last_built_at = 0.0  # force a rebuild

        if latest_source_mtime() <= _last_built_at:
            return
        print("  ↻ source changed — rebuilding")
        build_site.main()
        _last_built_at = latest_source_mtime()


class OverlayHandler(http.server.SimpleHTTPRequestHandler):
    """Serves _site/ by default, with /assets/* falling through to ./assets/."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == "/assets" or clean.startswith("/assets/"):
            return self._translate_under(ROOT, path)
        # Static-file collections under content/<dir>/ are served at /<dir>/*
        # so the page route /<dir>/ (rendered HTML) and the files coexist.
        # Only kick in when there's a filename — bare `/<dir>/` is the page.
        if "/" in clean.lstrip("/") and "." in clean.rsplit("/", 1)[-1]:
            content_path = ROOT / "content" / clean.lstrip("/")
            if content_path.is_file():
                return self._translate_under(ROOT / "content", path)
        return super().translate_path(path)

    def _translate_under(self, directory: Path, path: str) -> str:
        saved = self.directory
        try:
            self.directory = str(directory)
            return super().translate_path(path)
        finally:
            self.directory = saved

    def do_GET(self) -> None:
        if not self.path.startswith(SKIP_REBUILD_PREFIXES):
            maybe_rebuild()
        super().do_GET()


def main() -> int:
    maybe_rebuild()

    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", port), OverlayHandler) as httpd:
        print(f"Serving _site/ + assets/ overlay at http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
