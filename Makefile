.SILENT: ;               # No need for @
.ONESHELL: ;             # Single shell for a target (required to properly use all of our local variables)
.EXPORT_ALL_VARIABLES: ; # Send all vars to shell
.DEFAULT: help # Running Make without target will run the help target

.PHONY: help init clean run package
help: ## Show Help
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

init: ## Init or resync development environment
	uv sync

clean: ## Remove build and temporary files
	rm -rf dist/*

run: init ## Run application
	uv run python main.py

package: clean init ## Generate Python wheel and macOS App bundle
	echo "Building Python wheel..."
	uv build --wheel
	echo ""
	echo "✓ Wheel created in dist/"
	echo ""
	echo "Building macOS App Bundle with PyInstaller..."
	echo "Installing PyInstaller if needed..."
	uv pip install pyinstaller
	echo "Creating app bundle..."
	uv run pyinstaller geosetter_lite.spec
	echo ""
	echo "✓ macOS App Bundle created in dist/GeoSetter Lite.app"
