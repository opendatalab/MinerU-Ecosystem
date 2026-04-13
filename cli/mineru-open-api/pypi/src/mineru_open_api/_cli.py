import os
import platform
import subprocess
import sys
from pathlib import Path


def _get_binary_path():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("amd64", "x86_64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    ext = ".exe" if system == "windows" else ""
    if system == "darwin":
        binary_name = f"mineru-open-api-darwin-{arch}{ext}"
    elif system == "linux":
        binary_name = f"mineru-open-api-linux-{arch}{ext}"
    elif system == "windows":
        binary_name = f"mineru-open-api-windows-{arch}{ext}"
    else:
        raise RuntimeError(f"Unsupported OS: {system}")

    binary_path = Path(__file__).parent / "bin" / binary_name
    if not binary_path.exists():
        raise FileNotFoundError(
            f"Binary not found: {binary_path}\n"
            f"Your platform ({system}-{arch}) may not be supported."
        )
    return str(binary_path)


def main():
    binary = _get_binary_path()
    if sys.platform != "win32":
        os.chmod(binary, 0o755)
    raise SystemExit(subprocess.call([binary] + sys.argv[1:]))
