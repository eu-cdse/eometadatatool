# Building New STAC Templates in eometadatatool

This guide explains how to add new STAC item templates to this repository. It covers project structure, the end‑to‑end flow from metadata to STAC, how to write a template, how to add mappings, how to validate correctness, and where to research domain details.

The goals are simplicity, consistency, and correctness. Follow existing patterns, keep control flow linear, and reuse the framework utilities provided here.

## Overview

- What you build: a Python template (`stac_*.py`) that turns mapped metadata into a valid STAC Item JSON for a specific product/collection.
- Where it fits: templates live under `eometadatatool/stac/<collection>/template/*`.
- How it runs: the core app extracts metadata + files, applies mapping CSV rules, then calls your template’s `render(attr)` which uses the framework (Item/Assets/Links/Extensions) to assemble the STAC Item.
- How it’s verified: automated validation checks Items against the STAC specification.

## Non‑Negotiables

- Online research is mandatory. Do not rely solely on this repository; confirm product details with authoritative public sources and cite them.
- Do not write code until a complete `RESEARCH.md` exists (see below).
- Keep the research file up to date during implementation when decisions change; record source links for any new assumptions.
- Prefer official specs and mission handbooks over secondary sources; reconcile conflicts and document the rationale.
- Do not assume local access to scene files. You can progress research using documentation, OData/API examples, and naming conventions.
- Respect invariants (see "Invariants, Casting, and Fallbacks"). Avoid defaults, silent fallbacks, or forced casts; surface unexpected states instead of masking them.

## Connectivity Check (required)

Before starting, verify outbound internet connectivity. For example:

```sh
curl -sSf https://github.com >/dev/null
```

If the check fails, stop and fix connectivity (or request access) before proceeding. Do not attempt implementation without working internet access.

## Repository Structure Essentials

- Collection folders live under `eometadatatool/stac/<collection>/`:
  - `template/` — must contain exactly one template file matching `stac*.py`.
  - `mapping/` or `mappings/` — CSV rules used to extract normalized attributes consumed by your template.
- Shared framework code (do not duplicate):
  - STAC assets: `eometadatatool/stac/framework/stac_asset.py`
  - Bands definitions: `eometadatatool/stac/framework/stac_bands.py`
  - STAC item builder: `eometadatatool/stac/framework/stac_item.py`
  - STAC links: `eometadatatool/stac/framework/stac_link.py`
  - Extensions enum: `eometadatatool/stac/framework/stac_extension.py`
- Mappings infrastructure:
  - Global routing: `eometadatatool/mappings/ProductTypes2RuleMapping.csv`
  - Loader: `eometadatatool/mapping_loader.py`, `eometadatatool/clas/mapping.py`
- Template auto‑detection (by filename): `eometadatatool/clas/template.py`

## Lifecycle Overview

- Stage 1 — Discover: Research the mission and product type (collection). Prefer selecting a representative scene if available; otherwise capture the authoritative scene filename/identifier scheme with example IDs/filenames from docs or catalogs. Record sources and decisions in `RESEARCH.md`.
- Stage 2 — Map: Create mapping CSV(s) that yield the normalized attributes your template needs; add routing in `ProductTypes2RuleMapping.csv`.
- Stage 3 — Implement: Write `template/stac_<name>.py` (async `render(attr)`) using the framework’s item, assets, links, and extensions.
- Stage 4 — Choose STAC Extensions: Decide and declare only the extensions you actually use, based on emitted fields.
- Stage 5 — Detect & Route: Add or confirm filename‑based template detection in `clas/template.py`.
- Stage 6 — Validate & Ship: Validate the Item, sanity‑check roles/projection/extensions, and ship with a concise change summary.

## Invariants, Casting, and Fallbacks

- Try to research and verify any ambiguities first. Do not guess or make unfounded assumptions.
- Inside templates, trust the mapped `attr`. Use `attr[...]` for required fields. Use `attr.get(...)` only for fields that are truly optional per spec or where ambiguity is documented. If a required value is missing, prefer failing fast.
- Use casts and fallbacks only as a last resort.

## System Orchestration (reference)

- Scene path → mapping (normalized `attr`) → `render(attr)` → STAC Item → validation.
See: `eometadatatool/metadata_extract.py` and `eometadatatool/extract.py` for orchestration.

## Stage 1 — Discover (Research the Product)

- Identify the exact mission/instrument/product (e.g., S1 GRD, S2 L2A, S3 OL2, S5P L2, DEMs, CCM). Pin down level, subtype, timeliness, and expected file structure.
- Start with official references (skim first, then deep‑dive as needed):
  - STAC core and extensions (what fields exist and how to use them): <https://github.com/radiantearth/stac-spec> and the extension registry <https://stac-extensions.github.io/>
  - Copernicus SentiWiki Document Library (product and metadata specs): <https://sentiwiki.copernicus.eu/web/document-library>
  - CDSE docs (OData, S3, `zipper`, auth): <https://documentation.dataspace.copernicus.eu/>
  - ESA mission product specs/handbooks for the product type (SAFE structure, metadata fields, band/channel definitions, units, masks). Examples (search by scene filename or identifier in docs/catalogs):
    - Sentinel‑1 Product Specification (GRD/SLC SAFE structure, polarization, instrument modes)
    - Sentinel‑2 MSI L1C/L2A Product Specification (JP2 assets, TCI, QA bands)
    - Sentinel‑3 (OLCI/SLSTR/SRAL) Product Guides (band sets, geometric parameters)
    - Sentinel‑5P TROPOMI L1B/L2 Product Readmes (variables, timeliness)
- Research workflow (practical):
  - Use targeted queries combining mission, product, and metadata keywords.
  - Open representative products (OData or sample archives) and skim manifest/metadata to locate geometry, time, orbit, projection and assets.
  - Inspect a data file with GDAL (`gdalinfo -json`): check projection, shape, transform, data type, nodata, and the generated `stac` block.
  - Keep a short decision log with sources (URLs + section names) for each choice so reviewers can verify.
- Cross‑check public STAC Items for the same mission to confirm naming and extension usage; reconcile with STAC spec pages.
- Optional: If a representative scene becomes available (from research or provided), use standard tools for targeted analysis, e.g.:
  - `curl` to fetch small metadata files; `aws s3 ls/cp` (if relevant buckets are accessible);
  - `gdalinfo -json` to inspect raster projection, shape, transform, dtype, nodata;
  - `ncdump -h` to peek NetCDF structure (dimensions/variables/attributes);
  - `jq` to explore JSON (e.g., OData/STAC payloads).
  Use them to validate assumptions and record key findings in the research notes.

### Research deliverable (required before coding)

- Add `RESEARCH.md` under `eometadatatool/stac/<collection>/` capturing (use public online sources and cite with full URLs):
  - Sources: 5–7 authoritative links with one‑line purpose per link.
  - Product structure: SAFE layout overview and where key metadata lives (time, orbit, geometry, projection, assets).
  - STAC mapping approach: extensions you will use and the key item/asset fields you plan to emit (bulleted list).
- Evidence: either (a) a representative scene with link/reference, or (b) the authoritative scene filename/identifier scheme with one or two example IDs/filenames from documentation or catalogs. Include example file paths if known and a few key metadata fields to map. If no scene is accessible yet, note that fixtures are pending — this is acceptable when documentation is sufficient.
  - Assumptions & open questions: anything not fully resolved with a short plan to verify.
- Acceptance criteria: what “done” means for this mission (e.g., automated validation passes, extensions consistent).

Suggested scaffold:

```md
# RESEARCH

## Sources
- [Link] — purpose

## Product structure
- SAFE layout; where time/orbit/geometry/projection/assets live

## Planned STAC mapping
- Extensions: ...
- Item fields: ...
- Asset fields/extras: ...

## Evidence
- Representative scene: ... (link/ref)  OR
- Filename/identifier scheme + example IDs/filenames: ... (link/ref)
- Example file paths: ... (if known)
- Key metadata fields: ...

## Assumptions / open questions
- ...

## Acceptance criteria
- ...
```

If you’re using an automation/agent, ensure it produces this file first and only then proceeds to implementation.

### Planning (recommended)

- Make a brief plan of action (key steps and order).

### Use existing patterns

- Reuse nearby templates and mappings; see “Where to look” for concrete examples. Helpful starting points:
  - Sentinel‑2 L2A: `eometadatatool/stac/sentinel-2-l2a/template/stac_s2l2a.py`
  - Sentinel‑1 SLC: `eometadatatool/stac/sentinel-1-slc/template/stac_s1_slc.py`
  - Sentinel‑5P L2: `eometadatatool/stac/sentinel-5p/template/stac_s5p.py`
  - DEM COG: `eometadatatool/stac/copdem-cog/template/stac_copdem_cog.py`

### Where to look

- Targeted search: combine mission/product name with keywords like "product specification", "SAFE", "user guide", "metadata", "naming", "filename pattern", "identifier".
- Official mission/product specs and handbooks: Copernicus SentiWiki Document Library <https://sentiwiki.copernicus.eu/web/document-library> and agency portals.
- Platform/APIs for data access: CDSE docs (OData, S3, `zipper`, auth) <https://documentation.dataspace.copernicus.eu/>.
- Real products (OData/S3 archives) to confirm field names and SAFE structure.
- Public STAC catalogs to see extension/role usage.
- STAC examples and guidance: STAC best‑practice examples <https://github.com/radiantearth/stac-spec/tree/master/examples> and `stactools` packages <https://github.com/stactools-packages>.
- Other mission resources as needed (e.g., USGS Landsat Collection 2 docs <https://www.usgs.gov/landsat-missions/collection-2>).

Cross‑check sources: don’t stop at the first match; consult multiple docs and catalogs to confirm details and broaden understanding.

### Interpreting Product Metadata into STAC

- Item properties: derive from official metadata/OData (time range, platform/instrument, orbit, processing). Keep names consistent with existing mission templates.
- Assets: prefer framework asset classes (COG/JP2/NetCDF/XML/Thumbnail/Product) with minimal, typed extras. See “Asset Patterns and Conventions”.

## Stage 2 — Map (CSV)

Templates consume a normalized attribute dict `attr` populated from your mapping CSV(s). Each row describes how to extract one attribute from an input file using XPath/XQuery‑like expressions or static values.

- Place mapping file(s) in `eometadatatool/stac/<collection>/mapping/` or `mappings/`.
- CSV schema: `metadata;file;mappings;datatype`
  - `metadata` is the output key (e.g., `beginningDateTime`, `asset:B02`, `asset:proj:shape:10:NROWS`).
  - `file` is the input filename (e.g., `MTD_MSIL2A.xml`, `manifest.safe`, `static`).
  - `mappings` is the extraction expression (XPath, helper functions, literals for `static`).
  - `datatype` is one of String, Int64, Double, DateTimeOffset, etc.
- Add a route for your product type to `eometadatatool/mappings/ProductTypes2RuleMapping.csv` so the loader selects your CSV by ESA product type.
- Reuse existing key names where possible (see S2 L2A mapping for common keys, e.g., temporal, orbit, EPSG, per‑asset paths and per‑asset projection info).

Tip: Keep mappings minimal but sufficient—let the template focus on assembly, not parsing.

Mapping expression helpers live in `eometadatatool/function_namespace.py` (authoritative list with behavior). Common helpers include turning coordinate lists into WKT (`WKT(...)`), simple string transforms, JSON mapping (`map(...)`), and date helpers (`date_format`, `date_diff`). Note: `WKT(...)` defaults to `input_mode='latlon'` (lat,lon). If your source is lon,lat, pass `input_mode='lonlat'`. For examples/patterns, use existing mappings such as `eometadatatool/stac/sentinel-2-l2a/mapping/S2_MSI_L2A.csv` as a reference.

## Stage 3 — Implement (Template)

Create `eometadatatool/stac/<collection>/template/stac_<name>.py` with an async `render(attr)` function. Minimal, content‑first example:

```python
from typing import Any
from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink, ZipperLink
from eometadatatool.stac.framework.stac_extension import StacExtension

async def render(attr: dict[str, Any]) -> dict[str, Any]:
    # 1) Item‑level properties (content first; use mapped keys)
    props = {
        '_private': {
            'product_size': attr['private:product_size'],
        },
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': attr['platformShortName'] + attr['platformSerialIdentifier'],
        'constellation': attr['platformShortName'].lower(),
        'instruments': (attr['instrumentShortName'].lower(),),
        # Processing level must be provided by mapping per mission spec
        'processing:level': attr['processingLevel'],
        'product:type': attr['productType'],
        # add mission‑specific props here…
    }
    # Include optional properties only when present; do not guess
    if proj_code := attr.get('proj:code'):
        props['proj:code'] = proj_code

    # 2) OData context (enables auth/links/checksums/HTTP hrefs)
    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)

    # 3) Assets (use framework classes; add mission-specific extras)
    asset_extra: dict[str, Any] = {}
    if gsd := attr.get('gsd'):
        asset_extra['gsd'] = gsd
    if proj_code := attr.get('proj:code'):
        asset_extra['proj:code'] = proj_code
    assets = {
        # product/SAFE manifest; pick the file name that exists for your mission
        'manifest': ProductManifestAsset(path=f"{item_path}/manifest.safe"),

        # optional quicklook thumbnail
        'thumbnail': ThumbnailAsset(path=attr['ql:path']) if 'ql:path' in attr else None,

        # primary measurement (example with COG; use JPEG2000Asset/NetCDFAsset/etc. as appropriate)
        'measurement': CloudOptimizedGeoTIFFAsset(
            path=f"{item_path}/{attr['asset:DATA']}",
            title='Primary measurement', roles=('data',),
            # Only include extras that are present and justified by spec
            extra=asset_extra,
            checksum=attr.get('asset:DATA:checksum'),
            size=attr.get('asset:DATA:size'),
        ),
    }
    assets = {k: v for k, v in assets.items() if v is not None}

    # 4) Links (traceability + zipper directory)
    links = [
        TraceabilityLink(href=f"{odata.name}.zip"),
        ZipperLink(href=item_path),
    ]

    # 5) Build item using framework (adds defaults, auth/storage, etc.)
    item = STACItem(
        path=item_path,
        odata=odata,
        collection='<your-collection-id>',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],  # WKT from mapping
        links=links,
        assets=assets,
        extensions=(
            StacExtension.PROJECTION,
            StacExtension.RASTER,
            # add EO/SAR/VIEW/SATELLITE/GRID/FILE/etc. as needed
        ),
        extra=props,
    )

    return await item.generate()
```

Key points:

- Prefer invariants over defenses: use `attr[...]` for required fields; omit unknown optional keys instead of filling placeholders. Use `attr.get(...)` only for truly optional fields backed by the spec.
- Use the provided asset classes; add mission‑specific extras (bands via `generate_bands`, gsd, lineage, `proj:*`, etc.) so downstream users understand each asset.
- Extensions: add only those for fields you emit; see Stage 4 — Choose STAC Extensions.
- Links: include product traceability (`TraceabilityLink`) and a `ZipperLink` to the product directory when the path is known.
- Processing level normalization can be mission‑specific (e.g., S‑6 uses `'L' + attr['processingLevel']`).
- Return only the dict from `item.generate()`.

Real templates often declare many assets (per-band JP2/NetCDF, derived products, manifests, ancillary data). Add each using the best-fit asset class, populate checksums/sizes, and include mission-specific extras for context.

Good real‑world references: `eometadatatool/stac/sentinel-2-l2a/template/stac_s2l2a.py` (EO/COG‑centric) and `eometadatatool/stac/sentinel-6/template/stac_s6.py` (netCDF/SAFE‑centric).

## Stage 4 — Choose STAC Extensions

Choose and declare only the extensions your Item actually uses.

- Research and pick:
  - Extension registry: use <https://stac-extensions.github.io/> to locate the extension, confirm scope (Item/Collection/Asset), check maturity, review dependencies, and copy the identifier URL you will place in `eometadatatool/stac/framework/stac_extension.py`.
  - Extension repositories: read the extension’s README and schemas to understand required/optional fields, behavior, and any cross‑extension dependencies (linked from the registry page).

- Decide to include when:
  - You emit at least one namespaced field from that extension (e.g., `proj:*`, `raster:*`, `eo:*`, `sar:*`, `file:*`).
  - Scope matches where you set fields. Asset‑level fields still require the parent Item to declare the extension.
  - The extension’s maturity is Stable/Candidate/Pilot.

- Common pairs:
  - `PROJECTION` when using any `proj:*` field or per‑asset projection metadata.
  - `RASTER` when emitting `raster:*`, nodata/dtype/scale/offset, or band matrices.
  - `EO` for optical bands/reflectance; `SAR` for radar modes/polarizations.
  - `PRODUCT`/`PROCESSING` for product metadata; `VIEW`/`SATELLITE` for angles/orbit.
  - `FILE` when using `file:*` checksums/sizes outside of framework defaults.

Start with none; add only those justified by fields you emit.

## Stage 5 — Detect & Route (if needed)

If your product filename pattern is not handled yet, add a rule in `eometadatatool/clas/template.py` so the system can auto‑select your `stac_*.py` for that product. The file documents the existing heuristics; follow those patterns and return your template stem without suffix.

## Stage 6 — Validate & Ship

- Validate the generated Item against the STAC spec.
- Sanity‑check assets (roles, projection code, nodata/dtype, gsd where relevant) and extension usage.
- Ensure alternates/auth/storage behave correctly when `odata` or S3 paths are present.
- Confirm the acceptance criteria in `RESEARCH.md` are met and perform a deep verification pass.

## Asset Patterns and Conventions

- Prefer these classes:
  - `ProductAsset` — the zipped product (auto‑managed by `STACItem` when `odata` is present; don’t add it yourself unless you need a custom name via `product_asset_name`).
  - `CloudOptimizedGeoTIFFAsset` — COGs (fills proj/datatype/nodata if available via GDAL).
  - `JPEG2000Asset` — JP2 data (S2 style), typically with `bands`, `gsd`, `proj:*` extras.
  - `XMLAsset`, `NetCDFAsset`, `ThumbnailAsset`, `ProductManifestAsset` — as needed.
- Roles: use small, composable roles to encode semantics and invariants:
  - Data roles: `('data',)`, add qualifiers like `'reflectance'`, `'gsd:10m'`, `'sampling:original|upsampled|downsampled'`.
- Visualization: `('visual', 'overview')` (e.g., TCI).
  - Metadata: `('metadata',)`; Thumbnail: `('thumbnail',)`.
- Extras to prefer (keep minimal, accurate, and typed):
  - For rasters: `'bands'` (from `stac_bands`), `'data_type'`, `'nodata'`, `'raster:scale'`, `'raster:offset'`, `'gsd'`.
  - Projection (per‑asset when needed): `'proj:code'`, `'proj:shape'`, `'proj:transform'`, `'proj:bbox'`.
- Bands: use `generate_bands(<BAND_TABLE>, names)` to attach EO/SAR band metadata. EO bands auto‑add the EO extension; SAR bands auto‑add SAR.
- Checksums and sizes:
  - Product zip: taken from OData automatically (`ProductAsset`).
  - Other assets: use mapped `:<file>:checksum` and `:<file>:size` from `extract()` when available. Defaults to MD5 multihash if you pass `checksum`.
- Alternates and hrefs:
  - S3 paths are detected and become alternates automatically.
  - `https` hrefs come from OData zipper when `https_href='zipper'` (default for `STACAsset`) and `odata` is present.
  - Authentication and storage schemas are attached automatically.

Thumbnails (quicklooks):

- If your thumbnail is not named like `*-ql.*`, `quicklook.*`, or `thumbnail.*`, map it explicitly with `asset:quicklook` to the relative path (and optionally `asset:quicklook:checksum` and `asset:quicklook:size`). The extractor will then populate `ql:*` keys consumed by `ThumbnailAsset`.

## Item‑Level Properties: Common Fields

- Time: `datetime`, `start_datetime`, `end_datetime`.
- Platform: `platform`, `constellation`, `instruments` (lowercase short names, arrays where needed). Some missions include a platform serial (e.g., appending `A`/`B`/`C`); follow existing mission templates.
- Processing: `processing:level`, `processing:datetime`, `processing:version`, optional `processing:facility`.
- Processing names may be mission‑specific (e.g., `'L2'`, `'L1C'`, or `'L' + attr['processingLevel']`). Match existing templates for that mission.
- Product: `product:type`, `product:timeliness`, `product:timeliness_category`.
- Geometry: `coordinates` from mapping (WKT), `bbox` is computed by the framework.
- Mission‑specific: EO/SAR angles, orbits, look direction, view geometry, `grid:code`, etc.
- The framework auto‑adds:
  - `processing:software` with the current `eometadatatool` version.
  - `auth:schemes` and `storage:schemes`.
  - `eopf:origin_datetime` when `odata` is present.
  - `expires` far in the future.

## Practical Patterns By Mission

- Sentinel‑2 (L1C/L2A): many per‑band JP2 assets with per‑asset `gsd`, `proj:*`, and EO bands; classification maps with `classification:classes` at original resolution; TCI (`visual`). See `sentinel-2-l2a/template/stac_s2l2a.py`.
- Sentinel‑1 (GRD/SLC + mosaics): SAR polarizations/modes, `sar:*` properties, radiometric or RTC specifics; for code patterns see `sentinel-1-slc/template/stac_s1_slc.py` or `sentinel-1-mosaic/templates/stac_s1_mosaic.py`.
- Sentinel‑3 (OL/SL/SR/SY): multiple instruments, per‑product metadata nuance. Reuse EO band tables from `stac_bands.py`.
- Sentinel‑5P (L1B/L2): netCDF assets, timeliness categories, scientific and product extensions, summarized GSD per subtype. See `sentinel-5p/template/`.
- DEMs and mosaics: COGs with `proj:*`, large overviews, simple role sets, few properties. See `copdem-cog/template/` and `landsat-mosaic/template/`.

## Appendix: Attribute Naming Cheatsheet (starter list)

Use these as quick reminders when drafting mappings; they’re not exhaustive. Check similar mission mappings and mission documentation online for comprehensive field lists.

Item‑level

- `beginningDateTime`, `endingDateTime`, `processingDate`, `processorVersion`
- `platformShortName`, `platformSerialIdentifier`, `instrumentShortName`
- `orbitNumber` (`sat:absolute_orbit`), `relativeOrbitNumber`, `orbitDirection`
- `cloudCover`, `productType`, `epsg`, `grid:code`, `coordinates` (WKT)
- Mission specifics: `view:*`, `eopf:*`, `sar:*`, `eo:*`

Per‑asset (examples)

- `asset:<BAND>` — relative path (e.g., `B02`, `TCI`, `AOT`, `SCL`)
- `asset:<BAND>:view:azimuth`, `asset:<BAND>:view:incidence_angle`
- `asset:proj:shape:<gsd>:(NROWS|NCOLS)`, `asset:proj:transform:<gsd>:(ULX|ULY)`
- `nodata` — nodata value for rasters
- File stats added by `extract()`: `<file>:checksum`, `<file>:size`

Keep new keys consistent with existing ones; prefer reusing names to maximize template uniformity.

---

When in doubt, open a nearby, production‑ready template and copy its structure. Consistency is key — templates should read similarly across missions, with differences only where the data requires it.
