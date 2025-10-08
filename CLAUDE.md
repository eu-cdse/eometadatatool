# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses **Nix** for development environment management. To set up:

```bash
# Enter the development environment
nix-shell

# Or use direnv for automatic loading
direnv allow
```

The project uses **UV** (modern Python package manager) instead of pip:

```bash
# Install/sync dependencies
uv sync --frozen

# Add new packages
uv add <package>
uv add <dev-package> --dev

# Remove packages  
uv remove <package>
```

## Common Development Commands

### Testing
```bash
# Run tests
uv run pytest

# Run tests with coverage (custom script in nix shell)
run-tests

# Run tests with terminal output
run-tests term

# Watch tests during development
watch-tests

# Run specific test files
uv run pytest tests/test_extract.py
```

### Code Quality
```bash
# Run linter
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
ruff format .

# Type checking
pyright
```

### Running the CLI
```bash
# Run the metadata extraction tool
uv run metadata_extract [arguments]

# Or after environment activation
metadata_extract [arguments]
```

### Building
```bash
# Build package
uv build

# Install in development mode
uv pip install -e .
```

## Architecture Overview

EOMetadataTool is a satellite imagery metadata extraction and STAC (SpatioTemporal Asset Catalog) generation system with these core components:

### Processing Pipeline
```
Input Scene → Classification → Mapping → Extraction → Rendering → STAC Output
```

### Key Components

**CLAS (Classification) System** (`eometadatatool/clas/`):
- `product_type.py`: Identifies satellite product types from scene names
- `collection_name.py`: Maps product types to standardized collections  
- `template.py`: Detects appropriate STAC templates
- `mapping.py`: Links product types to CSV mapping files

**Metadata Processing**:
- `extract.py`: Main async orchestrator for metadata extraction
- `mapping_loader.py`: Loads CSV mapping files with XPath queries
- `metafile_loader.py`: Handles various file formats (ZIP, NetCDF, XML, JSON)

**STAC Framework** (`eometadatatool/stac/framework/`):
- Modular STAC item, asset, and extension generation
- 60+ ESA-compliant templates for Copernicus Programme
- Template structure: `/stac/{mission}/template/` and `/stac/{mission}/mapping/`

**Dual Processing Model**:
- Local filesystem and S3 processing with unified `Path` interface
- Async/await throughout for non-blocking I/O
- Parallel processing with configurable workers and concurrency

### Data Flow
1. **Scene Classification**: CLAS identifies product type and collection
2. **Mapping Selection**: CSV mapping files define metadata extraction rules
3. **Concurrent Extraction**: Multiple metadata files processed in parallel
4. **Template Rendering**: Python templates transform raw metadata to STAC JSON
5. **Output Generation**: Final STAC-compliant JSON with optional validation

## Mission Support

The tool supports extensive satellite missions through modular templates:
- **Sentinel-1**: SLC, GRD, mosaics with various acquisition modes
- **Sentinel-2**: L1C, L2A, and quarterly mosaics
- **Sentinel-3**: OLCI, SLSTR, SRAL, SYNERGY products
- **Sentinel-5P**: TROPOMI L1B and L2 products
- **Landsat**: LC09 L1/L2 products
- **Custom missions**: Extensible through new template directories

## Important Notes

- **Python 3.13+**: Uses modern Python syntax and features
- **Async-first**: Extensive use of asyncio for performance
- **Type safety**: Comprehensive type hints with pyright checking
- **S3 integration**: Native cloud storage support with intelligent caching
- **Testing**: Async test configuration in `tests/conftest.py`
- **Performance**: Built-in profiling and timing decorators available

## Adding New Missions

To add support for a new satellite mission:

1. Create directory structure: `/eometadatatool/stac/{mission-name}/`
2. Add mapping CSV: `/mapping/{product}.csv` with XPath extraction rules
3. Create template: `/template/stac_{mission}.py` for STAC generation
4. Update CLAS components to recognize new product patterns
5. Add example outputs in `/example/` directory

## Configuration

- **S3 credentials**: Place `credentials.json` in project root (auto-loaded by nix-shell)
- **Environment variables**: Standard boto3 configuration supported
- **Development**: Use `shell.nix` for custom environment modifications