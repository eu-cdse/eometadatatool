# The official repository of CDSE STAC templates

## Table of Contents

- [The official repository of CDSE STAC templates](#the-official-repository-of-cdse-stac-templates)
  - [General rules](#general-rules)
  - [Table of Contents](#table-of-contents)
  - [Regular Missions Status](#regular-missions-status)
  - [CCM Status](#ccm-status)
  - [Story](#story)
  - [Status Dictionary](#status-dictionary)

## General rules

In order to work with implemented tests a collection needs to meet the following conditions:

- Have at least 2 folders named: example(s) and template(s),
- Have at least one example in examples folder in JSON format,
- Have at least one collection in templates folder in JSON format and it's name start with 'collection' prefix,
- Have **exactly** one template in templates folder and it's name start with 'stac' prefix.

## Regular Missions Status

| collection                 | item status | collection status | comment |
| ---------------------------|-------------|-------------------|---------|
| sentinel-1-card-bs         | work-in-progress | work-in-progress | New collection, needs review -- see note below |
| sentinel-1-etad            | finished    | finished          |         |
| sentinel-1-grd-cog         | finished    | finished          |         |
| sentinel-1-mosaic          | finished    | finished          |         |
| sentinel-1-slc             | finished    | finished          |         |
| sentinel-1-slc-wv          | finished    | finished          |         |
| sentinel-1-ocn             | finished    | finished          |         |
| sentinel-1-ocn-wv          | finished    | finished          |         |
| sentinel-2-gri-l1c         | finished    | finished          |         |
| sentinel-2-gri-l1c-gcp     | finished    | finished          |         |
| sentinel-2-l1c             | finished    | finished          |         |
| sentinel-2-l2a             | finished    | finished          |         |
| sentinel-2-mosaics         | finished    | finished          |         |
| sentinel-3-ol1-efr-nrt     | finished    | finished          |         |
| sentinel-3-ol1-efr-ntc     | finished    | finished          |         |
| sentinel-3-ol1-err-nrt     | finished    | finished          |         |
| sentinel-3-ol1-err-ntc     | finished    | finished          |         |
| sentinel-3-ol2-lfr-nrt     | finished    | finished          |         |
| sentinel-3-ol2-lfr-ntc     | finished    | finished          |         |
| sentinel-3-ol2-lrr-nrt     | finished    | finished          |         |
| sentinel-3-ol2-lrr-ntc     | finished    | finished          |         |
| sentinel-3-ol2-wfr-nrt     | finished    | finished          |         |
| sentinel-3-ol2-wfr-ntc     | finished    | finished          |         |
| sentinel-3-ol2-wrr-nrt     | finished    | finished          |         |
| sentinel-3-ol2-wrr-ntc     | finished    | finished          |         |
| sentinel-3-sl1-rbt-nrt     | finished    | finished          |         |
| sentinel-3-sl1-rbt-ntc     | finished    | finished          |         |
| sentinel-3-sl2-aod-nrt     | finished    | finished          |         |
| sentinel-3-sl2-frp-nrt     | finished    | finished          |         |
| sentinel-3-sl2-frp-ntc     | finished    | finished          |         |
| sentinel-3-sl2-lst-nrt     | finished    | finished          |         |
| sentinel-3-sl2-lst-ntc     | finished    | finished          |         |
| sentinel-3-sl2-wst-nrt     | finished    | finished          |         |
| sentinel-3-sl2-wst-ntc     | finished    | finished          |         |
| sentinel-3-sr1-sra-nrt     | finished    | finished          |         |
| sentinel-3-sr1-sra-ntc     | finished    | finished          |         |
| sentinel-3-sr1-sra-stc     | finished    | finished          |         |
| sentinel-3-sr1-sra-a-nrt   | finished    | finished          |         |
| sentinel-3-sr1-sra-a-ntc   | finished    | finished          |         |
| sentinel-3-sr1-sra-a-stc   | finished    | finished          |         |
| sentinel-3-sr2-lan-nrt     | finished    | finished          |         |
| sentinel-3-sr2-lan-ntc     | finished    | finished          |         |
| sentinel-3-sr2-lan-stc     | finished    | finished          |         |
| sentinel-3-sr2-lan-hy-nrt  | finished    | finished          |         |
| sentinel-3-sr2-lan-hy-ntc  | finished    | finished          |         |
| sentinel-3-sr2-lan-hy-stc  | finished    | finished          |         |
| sentinel-3-sr2-lan-li-nrt  | finished    | finished          |         |
| sentinel-3-sr2-lan-li-ntc  | finished    | finished          |         |
| sentinel-3-sr2-lan-li-stc  | finished    | finished          |         |
| sentinel-3-sr2-lan-si-nrt  | finished    | finished          |         |
| sentinel-3-sr2-lan-si-ntc  | finished    | finished          |         |
| sentinel-3-sr2-lan-si-stc  | finished    | finished          |         |
| sentinel-3-sr2-wat-nrt     | finished    | finished          |         |
| sentinel-3-sr2-wat-ntc     | finished    | finished          |         |
| sentinel-3-sr2-wat-stc     | finished    | finished          |         |
| sentinel-3-sy2-aod-ntc     | finished    | finished          |         |
| sentinel-3-sy2-syn-ntc     | finished    | finished          |         |
| sentinel-3-sy2-syn-stc     | finished    | finished          |         |
| sentinel-3-sy2-v10-ntc     | finished    | finished          |         |
| sentinel-3-sy2-v10-stc     | finished    | finished          |         |
| sentinel-3-sy2-vg1-ntc     | finished    | finished          |         |
| sentinel-3-sy2-vg1-stc     | finished    | finished          |         |
| sentinel-3-sy2-vgp-ntc     | finished    | finished          |         |
| sentinel-3-sy2-vgp-stc     | finished    | finished          |         |
| sentinel-5p-l1-ra          | finished    | finished          |         |
| sentinel-5p-l1-ra-nrti     | finished    | finished          |         |
| sentinel-5p-l2-aer-ai      | finished    | finished          |         |
| sentinel-5p-l2-aer-ai-nrti | finished    | finished          |         |
| sentinel-5p-l2-aer-lh      | finished    | finished          |         |
| sentinel-5p-l2-aer-lh-nrti | finished    | finished          |         |
| sentinel-5p-l2-ch4         | finished    | finished          |         |
| sentinel-5p-l2-ch4-nrti    | finished    | finished          |         |
| sentinel-5p-l2-cloud       | finished    | finished          |         |
| sentinel-5p-l2-cloud-nrti  | finished    | finished          |         |
| sentinel-5p-l2-co          | finished    | finished          |         |
| sentinel-5p-l2-co-nrti     | finished    | finished          |         |
| sentinel-5p-l2-hcho        | finished    | finished          |         |
| sentinel-5p-l2-hcho-nrti   | finished    | finished          |         |
| sentinel-5p-l2-no2         | finished    | finished          |         |
| sentinel-5p-l2-no2-nrti    | finished    | finished          |         |
| sentinel-5p-l2-np-bd3      | finished    | finished          |         |
| sentinel-5p-l2-np-bd6      | finished    | finished          |         |
| sentinel-5p-l2-np-bd7      | finished    | finished          |         |
| sentinel-5p-l2-o3          | finished    | finished          |         |
| sentinel-5p-l2-o3-nrti     | finished    | finished          |         |
| sentinel-5p-l2-o3-pr       | finished    | finished          |         |
| sentinel-5p-l2-o3-pr-nrti  | finished    | finished          |         |
| sentinel-5p-l2-o3-tcl      | finished    | finished          |         |
| sentinel-5p-l2-o3-tcl-nrti | finished    | finished          |         |
| sentinel-5p-l2-so2         | finished    | finished          |         |
| sentinel-5p-l2-so2-nrti    | finished    | finished          |         |
| sentinel-6-amr-c-nrt       | finished    | finished          |         |
| sentinel-6-amr-c-ntc       | finished    | finished          |         |
| sentinel-6-amr-c-stc       | finished    | finished          |         |
| sentinel-6-p4-1b-nrt       | finished    | finished          |         |
| sentinel-6-p4-1b-ntc       | finished    | finished          |         |
| sentinel-6-p4-1b-stc       | finished    | finished          |         |
| sentinel-6-p4-2-nrt        | finished    | finished          |         |
| sentinel-6-p4-2-ntc        | finished    | finished          |         |
| sentinel-6-p4-2-stc        | finished    | finished          |         |
| landsat-c2-l1-oil-tirs     | finished    | finished          |         |
| landsat-c2-l1-oil          | finished    | finished          |         |
| landsat-c2-l1-tirs         | finished    | finished          |         |
| landsat-c2-l2-oil-tirs     | finished    | finished          |         |
| landsat-mosaic             | finished    | finished          |         |

## CCM Status

| collection                 | item status        | collection status  | comment |
| ---------------------------|--------------------|--------------------|---------|
| ccm-optical                | finished           | finished           |         |
| ccm-sar                    | finished           | finished           |         |
| copdem-cog-30              | finished           | finished           |         |
| copdem-cog-90              | finished           | finished           |         |
| copdem-insp                | finished           | finished           |         |

## MODIS Status

| collection                 | item status        | collection status  | comment |
| ---------------------------|--------------------|--------------------|---------|
| modis-aqua-myd09a1         | finished           | finished           |         |
| modis-aqua-myd09q1         | finished           | finished           |         |
| modis-aqua-myd10a1         | finished           | finished           |         |
| modis-aqua-myd10a2         | finished           | finished           |         |
| modis-aqua-myd11a1         | finished           | finished           |         |
| modis-aqua-myd11a2         | finished           | finished           |         |
| modis-aqua-myd13a1         | finished           | finished           |         |
| modis-aqua-myd13a2         | finished           | finished           |         |
| modis-aqua-myd13q1         | finished           | finished           |         |
| modis-aqua-myd14a1         | finished           | finished           |         |
| modis-aqua-myd14a2         | finished           | finished           |         |
| modis-aqua-myd15a2h        | finished           | finished           |         |
| modis-aqua-myd16a3gf       | finished           | finished           |         |
| modis-aqua-myd17a2h        | finished           | finished           |         |
| modis-aqua-myd17a2hgf      | finished           | finished           |         |
| modis-aqua-myd17a3hgf      | finished           | finished           |         |
| modis-aqua-myd21a2         | finished           | finished           |         |
| modis-terra-mod09a1        | finished           | finished           |         |
| modis-terra-mod09q1        | finished           | finished           |         |
| modis-terra-mod10a1        | finished           | finished           |         |
| modis-terra-mod10a2        | finished           | finished           |         |
| modis-terra-mod11a1        | finished           | finished           |         |
| modis-terra-mod11a2        | finished           | finished           |         |
| modis-terra-mod13a1        | finished           | finished           |         |
| modis-terra-mod13a2        | finished           | finished           |         |
| modis-terra-mod13q1        | finished           | finished           |         |
| modis-terra-mod14a1        | finished           | finished           |         |
| modis-terra-mod14a2        | finished           | finished           |         |
| modis-terra-mod15a2h       | finished           | finished           |         |
| modis-terra-mod16a2gf      | finished           | finished           |         |
| modis-terra-mod16a3gf      | finished           | finished           |         |
| modis-terra-mod17a2h       | finished           | finished           |         |
| modis-terra-mod17a2hgf     | finished           | finished           |         |
| modis-terra-mod17a3hgf     | finished           | finished           |         |
| modis-terra-mod21a2        | finished           | finished           |         |
| modis-terraaqua-mcd12q1    | finished           | finished           |         |
| modis-terraaqua-mcd15a2h   | finished           | finished           |         |
| modis-terraaqua-mcd15a3h   | finished           | finished           |         |
| modis-terraaqua-mcd43a4    | finished           | finished           |         |
| modis-terraaqua-mcd64a1    | finished           | finished           |         |

## Story

The repository stores all the templates used for generating items based on original metadata, defined collections, and examples of generated items. Due to the number of collections and the different developers working on them, it was decided to create a table that allows for quick verification of whether a given collection is ready at the production level (whether it can start batch loading data).

## Status Dictionary

- **finished** - The collection is production-ready; products for the entire history can start being generated.
- **final-review** - The collection is almost production-ready; it's waiting for the final review or it’s a matter of solving a few remaining issues.
- **blocked** - The collection is blocked awaiting action from other teams. The description should include a list of attributes that are blocked and cannot be mapped at the moment, along with reasons provided in table number 3.
- **work-in-progress** - The collection has a developer assigned who has started working on it. This includes metadata mapping and any development related to eometadatatool.
- **unassigned** - Defined in plans, but the collection does not have a developer assigned or the developer has not yet started working on it.
