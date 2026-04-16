#!/usr/bin/env python3
"""Build a self-contained .mcpb bundle that includes the server source code."""

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Source files to include inside the bundle (relative to ROOT)
SOURCE_FILES = [
    "pyproject.toml",
    "uv.lock",
    "icon.png",
    "src/mineru_open_mcp/__init__.py",
    "src/mineru_open_mcp/cli.py",
    "src/mineru_open_mcp/config.py",
    "src/mineru_open_mcp/server.py",
    "src/mineru_open_mcp/tools/__init__.py",
    "src/mineru_open_mcp/tools/extract.py",
    "src/mineru_open_mcp/tools/tools.py",
]


def main() -> None:
    manifest_path = ROOT / "mcpb" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest["version"]

    out_dir = ROOT / "mcpb"
    out_path = out_dir / f"mineru-open-mcp-{version}.mcpb"

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # manifest.json at bundle root
        zf.write(manifest_path, "manifest.json")

        for rel in SOURCE_FILES:
            src = ROOT / rel
            if not src.exists():
                print(f"  WARNING: missing {rel}, skipping", file=sys.stderr)
                continue
            zf.write(src, rel)
            print(f"  + {rel}")

    print(f"\nBundle written: {out_path}")
    print(f"  Files: {len(zf.namelist())}")


if __name__ == "__main__":
    main()
