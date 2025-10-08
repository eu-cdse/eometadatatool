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

Next reviews: S1 SLC => S1 RTC => S3 SR1 SRA BS => S5P L2 NO2

| collection            | item status        | collection status  | next action     | comment |
| --------------------- | ------------------ | ------------------ | --------------- | ------- |
| sentinel-1-grd-cog    | finished           | finished           | -               | |
| sentinel-1-slc        | finished           | finished           | -               | |
| sentinel-1-rtc        | final review       | work-in-progress   | Matthias Mohr   | Waiting for review |
| sentinel-1-mosaic     | finished           | finished           | -               | |
| sentinel-2-l1c        | finished           | finished           | -               | |
| sentinel-2-l2a        | finished           | finished           | -               | |
| sentinel-2-mosaics    | Python conversion  | blocked            | Kamil?          | |
| sentinel-3-ol1-efr    | finished           | finished           | -               | |
| sentinel-3-ol1-err    | finished           | finished           | -               | |
| sentinel-3-ol2-lfr    | finished           | finished           | -               | |
| sentinel-3-ol2-lrr    | finished           | finished           | -               | |
| sentinel-3-ol2-wfr    | finished           | finished           | -               | |
| sentinel-3-ol2-wrr    | finished           | finished           | -               | |
| sentinel-3-sl1-rbt    | work-in-progress   | blocked            | Jacek Chojnacki | |
| sentinel-3-sl2-aod    | finished           | finished           | -               | |
| sentinel-3-sl2-frp    | finished           | finished           | -               | |
| sentinel-3-sl2-lst    | finished           | finished           | -               | |
| sentinel-3-sl2-wst    | finished           | finished           | -               | |
| sentinel-3-sr1-sra    | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr1-sra-a  | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr1-sra-bs | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr2-lan    | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr2-lan-hy | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr2-lan-li | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr2-lan-si | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sr2-wat    | final review       | blocked            | Matthias Mohr   | |
| sentinel-3-sy2-aod    | work-in-progress   | blocked            | Jacek Chojnacki | check scope of proj fields, add nodata value, add data_type if applicable |
| sentinel-3-sy2-syn    | work-in-progress   | blocked            | Jacek Chojnacki | |
| sentinel-3-sy2-v10    | work-in-progress   | blocked            | Jacek Chojnacki | |
| sentinel-3-sy2-vg1    | work-in-progress   | blocked            | Jacek Chojnacki | |
| sentinel-3-sy2-vgp    | work-in-progress   | blocked            | Jacek Chojnacki | |
| sentinel-5p-l1-ra-bd  | finished           | finished           | -               | |
| sentinel-5p-l2-aer-ai | finished           | finished           | -               | |
| sentinel-5p-l2-aer-lh | finished           | finished           | -               | |
| sentinel-5p-l2-ch4    | finished           | finished           | -               | |
| sentinel-5p-l2-cloud  | finished           | finished           | -               | |
| sentinel-5p-l2-co     | finished           | finished           | -               | |
| sentinel-5p-l2-hcho   | finished           | finished           | -               | |
| sentinel-5p-l2-no2    | finished           | finished           | -               | |
| sentinel-5p-l2-np-bd3 | finished           | finished           | -               | |
| sentinel-5p-l2-np-bd6 | finished           | finished           | -               | |
| sentinel-5p-l2-np-bd7 | finished           | finished           | -               | |
| sentinel-5p-l2-o3     | finished           | finished           | -               | |
| sentinel-5p-l2-o3-pr  | finished           | finished           | -               | |
| sentinel-5p-l2-so2    | finished           | finished           | -               | |
| sentinel-5p-l2-o3-tcl | finished           | finished           | -               | |
| landsat-c2-l1-oli-tirs | work-in-progress  | blocked            | ?               | |
| landsat-c2-l1-oli     | work-in-progress   | blocked            | ?               | |
| landsat-c2-l1-tirs    | work-in-progress   | blocked            | ?               | |

## CCM Status

| ccm collection         | item status      | collection status | next action   | comment                                                      |
| ---------------------- | ---------------- | ----------------- | ------------- | ------------------------------------------------------------ |
| ccm/ais                | blocked          | blocked           | Tomasz Furtak | Metadata confusion. Waiting for ESA comment about KOMPSAT satellite|
| ccm/dov                | blocked          | done              | Tomasz Furtak | One product does not work                       |
| ccm/gis                | blocked          | done              | Tomasz Furtak | Attribute published does not show up in browser |
| ccm/hrs                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/nao                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/opt                | blocked          | blocked           | Tomasz Furtak | Plaform ID cofusion                             |
| ccm/phr                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/s14                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/vhi                | blocked          | blocked           | Tomasz Furtak | Plaform ID cofusion                             |
| ccm/wv2                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/wv3                | done             | done              | Tomasz Furtak | Read to be checked                              |
| ccm/cos                | work-in-progress | work-in-progress  | Tomasz Furtak |                                                 |
| ccm/ice                | work-in-progress | work-in-progress  | Tomasz Furtak |                                                 |
| ccm/paz                | work-in-progress | work-in-progress  | Tomasz Furtak |                                                 |
| ccm/rs2                | work-in-progress | work-in-progress  | Tomasz Furtak |                                                 |
| ccm/tsx                | work-in-progress | work-in-progress  | Tomasz Furtak |                                                 |

## Story

The repository stores all the templates used for generating items based on original metadata, defined collections, and examples of generated items. Due to the number of collections and the different developers working on them, it was decided to create a table that allows for quick verification of whether a given collection is ready at the production level (whether it can start batch loading data).

## Status Dictionary

- **finished** - The collection is production-ready; products for the entire history can start being generated.
- **final-review** - The collection is almost production-ready; it's waiting for the final review or it’s a matter of solving a few remaining issues.
- **blocked** - The collection is blocked awaiting action from other teams. The description should include a list of attributes that are blocked and cannot be mapped at the moment, along with reasons provided in table number 3.
- **work-in-progress** - The collection has a developer assigned who has started working on it. This includes metadata mapping and any development related to eometadatatool.
- **unassigned** - Defined in plans, but the collection does not have a developer assigned or the developer has not yet started working on it.
