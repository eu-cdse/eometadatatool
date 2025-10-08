# EOMetadataTool

EOMetadataTool is a table-controlled metadata extractor for Earth observation (EO) products, designed to process satellite imagery metadata and generate both **STAC-compliant** outputs and custom formats.
The tool was originally created by [Christoph Reck](https://github.com/dlr-eoc/EOMetadataTool) and is now enhanced and maintained by the **CloudFerro S.A.** Data Science team: **Jan Musiał, Bartosz Staroń, Michał Bojko, Jacek Chojnacki, Tomasz Furtak, Kamil Monicz, and Marcin Niemyjski**.

Satellite data comes from a wide variety of sources, formats, and missions, each with its own structure, naming conventions, and metadata standards. This diversity creates a not entirely coherent ecosystem, making it challenging to organize, compare, and reuse data efficiently.

EOMetadataTool addresses this by using CSV-based templates to define XPath rules for extracting metadata, allowing full configurability without modifying the code. The template-driven approach enables easy adaptation to different missions and formats.

### Key capabilities include:

- **Multi-format support**: Reads metadata from ZIP, GZIP, TAR, SAFE, NetCDF files, and directory structures
- **Flexible extraction**: Uses XPath expressions with custom function extensions for complex metadata processing
- **Template-driven output**: Generates STAC, EOP XML, JSON, or custom formats using Jinja templates or Python scripts
- **Embeddable API**: Integrates seamlessly into existing Python applications

### Supported STAC Collections

<details><summary>Sentinel Collections (click to expand)</summary>

| collection            |
|-----------------------|
| sentinel-1-grd-cog    |
| sentinel-1-mosaic     |
| sentinel-1-slc        |
| sentinel-2-l1c        |
| sentinel-2-l2a        |
| sentinel-2-mosaics    |
| sentinel-3-ol1-efr    |
| sentinel-3-ol1-efrrr  |
| sentinel-3-ol1-err    |
| sentinel-3-ol2-lfr    |
| sentinel-3-ol2-lrr    |
| sentinel-3-ol2-wfr    |
| sentinel-3-ol2-wrr    |
| sentinel-3-sl1-rbt    |
| sentinel-3-sl2-aod    |
| sentinel-3-sl2-frp    |
| sentinel-3-sl2-lst    |
| sentinel-3-sl2-wst    |
| sentinel-3-sr1-sra    |
| sentinel-3-sr1-sra-a  |
| sentinel-3-sr1-sra-bs |
| sentinel-3-sr2-lan    |
| sentinel-3-sr2-lan-hy |
| sentinel-3-sr2-lan-li |
| sentinel-3-sr2-lan-si |
| sentinel-3-sr2-wat    |
| sentinel-3-sy2-aod    |
| sentinel-3-sy2-syn    |
| sentinel-3-sy2-v10    |
| sentinel-3-sy2-vg1    |
| sentinel-3-sy2-vgp    |
| sentinel-5p-l1-ir-sir |
| sentinel-5p-l1-ir-uvn |
| sentinel-5p-l1-ra-bd  |
| sentinel-5p-l2-aer-ai |
| sentinel-5p-l2-aer-lh |
| sentinel-5p-l2-ch4    |
| sentinel-5p-l2-cloud  |
| sentinel-5p-l2-co     |
| sentinel-5p-l2-hcho   |
| sentinel-5p-l2-no2    |
| sentinel-5p-l2-np-bd3 |
| sentinel-5p-l2-np-bd6 |
| sentinel-5p-l2-np-bd7 |
| sentinel-5p-l2-o3     |
| sentinel-5p-l2-o3-pr  |
| sentinel-5p-l2-so2    |
| sentinel-5p-l2-o3-tcl |

</details>

---

## Data Access

The primary data source for **EOMetadataTool** is an **S3 bucket** containing complete satellite products from major missions.
However, processing of locally stored data is also supported. In our main use case, we use the **EODATA S3 repository** from the **Copernicus Data Space Ecosystem (CDSE)**, which hosts a wide range of satellite data — primarily from the **Sentinel missions**, but also additional datasets.

To access this repository, you must generate your own **CDSE S3 credentials**. The full procedure for generating credentials is documented [here](https://documentation.dataspace.copernicus.eu/APIs/S3.html) and can be performed via the [CDSE portal](https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/auth?client_id=cdse-public&response_type=code&scope=openid&redirect_uri=https%3A//dataspace.copernicus.eu/account/confirmed/1).

To connect EOMetadataTool, you will need:
- **aws_s3_endpoint** – the CDSE S3 endpoint URL
- **aws_access_key_id** – your generated access key
- **aws_secret_access_key** – your generated secret key

> **Important:** CDSE credentials are displayed **only once** after generation—make sure to store them securely.  
> **Note:** To process **Copernicus Contributing Missions (CCM)** data, you must first request access. You can request it here: [CCM — How to register](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/ccm-how-to-register).


---

## Installation

Follow the steps below to set up **EOMetadataTool** locally:

1. **Clone the repository**

    ```bash
    git clone https://gitlab.cloudferro.com/data-science/eometadatatool.git
    ```

2. **Navigate into the project directory**

    ```bash
    cd eometadatatool
    ```

3. **Configure S3 credentials**

    In the repository, you will find a file named `credentials_example.json`.
    Replace the placeholder values in this file with your own credentials, then **remove the `_example` part from the filename** so that the file is named exactly `credentials.json`.
    The file should have the following structure:

    ```json
    {
      "aws_s3_endpoint": "YOUR_AWS_S3_ENDPOINT",
      "aws_access_key_id": "YOUR_ACCESS_KEY",
      "aws_secret_access_key": "YOUR_SECRET_KEY"
    }
    ```
    - Save the file.
    > **Note:** Remember that whenever you change the credentials file, you need to re-run `nix-shell` to create the updated environment.

4. **Start a nix shell with all required dependencies**

    ```bash
    nix-shell
    ```

    > **About:** `nix-shell` launches a fully reproducible development/runtime environment defined in this repository.
   > Running this command automatically downloads and configures all required system packages, Python libraries, and geospatial tools (e.g., GDAL).
   > This guarantees a consistent environment on any machine, regardless of the host OS configuration.

After entering the nix shell, all necessary commands and tools (including `metadata_extract`) will be available in your environment.

---
## Usage

**EOMetadataTool** can be used directly from the command line. It supports:
- **Single-scene processing** — process one product at a time, with console output and optional error logging.
- **Batch processing** — process multiple products in a single run, either by:
  - Providing multiple local or S3 paths as arguments, or
  - Passing a text file containing one scene path per line. The tool will automatically process all listed scenes.


The tool automatically calculates an efficient distribution of tasks across workers.
For example, with **100 tasks**, **16 requested workers**, and **80 concurrency per worker**, it will use 2 workers to maximize resource utilization.


### Commands

```bash
# Show help and available options
metadata_extract --help

# Process a single local scene
metadata_extract /path/to/scene

# Process a scene directly from the EODATA S3 repository
metadata_extract s3://eodata/Sentinel-2/MSI/L1C/2024/01/16/S2A_MSIL1C_20240116T000741_N0510_R130_T51CVP_20240116T010505.SAFE

# Process scenes listed in a file and save outputs to custom path pattern
metadata_extract --scenes-file scenes.txt --out-pattern "./output/{name}.json"
```


### Command-Line Arguments

| Argument / Flag | Description                                                                                                                                                  |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `scene` | **Positional argument** – one or more scene paths to process. Supports local paths and `s3://` URIs. If not provided, must be specified via `--scenes-file`. |
| `-h, --help` | Display the help message and exit.                                                                                                                           |
| `--scenes-file SCENES_FILE` | Path to a file containing a list of scene paths (one per line). Useful for batch processing.                                                                 |
| `-t, --template TEMPLATE` | Force a specific template renderer. Use `off` to disable templating entirely.                                                                                |
| `-v, --verbose` | Increase verbosity level. Repeat (`-vv`, `-vvv`) for more detailed output.                                                                                   |
| `-f, --force` | Overwrite existing output files without asking.                                                                                                              |
| `--fail-log FAIL_LOG` | Directory to file storing logs of scenes that failed processing. Use `off` to disable logging or `raise` to propagate errors. Default: `fail.log`.        |
| `--num-workers NUM_WORKERS` | Number of CPU workers to use. Defaults to `number_of_threads * 2`.                                                                                           |
| `--concurrency-per-worker CONCURRENCY_PER_WORKER` | Number of concurrent tasks each worker will handle. Default: `100`.                                                                                          |
| `--task-timeout TASK_TIMEOUT` | Timeout (in seconds) for receiving a result from a worker. Default: `180`.                                                                                   |
| `--sequential` | Process scenes one by one (no parallelism). Useful for debugging or profiling.                                                                               |
| `--out-pattern OUT_PATTERN` | Output file naming pattern. Supports placeholders like `{attr}` replaced with scene attributes (e.g., `{Path.name}`).                                        |
| `--ndjson NDJSON` | Enable NDJSON (newline-delimited JSON) mode and set batch size.                                                                                              |
| `--minify` | Minify JSON output if possible (remove whitespace).                                                                                                          |
| `--strict` | Enable strict mode — raise exceptions on processing errors.                                                                                                  |
| `--no-footprint-facility`, `--no-ff` | Disable footprint facility usage.                                                                                                                            |
| `--profile` | Enable application profiling to analyze performance. Works best with `--sequential`.                                                                         |

> **Note (S3 limits)**
> 
> When accessing EODATA via S3 in CDSE, the following limits apply:
> - Max **2000 requests/minute**  
> - Up to **100 active sessions**  
> - Max **4 concurrent connections** (20 MB/s each)  
> - **12 TB monthly transfer**  
> - Token validity: **10 min**, refreshable within **60 min**  
>
> To avoid hitting these limits, tune `--num-workers` and `--concurrency-per-worker`  
> (e.g. keep total concurrency ≤ 4 for S3 access).

### Python API (Embeddable)

The library is **embeddable** in any Python application. You can call the async API directly from your code (scripts, services, notebooks) to extract and model metadata without invoking the CLI.

#### Example script

```python
import asyncio
from pathlib import Path
from pprint import pprint

from eometadatatool.metadata_extract import extract_metadata
from eometadatatool.s3_utils import setup_s3_client

async def main():
    # Local file processing
    local_scenes = [Path('path/to/scene1.SAFE'), Path('path/to/scene2.SAFE')]
    results = await extract_metadata(local_scenes)
    pprint(results)

    # S3 processing (requires S3 client setup and credentials.json)
    async with setup_s3_client():
        s3_scenes = [Path('s3://bucket/path/to/scene.SAFE')]
        s3_results = await extract_metadata(s3_scenes)
        pprint(s3_results)

if __name__ == "__main__":
    asyncio.run(main())
```
---

## Custom Metadata Mapping

In addition to using the prepared CSV templates for mapping metadata from the CDSE repository, **EOMetadataTool** also supports creating **custom metadata mappings** from other data sources.
All existing templates for supported satellite missions are located in the `stac/` folder. Each mission has its own folder containing:
- `mapping/` — CSV files defining how to extract metadata fields.
- `template/` — Python or Jinja template files for structuring the extracted metadata into the desired output format (e.g., STAC-compliant).
- `example/` — sample metadata files in JSON format, showing the expected result structure.
### Creating your own mapping

To create a custom mapping:
1. Create a **new folder** inside `eometadatatool/eometadatatool/stac/` with a unique name for your mission or data source.
2. Inside it, create three subfolders:
   - `mapping/` — for CSV mapping files. Each CSV defines rules (e.g., XPath expressions) for extracting metadata fields from your product files.
   - `template/` — for template files (`.py` or `.j2` Jinja files) to format the extracted metadata into your target structure.
   - `example/` — for example results of your processing.
3. The CSV mapping file should follow this structure (semicolon-separated):

   | Column       | Description |
   |--------------|-------------|
   | `metadata`   | The name of the metadata field to extract. |
   | `file`       | The source file inside the satellite product (e.g., `MTD_MSIL1C.xml`). |
   | `mappings`   | The XPath expression used to locate the value. |
   | `datatype`   | The expected data type (e.g., `DateTimeOffset`, `String`, `Integer`). |

   **Example:**
   ```csv
   metadata;file;mappings;datatype
   beginningDateTime;MTD_MSIL1C.xml;//PRODUCT_START_TIME/text();DateTimeOffset
   endingDateTime;MTD_MSIL1C.xml;//PRODUCT_STOP_TIME/text();DateTimeOffset

#### XPath Extension Functions (Mapping DSL)

EOMetadataTool extends XPath with a small set of **custom functions** you can call directly in the `mappings` column of your CSV.  
They are registered automatically at runtime (see `function_namespace.register_function_namespace()`), so you can use them without any extra imports or prefixes.

These helpers let you transform values on the fly (geometry, dates, string ops, lookups) while keeping your CSVs declarative.

#### Quick reference

| Function | Purpose | Example (CSV `mappings`) |
|----------|---------|---------------------------|
| `WKT(...)` | Convert coordinate lists into WKT (Point/Line/Polygon or Multi\*) | `WKT(//Global_Footprint/EXT_POS_LIST/text())` |
| `geo_pnt2wkt(nodes)` | Build WKT from elements that have `LATITUDE`/`LONGITUDE` children | `geo_pnt2wkt(//*[local-name()='Point'])` |
| `map(value, json)` | Table lookup with `"default"` fallback | `map(//quality/text(), '{"PASSED":"OK","default":"NOK"}')` |
| `date_format(value, fmt?, delta?)` | Parse ISO date, add delta (e.g. `2h30m`), format | `date_format(//GENERATION_TIME/text(), "%Y-%m-%dT%H:%M:%SZ","30m")` |
| `date_diff(start, end, timespec?)` | Midpoint between two datetimes (ISO 8601) | `date_diff(//START_TIME/text(), //STOP_TIME/text())` |
| `uppercase(value)` / `lowercase(value)` | Case transform | `uppercase(//PRODUCT_TYPE/text())` |
| `regex-match(value, pattern, group=1)` | Regex extract (first match) | `regex-match(//PRODUCT_URI/text(), "R(\\d+)", 1)` |
| `join(nodes, sep=", ")` | Join multiple nodes as one string | `join(//Identifier/text(), "; ")` |
| `from_json(value)` | Parse JSON string to a structure (primarily for templates) | `from_json(//SomeJSON/text())` |
| `quote(x)` | Wrap input in a list (rarely needed) | `quote(//field/text())` |


This approach allows you to:
- Process other different satellite and non-satellite products.
- Adapt to different metadata structures.
- Generate outputs in STAC format or any custom format of your choice.


### Creating your own output template

A template in this case is a Python module that defines how metadata from your dataset is transformed into a custom metadata file.
It contains a single asynchronous function, which returns ready structured metadata json:

```python
async def render(attr: dict[str, Any]) -> dict[str, Any]:
    ...
    return await item.generate()
```
In the case of STAC collections, this function::
- Reads attributes (`attr`) extracted from your product’s metadata and file structure.
- Builds a `props` dictionary with STAC properties (datetime, platform, orbit, EO/SAR metadata, etc.).
- Defines an `assets` dictionary with the product’s files, using appropriate asset classes (e.g., `JPEG2000Asset`, `XMLAsset`, `ThumbnailAsset`).
- Instantiates a `STACItem` object, sets geometry, extensions, links, and extra metadata.
- Returns the generated STAC item dictionary.

#### STAC Framework Helpers (Reusable Building Blocks)

As shown in the template script, various ready-to-use classes are employed to keep attributes standardized. All these classes are located in the `stac/framework/` directory and are organized by type, allowing you to build output metadata from modular components. By reusing these helper classes (assets, bands, extensions), you can reduce repetitive code and keep your template concise.  These modules provide common base classes, helper functions, and predefined configurations for assets, bands, and metadata properties, which can also be adjusted for custom usage..

**Overview of key module files:**

- **`stac_item.py`** – Defines the `STACItem` class, representing a complete STAC Item object.
  Responsibilities of this module include:
  - Storing paths, metadata (`ODataInfo`), geometry (WKT), links, and associated assets.
  - Managing which STAC extensions are applied to an item.
  - Generating full STAC-compliant JSON with geometry normalization, bounding boxes, and asset generation.
  - Embedding authentication and storage scheme definitions for Copernicus Data Space Ecosystem (CDSE) and CREODIAS S3.
  - Adding processing metadata (including `eometadatatool` version and processing facility).

**Example:**
  ```python
  item = STACItem(
      path=attr['filepath'],
      odata=odata,  # from get_odata_id(...)
      collection='sentinel-2-l2a',
      identifier=attr['identifier'],
      coordinates=attr['coordinates'],  # WKT
      links=[TraceabilityLink(href=f"{attr['s2msi:productUri']}.zip"), ZipperLink(href=attr['filepath'])],
      assets=assets,  # dict of STACAsset instances
      extensions=(StacExtension.EO, StacExtension.RASTER, StacExtension.PROJECTION),
      extra=props,
  )
  ```

- **`stac_asset.py`** – defines a hierarchy of asset classes (e.g., STACAsset, XMLAsset, JPEG2000Asset, CloudOptimizedGeoTIFFAsset, ThumbnailAsset) used to represent different data products in STAC.
  These classes:
  - Handle paths (local/S3/HTTPS) and metadata like size, checksums.
  - Support alternate download links and authentication requirements.
  - Provide automated filling of missing geospatial metadata (e.g., projection, bounding box) using GDAL.
  - Include specialized subclasses for different formats (XML, NetCDF, JP2, GeoTIFF, etc.).

**Example:**
  ```python
  assets = {
      'product_metadata': XMLAsset(
          path=f"{item_path}/MTD_MSIL2A.xml",
          title="MTD_MSIL2A.xml",
          roles=('metadata',),
          checksum=attr['MTD_MSIL2A:checksum'],
          size=attr['MTD_MSIL2A:size'],
      ),
      'B04_10m': JPEG2000Asset(
          path=f"{item_path}/{attr['asset:B04:10m']}",
          title="Red - 10m",
          roles=('data', 'reflectance', 'gsd:10m'),
          checksum=attr['asset:B04:10m:file:checksum'],
          size=attr['asset:B04:10m:file:size'],
          checksum_fn_code=0x16,
          extra={'bands': generate_bands(S2_Bands, ('B04',))}
      ),
      'thumbnail': ThumbnailAsset(
          path=attr['ql:path'],
          title="Quicklook",
          roles=('thumbnail', 'overview'),
          checksum=attr['ql:checksum'],
          size=attr['ql:size'],
      ),
  }
  ```
- **`stac_bands.py`** – stores predefined metadata for optical, SAR, and atmospheric bands for supported missions and enables creation of other custom band creation.
  Band classes include:
  - Central wavelengths, descriptions, and common names for EO bands.
  - SAR polarizations and frequency details.
  - Band groupings for specific instruments (OLCI, SLSTR, SRAL, SYN, etc.).
  - Utility function `generate_bands()` for filtering and selecting relevant bands for an asset.

**Example:**

```python
# Select all Sentinel-2 bands
all_bands = generate_bands(S2_Bands, None)

# Select just RGB for TCI
tci_bands = generate_bands(S2_Bands, ('B04', 'B03', 'B02'))
```
- **`stac_link.py`**
  - Implements the `STACLink` class used to define relationships between STAC entities.
  - Stores `rel` (relationship type), `href` (URL or path), `type` (media type), and optional `title`.
  - Provides a `generate()` method to return the link as a STAC-compliant dictionary.

**Example:**
```python
links = [
    TraceabilityLink(href=f"{odata.name}.zip"),
    ZipperLink(href=attr['filepath']),
]
```

- **`stac_extension.py`** – Stores a central registry of supported STAC extensions. The `StacExtension` enumeration maps each extension name to its official schema URL, ensuring validation against the correct STAC standard version. If needed, you can update these URLs here to point to a different version of the extension or add new extensions that are not yet included in the existing collections.

**Example:**
```python
extensions = (
    StacExtension.EO,
    StacExtension.RASTER,
    StacExtension.SATELLITE,
    StacExtension.PROJECTION,
)
```

### Custom Template Detection

In the **`clas/template.py`** file, there are rules responsible for detecting the appropriate STAC template based on the product (scene) name.
To support your own custom collection, you need to add a detection rule in this file that recognizes your product by its name or file structure and returns the correct template name.

**Example:**

```python
# Sentinel-2 L2A
if name.startswith('S2') and '_MSIL2A_' in name:
    return 'stac_s2l2a'
```
### Custom Product Type Detection

In the **`clas/`** directory, there is also a file named `product_type.py` which is responsible for determining the **product type** of a given scene.
This value is later used to correctly classify and process your data. To support a custom collection, you need to **add your own condition** inside this file so the program can recognize your product type from the product name or folder structure.

**Example:**
```python
# Custom satellite product
if name.startswith('MYMISSION') and '_L1_' in name:
    return 'MYMISSION_L1'
```



The detected product type is then mapped in a separate product-type registry CSV `mappings/ProductTypes2RuleMapping.csv` to determine which mapping and template to use. To support a custom collection, you also need to add the corresponding entry here with basic mapping rules.

**Example registry format:**
```csv
ProductType;RuleName;ESAProductType
S1_EW_GRDH_1S;S1_L1L2;EW_GRDH_1S
S2_MSI_L1C;S2_MSI;MSI_L1C
S3_OL_2_WFR___;S3_OL;OL_2_WFR___
```
- **ProductType** – value returned from `product_type.py`.
- **RuleName** – internal key linking to a specific mapping CSV and template (corresponding to the mapping file name).
- **ESAProductType** – canonical ESA label (or custom standardized name).

### DLC (Domain Logic & Custom Functions)

The `dlc.py` file contains reusable helper functions and utilities that can be referenced in **templates**. This is the place to define any **custom logic** specific to your data source — for example, functions that compute derived attributes, format metadata values, generate additional links, or perform geometric calculations.

**Example of usage in template:**
```python
odata = await get_odata_id(attr)  # attr has 's2msi:productUri' or 'filename'
average_azimuth = s2_compute_average(attr, 'view:azimuth')
```

After completing these steps, you will be able to run metadata_extract with your own custom product.
