"""Build hook: copy ui/dist into src/mineru_open_mcp/ui_dist/ before packaging."""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyWithUI(build_py):
    def run(self):
        src = Path(__file__).parent / "ui" / "dist"
        dst = Path(__file__).parent / "src" / "mineru_open_mcp" / "ui_dist"
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"[build] UI bundled: {src} → {dst}")
        else:
            print(f"[build] WARNING: {src} not found — browser UI will not be included.")
        super().run()


setup(cmdclass={"build_py": BuildPyWithUI})
