.PHONY: build-wheel clean

# Build a redistributable wheel.
# Bumps the patch version, then packages with python -m build.
# mineru-open-sdk is a regular PyPI dependency — no vendoring needed.
build-wheel:
	rm -rf dist/ build/
	@NEW_VER=$$(python3 scripts/bump_version.py) && echo "[version] bumped to $$NEW_VER"
	python3 -m pip install --quiet build
	python3 -m build --wheel
	@echo ""
	@echo "Wheel ready in dist/:"
	@ls dist/*.whl

clean:
	rm -rf dist/ build/ src/*.egg-info
