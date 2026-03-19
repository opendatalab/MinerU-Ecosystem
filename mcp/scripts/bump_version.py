#!/usr/bin/env python3
"""Increment the patch version in pyproject.toml and print the new version."""
import re
import sys
from pathlib import Path

toml = Path(__file__).parent.parent / "pyproject.toml"
text = toml.read_text()

m = re.search(r'^(version\s*=\s*")(\d+)\.(\d+)\.(\d+)(")', text, re.MULTILINE)
if not m:
    print("ERROR: could not find version = \"X.Y.Z\" in pyproject.toml", file=sys.stderr)
    sys.exit(1)

major, minor, patch = int(m.group(2)), int(m.group(3)), int(m.group(4))
new_version = f"{major}.{minor}.{patch + 1}"
new_text = text[: m.start()] + f'{m.group(1)}{new_version}{m.group(5)}' + text[m.end():]
toml.write_text(new_text)
print(new_version)
