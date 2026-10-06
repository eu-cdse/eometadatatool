# Utility scripts

## Table of Contents

- [compare_odata.py](#compare-odata)
- [find_unused_mappings.py](#find-unused-mappings)
- [regenerate_examples.py](#regenerate-examples)

## Compare odata
Validates OData generation by fetching upstream STAC metadata from CREODIAS DataHub and comparing it against locally-rendered OData output. Produces unified diff files for each example, canonicalizing both responses (sorted keys, normalized structures) to reduce noise and highlight actual discrepancies.

## Find unused mappings
Identifies unused metadata mapping entries by scanning CSV files in the repository and cross-referencing keys against actual usage in code (including wildcard patterns in f-strings). Supports `--apply` mode to remove dead rows in-place, helping maintain clean mapping tables.

## Regenerate examples
Regenerates item examples. Specify name of the collection to be regenerated:

```bash
python eometadatatool/stac/utils/regenerate_examples.py sentinel-2-l2a
```

Accepts multiple folders separated by white-space. If no parameters is specified, then all examples will be regenerated (Careful: time-intensive!)
