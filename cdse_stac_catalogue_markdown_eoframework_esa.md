# Copernicus Data Space Ecosystem (CDSE) STAC catalogue

Created by **Jan Musial**, last modified on **Aug 05, 2025**.

## STAC catalogues

1. Production catalogue: <https://radiantearth.github.io/stac-browser/#/external/catalogue.dataspace.copernicus.eu/stac>
2. Development catalogue: <https://radiantearth.github.io/stac-browser/#/external/pgstac.demo.cloudferro.com>

---

## CLMS attributes to be discussed 2025.07.14

**Columns:** OData attribute · Data type · Remove? · Target STAC extension / field · STAC counterpart · Collection level · Item level · Asset level · Notes · OData ICD definition · STAC definition · CLMS definition · Example (STAC) · Example (OData)

> The rows below are transcribed verbatim from the Confluence table. Line breaks inside cells are preserved with `<br>` for readability where needed.

| OData attribute | Data type | Remove? | Target STAC extension / field | STAC counterpart | Collection level | Item level | Asset level | Notes | OData ICD definition | STAC definition | CLMS definition | Example (STAC) | Example (OData) |
|---|---|:---:|---|---|---|---|---|---|---|---|---|---|---|
| areaOfInterest | StringAttribute | X | region | name | mandatory | optional | na | can be set as a `keyword` at collection level; CLMS specific | A human-readable name of the relevant region. | missing | — | — | global |
| beginningDateTime | DateTimeOffsetAttribute |  | STAC core attribute | start_datetime | na | mandatory | na | beginning of the interval that the data is valid. RFC beginning of interval start or end of second? CLMS specific | The first or start date and time for the resource, in UTC. It is formatted as `date-time` according to RFC 3339, section 5.6. | — | — | 2025-06-21T00:00:00.000000Z | 2025-06-21T00:00:00.000000Z |
| cellID | IntegerAttribute | ? | grid | code | na | optional | na | New grid variants may need to be added to the extension. CLMS specific | CLMS specific<br>Cell identifier describing the respective tile or sample. | — | — | — | 1300000000033 |
| Checksum | StringAttribute |  | file | checksum | na | na | mandatory | Represents the known checksums for the product’s physical data, providing a unique value for supporting download integrity check. At least MD5 checksum is mandatory. | Provides a way to specify file checksums (e.g. BLAKE2, MD5, SHA1, SHA2, SHA3). The hashes are self-identifying hashes as described in the Multihash specification and must be encoded as hexadecimal (base 16) string with lowercase letters. | missing | — | — | — |
| collectionName | StringAttribute | X | — | — | na | na | na | can be set as a `keyword` at collection level; CLMS specific | CLMS specific | — | mandatory `collectionName`<br>**TO BE REMOVED** | — | — |
| component | StringAttribute | X | — | — | na | na | na | can be set as a `keyword` at collection level; CLMS specific | CLMS specific | — | Component to which the dataset belongs | — | bio-geophysical |
| consolidationPeriod | IntegerAttribute |  | product | — | optional | optional | na | CLMS specific | CLMS specific | Consolidation period for the collection where multiple consolidations are produced. | — | — | 6 |
| ContentDate:End | DateTimeOffsetAttribute | yes | STAC core attribute | end_time | na | mandatory | na | nominal end | The last or end date and time for the resource, in UTC. It is formatted as `date-time` according to RFC 3339, section 5.6. | Beginnng date of the content period of the product. For products with consolidations, this will not be the same as the sensing start date but the start date of the nominal 10daily period. | — | 2025-06-30T23:59:59.999999Z | 2025-06-30T23:59:59.999999Z |
| ContentDate:Start | DateTimeOffsetAttribute | yes | STAC core attribute | start_datetime | na | mandatory | na | nominal start | The first or start date and time for the resource, in UTC. It is formatted as `date-time` according to RFC 3339, section 5.6. | Beginnng date of the content period of the product. For products with consolidations, this will not be the same as the sensing start date but the start date of the nominal 10daily period. | — | 2025-06-21T00:00:00.000000Z | 2025-06-21T00:00:00.000000Z |
| ContentLength | IntegerAttribute | yes | file | size | na | na | mandatory | Actual size in bytes (B) of the downloadable product package | The file size, specified in bytes. | missing | — | 2751622412 | 2751622412 |
| ContentType | StringAttribute | yes | STAC core attribute | type | na | na | mandatory | The Mime type of the product of the asset. See the common media types in the best practice doc for commonly used asset types. | Describes the content type of the product. The generic mime-type `application/octet-stream` shall be used as default. User can not filter on this attribute but through the file format attribute. | — | image/tiff; application=geotiff; profile=cloud-optimized | application/netcdf |
| datasetAlias | StringAttribute |  | — | — |  |  |  | can be set as a `keyword` at collection level; CLMS specific | CLMS specific | Provides an alias to group multiple datasets with same product category but with different version numbers. | — | — | wl-lakes_global_vector_daily |
| datasetIdentifier | StringAttribute | yes | STAC core attribute | collection | mandatory | na | na | CLMS specific | The `id` of the STAC Collection this Item references to with the `collection` relation type in the `links` array. | Uniquely identifies the dataset. The dataset is a group of products belonging to the same dataset / collection / parentIdentifier. | — | wl-lakes_global_vector_daily_v2 | wl-lakes_global_vector_daily_v2 |
| datasetShortName | StringAttribute |  | — | — |  |  |  | can be set as a `keyword` at collection level; CLMS specific | CLMS specific | Short name for the dataset. | — | — | lwl |
| datasetVersion | IntegerAttribute | yes | version | version | mandatory | na | na | it should be included in the collection name; CLMS specific | Version of the context this field is used in (e.g. Asset or Collection). | Version of the collection represented as a number. | — | 2 | 2 |
| endingDateTime | DateTimeOffsetAttribute |  | STAC core attribute | end_time | na | mandatory | na | CLMS specific | The last or end date and time for the resource, in UTC. It is formatted as `date-time` according to RFC 3339, section 5.6. | missing | — | 2025-06-30T23:59:59.999999Z | 2025-06-30T23:59:59.999999Z |
| EvictionDate | DateTimeOffsetAttribute | yes | timestamps | expires | na | mandatory | na | Date when the data file will be removed from the Interface Delivery Point. | Date and time the corresponding data (see below) expires (is not valid any longer), in UTC. | Date of eviction, removal of the product from the Odata catalogue. | — | 9999-12-31T23:59:59.999999Z | 9999-12-31T23:59:59.999999Z |
| fileFormat | StringAttribute |  | — | — |  |  |  | it should be included in the collection name; CLMS specific | CLMS specific | Format of the product. | — | — | geojson |
| gridLabel | StringAttribute | yes | STAC core attribute | gsd | mandatory | na | na | Required for all rasters; minimum nominal grid spacing for a collection. CLMS specific. | The nominal Ground Sample Distance for the data, as measured in meters on the ground. | Labels the nominal grid spacing in the format as been used in the datasetIdentifier, including the unit. | — | 300 | 300m |
| Id | StringAttribute |  | — | — |  |  |  | UUID | It is a universally unique identifier (UUID). The Id is a local identifier for the product instance within the Data Access, assigned during the product ingestion. | NA | NA | — | c46db475-d910-431f-8f36-d12bf3a93e7f |
| instrumentShortName | StringAttribute | yes | STAC core attribute | instruments | mandatory | mandatory | na | Can be array of strings. name of the Instrument | An array of all the sensors used in the creation of the data. | — | List of the instruments providing the acquisitions used for producing the product. This is used to search and filter on instrument. If multiple values, use comma seperator without whitespace. | VEGETATION | VEGETATION |
| metricGridSpacing | IntegerAttribute | yes | STAC core attribute | gsd | mandatory | mandatory | na | — | — | — | Refers to the nominal grid spacing of the product, expressed in meters. The purpose of this additional field is to filter on the nominal grid spacing as a number eg. `metricGridSpacing > 300`. | 1000 | 1000 |
| missionShortName | StringAttribute |  | — | — | na | na | na | CLMS specific | CLMS specific | — | List of the platforms providing the acquisitions used for producing the product. (All platforms in uppercase.) If multiple values, use comma seperator without whitespace. | NOT TO BE USED | SPOT4,SPOT5,PROBAV |
| ModificationDate | DateTimeOffsetAttribute | yes | STAC core attribute | updated | na | mandatory | na | modification of metadata in OData/STAC catalogue and not the modification of data/assets itself | Date when the product metadata was last modified. | Date and time the corresponding STAC entity or Asset (see below) was updated last, in UTC. | — | 2025-07-02T10:08:46.236018Z | 2025-07-02T10:08:46.236018Z |
| Name | StringAttribute | yes | STAC core attribute | id | na | mandatory | na | product name unique within a Collection, Data file name | It is important that an Item identifier is unique within a Collection, and that the Collection identifier in turn is unique globally. Items are strongly recommended to have Collections. If an Item does not have a Collection, then the Item identifier should be unique within its root Catalog or root Collection. | Unique name of the product. For netcdf products, the Name is the product file name with `_nc`. For COG products: `_cog`. For vector products in GeoJSON: `_geojson`. | — | c_gls_NDVI300_202506210000_GLOBE_OLCI_V2.0.1_nc | c_gls_NDVI300_202506210000_GLOBE_OLCI_V2.0.1_nc |
| nominalDate | DateTimeOffsetAttribute | yes | STAC core attribute | datetime | na | mandatory | na | — | — | This is likely the acquisition (single camera) or the 'nominal' time for combined assets. All times in STAC metadata should be in UTC. If there's no meaningful single 'nominal' time, it is allowed to use `null` and specify `start_datetime`/`end_datetime`. | The nominal date is the reference date for the data acquisition period covered by the product. This date will be used to extract YYYY/MM/DD in the folder structure. | 2025-06-21T00:00:00.000000Z | 2025-06-21T00:00:00.000000Z |
| Online | StringAttribute |  | — | — | na | na | na | Indication of current online presence. | — | — | Indicates if the product is online or not. | — | TRUE |
| OriginDate | DateTimeOffsetAttribute | yes | STAC core attribute | created | na | mandatory | na | When generated by the CLMS producer. Date and time of the product at the source (e.g., Publication date time on the PRIP). Time is in UTC. | Creation date and time of the corresponding STAC entity or Asset, in UTC. | Date of first creation of the product file. For CLMS data this is the `mtime` attribute from the rclone copyto info. | — | 2025-07-02T09:30:01.282075Z | 2025-07-02T09:30:01.282075Z |
| platformAcronym | StringAttribute | yes | STAC core attribute | constellation | mandatory | mandatory | na | — | The name of a logical collection of one or more platforms... | — | List of the platformAcronyms providing the acquisitions used for producing the product. If multiple values, use comma seperator without whitespace. | Sentinel-2 or multimission | Sentinel-2 |
| platformShortName | StringAttribute | yes | STAC core attribute | platform | mandatory | mandatory | na | name of the Platform | The unique name of the specific platform the instrument is attached to. | — | List of the platformShortNames providing the acquisitions used for producing the product. If multiple values, use comma seperator without whitespace. | Sentinel-2A or multimission | Senitnel-2A |
| processingCenter | StringAttribute | yes | processing | facility | na | mandatory | na | name of the Processing Centre | The name of the facility that produced the data. | — | Processing Center that produces the products. | — | VITO |
| productVersion | StringAttribute | yes | processing | version | na | mandatory | na | CLMS specific | The version of the primary processing software or processing chain that produced the data. | Version of the product represented with a minor 'v' (e.g. `v3.0.1` / `v2.0`). | — | v3.0.1 | v3.0.1 |
| PublicationDate | DateTimeOffsetAttribute | yes | timestamps | published | na | mandatory | na | Publication date and time of the product (time at which the product becomes accessible for retrieval to the client within the DA). | Date and time the corresponding data (see below) was published the first time, in UTC. | — | missing | 2025-07-02T10:08:46.236018Z |
| S3Path | StringAttribute | yes | STAC core attribute | href | na | na | mandatory | S3 path in the CDSE repository | S3 path in the CDSE repository | missing | — | /eodata/CLMS/bio-geophysical/vegetation_indices/ndvi_global_300m_10daily_v2/2025/06/21/c_gls_NDVI300_202506210000_GLOBE_OLCI_V2.0.1_nc | — |
| swiSubParameter | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Soil Water Index (SWI) sub-parameter acronym. | — | — | CI |
| temporalRepeatRate | StringAttribute |  | — | — |  |  |  | can be set as a `keyword` at collection level; CLMS specific | CLMS specific | missing | — | — | 10daily |
| vppSeason | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Vegetation phenology and productivity (VPP) season number. | — | — | S2 |
| vppSubParameter | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Vegetation phenology and productivity (VPP) sub-parameter acronym. | — | — | TPROD |
| wlBasinName | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Hydrological basin or catchment name (full name), in English. | — | — | Mackenzie River |
| wlLakeName | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Name of the lake (full name), in local language wherever possible (a choice might be done if the lake shore several different countries). | — | — | athabasca |
| wlRiverName | StringAttribute |  | — | — |  |  |  | CLMS specific | CLMS specific | Name of the river (full name), in local language wherever possible (a choice might be done if the lake shore several different countries). | — | — | Ya-lu-cang-bu-jiang |

---

## Sentinel-5P attributes to be discussed on 27.05.2024

**Columns:** OData attribute · Data type · Remove? · Target STAC extension / field · STAC counterpart · Description · Example (STAC) · Example (OData)

| OData attribute | Data type | Remove? | Target STAC extension / field | STAC counterpart | Description | Example (STAC) | Example (OData) |
|---|---|:---:|---|---|---|---|---|
| beginningDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) | start_datetime | — | 2018-11-03T23:58:55.121559Z | 2024-05-17T00:23:29.000Z |
| endingDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) | end_datetime | — | 2018-11-03T23:58:55.121559Z | 2024-05-17T00:27:08.000Z |
| instrumentShortName | StringAttribute |  | (core STAC attribute) | instruments | — | tropomi | TROPOMI |
| orbitNumber | IntegerAttribute |  | sat | sat:absolute_orbit | — | 34158 | 34158 |
| parentIdentifier | StringAttribute | X | — | — | — | — | urn:ogc:def:EOP:ESA:SENTINEL.S5P_TROP_L2__NO2___ |
| platformShortName | StringAttribute |  | (core STAC attribute) | constellation | — | sentinel-5p | SENTINEL-5P |
| processingCenter | StringAttribute |  | processing | processing:facility | — | ?pdgs-op | PDGS-OP |
| processingDate | DateTimeOffsetAttribute |  | processing | processing:datetime | — | 2018-11-03T23:58:55.121559Z | 2024-05-17T01:26:59.613000+00:00 |
| processingLevel | StringAttribute |  | processing | processing:level | — | L2 | L2 |
| processingMode | StringAttribute |  | product | product:timeliness; product:timeliness_category | — | `PT3H` | NRT / NRTI |
| processorName | StringAttribute | X | — | — | — | — | TROPNLL2DP |
| processorVersion | StringAttribute | X | — | — | For Sentinel-5P the processing:version should be taken from the netCDF global attribute `processor_version`. | — | 20600 |
| productType | StringAttribute |  | product | product:type | — | L2__NO2___ | L2__NO2___ |

---

## Sentinel-1 attributes to be discussed on 20.05.2024

**Columns:** OData attribute · Data type · Remove? · Target STAC extension / field · STAC counterpart · Description · Example (STAC) · Example (OData)

| OData attribute | Data type | Remove? | Target STAC extension / field | STAC counterpart | Description | Example (STAC) | Example (OData) |
|---|---|:---:|---|---|---|---|---|
| beginningDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) | start_datetime | — | 2018-11-03T23:58:55.121559Z | 2024-05-14T00:06:28.688Z |
| completionTimeFromAscendingNode | DoubleAttribute |  | sat | sat:anx_end_offset | — | 238903.7 | — |
| cycleNumber | IntegerAttribute |  | sat | sat:orbit_cycle | — | 322 | — |
| datatakeID | IntegerAttribute |  | EOPF | — | — | 429004 | — |
| endingDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) | end_datetime | — | 2018-11-03T23:59:55.112875Z | 2024-05-14T00:06:53.687Z |
| instrumentConfigurationID | IntegerAttribute |  | EOPF | — | — | 7 | — |
| instrumentShortName | StringAttribute |  | (core STAC attribute) | instruments | — | sar | SAR |
| operationalMode | StringAttribute |  | sar | sar:instrument_mode | — | IW | IW |
| orbitDirection | StringAttribute |  | sat | sat:orbit_state | — | descending | ASCENDING |
| orbitNumber | IntegerAttribute |  | sat | sat:absolute_orbit | — | 42767 | 53860 |
| origin | StringAttribute |  | processing | processing:facility | — | production service-serco | ESA |
| platformSerialIdentifier | StringAttribute |  | (core STAC attribute) | platform | — | sentinel-1a | A |
| platformShortName | StringAttribute |  | (core STAC attribute) | constellation | — | sentinel-1 | SENTINEL-1 |
| polarisationChannels | StringAttribute |  | sar | sar:polarizations | — | `[VV,VH]` | `VV&VH` |
| processingCenter | StringAttribute |  | processing | processing:facility | — | production service-serco | Production Service-SERCO |
| processingDate | DateTimeOffsetAttribute |  | processing | processing:datetime | — | 2024-05-14T08:04:12.593998+00:00 | — |
| processingLevel | StringAttribute |  | processing | processing:level | — | L1 | LEVEL1 |
| processorName | StringAttribute | X | — | — | to be dropped | — | Sentinel-1 IPF |
| processorVersion | StringAttribute | X | — | — | — | 3.71 | — |
| productType | StringAttribute |  | product | product:type | — | IW_GRDH_1S | IW_GRDH_1S |
| sar:product_type | — |  | sar | sar:product_type | **to be moved to** `product:type` (PR) | GRD | — |
| relativeOrbitNumber | IntegerAttribute |  | sat | sat:relative_orbit | — | 63 | — |
| segmentStartTime | DateTimeOffsetAttribute | X | — | — | — | 2024-05-14T00:05:09.988000+00:00 | — |
| sliceNumber | IntegerAttribute | X | — | — | — | 4 | — |
| sliceProductFlag | BooleanAttribute | X | — | — | — | false | — |
| startTimeFromAscendingNode | DoubleAttribute |  | sat | sat:anx_start_offset | milliseconds from ANX crossing | 213904.7 | — |
| swathIdentifier | StringAttribute | X | — | — | — | IW | — |
| timeliness | StringAttribute |  | product | product:timeliness; product:timeliness_category | — | `PT24H` | Fast-24H / Fast-24h |
| totalSlices | IntegerAttribute | X | — | — | — | 20 | — |

**Additional attributes for bursts (example to be added to STAC):**

- `linesPerBurst`: 1493
- `samplesPerBurst`: 21673
- `subswath`: "IW1" (should be string) → `sar:subswaths_id`
- `polarization`: `vh` → `sar:polarizations`
- `start line`: 1493
- `azimuthTime`: 2024-05-10T00:40:19.788314 (→ `start_datetime` / `datetime`)
- `sensingTime`: 2024-05-10T00:40:19.788314 (→ `start_datetime` / `datetime`)
- `byteOffset`: 129538967
- `burstId_relative`: 8690 (should be string; used to be called `frame_id`) → `sar:relative_burst`
- `burstId_absolute`: 115560765
- `burstID_internal`: 2

---

## Sentinel-3 attributes to be discussed on 13.05.2024

| OData attribute | Data type | Remove? | Target STAC extension / field | STAC counterpart | Description | Example (STAC) | Example (OData) |
|---|---|:---:|---|---|---|---|---|
| baselineCollection | StringAttribute | X | processing | processing:version | reflected in the processing:version | OL__L1_.003.03.02 | 003 |
| beginningDateTime | DateTimeOffset |  | (core STAC attribute) | start_datetime | — | 2023-07-10T00:47:16.702921Z | 2024-05-04T00:02:03.199Z |
| cloudCover | DoubleAttribute |  | eo | eo:cloud_cover | — | 28 | 28 |
| coastalCover | DoubleAttribute | X | — | — | — | 1 | 0.009 |
| cycleNumber | IntegerAttribute |  | sat | sat:orbit_cycle | The orbital cycle is 27 days (14+7/27 orbits per day, 385 orbits per cycle). The orbit cycle is the time taken for the satellite to pass over the same geographical point on the ground. | 112 | — |
| endingDateTime | DateTimeOffset |  | (core STAC attribute) | end_datetime | — | 2023-07-10T00:47:16.702921Z | 2024-05-04T00:05:03.199Z |
| freshInlandWaterCover | DoubleAttribute | X | s3 | s3:fresh_inland_water | — | 0 | 0 |
| instrumentShortName | StringAttribute |  | (core STAC attribute) | instruments | — | olci | OLCI |
| landCover | DoubleAttribute |  | s3 | s3:land | — | 2 | 2 |
| operationalMode | StringAttribute? |  | — | — | To be harmonized across missions | Earth Observation | — |
| orbitDirection | StringAttribute |  | sat | sat:orbit_state | — | descending | DESCENDING |
| orbitNumber | IntegerAttribute |  | sat | sat:absolute_orbit | — | 42767 | 42767 |
| platformSerialIdentifier | StringAttribute |  | (core STAC attribute) | platform | — | sentinel-3a | A |
| platformShortName | StringAttribute |  | (core STAC attribute) | constellation | — | sentinel-3 | SENTINEL-3 |
| processingDate | DateTimeOffset |  | processing | processing:datetime | — | 2023-07-10T00:47:16.702921Z | 2024-05-04T02:11:42+00:00 |
| processingLevel | StringAttribute |  | processing | processing:level | — | L2 | 2 |
| processorName | StringAttribute | X | — | — | To be dropped and discussed with ESA experts. | PUG | PUG |
| processorVersion | StringAttribute | X | — | — | `<sentinel3:processingBaseline>PB_ID.xxx.yy.zz</sentinel3:processingBaseline>` from SAFE does not exist in Odata. Mapping via processing:version. | 03.50 | — |
| productType | StringAttribute |  | product | product:type | — | OL_2_LFR___ | OL_2_LFR___ |
| relativeOrbitNumber | IntegerAttribute |  | sat | sat:relative_orbit | — | 59 | 59 |
| salineWaterCover | DoubleAttribute | X | s3 | s3:saline_water | — | 44 | 2 |
| tidalRegionCover | DoubleAttribute | X | s3 | s3:tidal_region | — | 2 | 0 |
| timeliness | StringAttribute |  | product | product:timeliness; product:timeliness_category | — | `PT3H` | NR / NR |

---

## Sentinel-2 attributes to be discussed on 06.05.2024

### Mappings not directly defined in the Sentinel extensions

| OData attribute | Data type | Remove? | Target STAC extension / field | Queryable | STAC counterpart | Asset level | Description | Example (STAC) | Example (OData) |
|---|---|:---:|---|---|---|---|---|---|---|
| mediaContentType | StringAttribute | X | — | — | — | — | — | — | application/octet-stream |
| Id | StringAttribute | X | — | — | Odata internal id | — | — | — | 3e3b9d1a-18d5-43b8-83d8-564587ec3070 |
| Name | StringAttribute |  | (core STAC attribute) | X | `s2:product_uri` (to be removed) | — | product name. STAC `id` is without `.SAFE` | S2A_MSIL2A_20240308T100841_N0510_R022_T33UVR_20240308T143352 | S2B_MSIL2A_20240419T001429_N0510_R116_T56NNG_20240419T013152.SAFE |
| ContentType | StringAttribute |  | (core STAC attribute) |  | type | — | differs between Odata and STAC | image/jp2 | application/octet-stream |
| ContentLength | IntegerAttribute |  | file |  | file:size | — | in bytes | 720970508 | 720970508 |
| OriginDate | DateTimeOffsetAttribute |  | (core STAC attribute) | X | — | — | time of the publication at PRIP | 2024-03-08T14:33:52.000000Z | 2024-04-19T02:13:20.000Z |
| PublicationDate | DateTimeOffsetAttribute |  | (core STAC attribute) | X | published | — | — | 2024-03-08T14:33:52.000000Z | 2024-04-19T02:20:17.555Z |
| ModificationDate | DateTimeOffsetAttribute |  | (core STAC attribute) | X | updated | — | — | 2024-03-08T14:33:52.000000Z | 2024-04-19T02:21:14.300Z |
| Checksum | Checksum |  | file |  | file:checksum | — | Blake3/MD5 in Odata vs Multihash in STAC | — | — |
| ContentDate.Start | DateTimeOffsetAttribute |  | (core STAC attribute) |  |  | X | `datetime` / `start_datetime` | 2024-04-19T00:14:29.024Z | — |
| ContentDate.End | DateTimeOffsetAttribute |  | (core STAC attribute) | X | end_datetime | — | — | — | 2024-04-19T00:14:29.024Z |
| GeoFootprint | — | X | (core STAC attribute) | X | geometry | X | (example polygon) | "GeoFootprint":{"type":"Polygon","coordinates":[[[153.9866661847601,0.945453049017732],[153.9866661847601,0.945453049017732]]]} | — |
| origin | StringAttribute |  | processing |  | processing:facility | — | from manifest or EUMETSAT | — | — |
| cloudCover | DoubleAttribute |  | eo | X | eo:cloud_cover | — | — | 14.583966 | — |
| orbitNumber | IntegerAttribute |  | sat |  | sat:absolute_orbit | — | — | 37179 | — |
| sourceProduct | StringAttribute | X | — | — | — | — | — | S2B_OPER_MSI_L2A_TL_2BPS_20240419T013152_A037179_T56NNG_N05.10 | S2B_OPER_MSI_L2A_DS_2BPS_20240419T013152_S20240419T001424_N05.10 |
| processingLevel | StringAttribute |  | processing |  | processing:level | — | — | L2 | S2MSI2A |
| platformShortName | StringAttribute |  | (core STAC attribute) |  | constellation | — | — | sentinel-2 | SENTINEL-2 |
| instrumentShortName | StringAttribute |  | (core STAC attribute) |  | instruments | — | — | msi | MSI |
| relativeOrbitNumber | IntegerAttribute |  | sat | X | sat:relative_orbit | — | — | 22 | 116 |
| sourceProductOriginDate | StringAttribute | X | — | — | — | — | — | 2024-04-19T02:13:20Z | 2024-04-19T01:32:14Z |
| platformSerialIdentifier | StringAttribute |  | (core STAC attribute) |  | platform | — | — | sentinel-2a | A |
| beginningDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) |  | start_datetime / datetime | — | — | 2024-03-08T14:33:52.000000Z | 2024-04-19T00:14:29.024Z |
| endingDateTime | DateTimeOffsetAttribute |  | (core STAC attribute) |  | end_datetime | — | — | 2024-03-08T14:33:52.000000Z | 2024-04-19T00:14:29.024Z |
| granuleIdentifier | StringAttribute | X | None | — | `s2:granule_id` (removed) | — | — | S2A_OPER_MSI_L2A_TL_2APS_20240308T143352_A045493_T33UVR_N05.10 | S2A_OPER_MSI_L2A_TL_2APS_20240308T143352_A045493_T33UVR_N05.10 |

### Sentinel-2 STAC extension attributes to be discussed (not all present in OData)

- `s2:generation_time` (also in s1)
- `s2:datatake_id` (also in s1)
- `s2:product_type` (also in s1, s3, s5)
- `s2:tile_id`
- `s2:product_uri`
- `s2:datastrip_id`
- `s2:datatake_type`
- `s2:processing_baseline`
- `s2:reflectance_conversion_factor`

See the table above for details.

---

## STAC Sentinel extensions

A priority should be to update the STAC Sentinel extensions to be less extensive at least. The plan is to find spaces in the general STAC community for these fields. As a first step, we need to identify which fields are actually relevant to the general public.

### General fields

For descriptions of the fields, please refer to the Sentinel extensions or the stactools-package implementations.

Idea is to keep a small variant of the Sentinel extensions as best practices, mostly using other extensions. EOPF is for "private" fields that externals are not interested in.

**Columns:** Field name · Data Type · Relevant to general public? · Potential future extension or field · Comments

#### Multi‑mission

| Field name | Data Type | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|---|
| s1:processing_datetime / s2:generation_time | date-time | Yes | processing:datetime (PR)<br>OData: processingDate | S2 Example: 2024-04-19T01:31:52+00:00 (in STAC Z instead of +00:00) |
| s1:datatake_id / s2:datatake_id | string | Yes | to be included in the CDSE STAC and added to eopf extension<br>OData: productGroupId | S2 Example: GS2A_20240308T100841_045493_N05.10 |
| s2:product_type / s3:product_type / s5p:product_type | string | No? | product:type | potentially restricted in S2 extension; what's the difference between name and type? Can it be just one property, e.g. the name? S2 example: S2MSI2A |
| s3:product_name / s5p:product_name | string | Yes? | — | — |
| s1:product_timeliness / s3:processing_timeliness | string | Yes? | product:timeliness | potentially restricted in S2 extension; Can we find a common set of values for this? e.g. ISO 8601 Durations? |

#### Sentinel‑1

| Field name | Data Type | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|---|
| s1:instrument_configuration_ID | string | No? | — | — |
| s1:orbit_source | string | No? | — | — |
| s1:product_identifier | string? | — | externalIds? | — |
| s1:resolution | string | No? | — | — |
| s1:slice_number | string | No | — | — |
| s1:total_slices | string | No | — | — |

#### Sentinel‑2

| Field name | Data Type | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|---|
| s2:tile_id | string | Yes? | grid:code (queryable) and mgrs:* (not queryable) | mgrs extension requires 3 fields (56, NN, G); grid:code is one field (MGRS-56NNG). OData: tileId (56NNG). |
| s2:product_uri | string | NO | — | To be removed. Might be needed in the S2 extension by some other users. |
| s2:datastrip_id | string | Yes? | EOPF | OData field: `datastripId` (e.g. `S2A_OPER_MSI_L2A_DS_2APS_20240308T143352_S20240308T101546_N05.10`). |
| s2:datatake_type | string | ON HOLD | EOPF | similar to `instrument_mode` in SAR.<br>OData: `operationalMode` (e.g. `INS-NOBS`). |
| s2:processing_baseline | string | Yes | processing:version (PR) | OData `processorVersion` example: 5.1; STAC example: 05.10. |
| s2:reflectance_conversion_factor | number | To be removed | — | Example: 1.01707999697991 |

#### Sentinel‑3

| Field name | Data Type | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|---|
| s3:gsd | various | No? | to be dropped or used across all missions | `gsd` is STAC core attribute |
| s3:lrm_mode | number | Yes? | altm:instrument_type | — |
| s3:sar_mode | number | Yes? | altm:instrument_mode | — |
| (Asset-level) s3:spatial_resolution | [number]? | — | raster:spatial_resolution (single value?) | — |
| (Asset-level) s3:altimetry_bands | [Altimetry Band Object]? | — | bands (STAC core in 1.1) | — |

#### Sentinel‑5

| Field name | Data Type | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|---|
| s5p:processing_mode | string? | — | — | — |
| s5p:collection_identifier | string? | — | — | — |
| s5p:spatial_resolution | [number]? | — | raster:spatial_resolution (single value?) | — |

**Sentinel‑5P container objects** (proposed to be flattened into top‑level properties; potential new extension: *None*)

- `s5p:aer_ai` (Aer Ai Object)
- `s5p:aer_lh` (Aer Lh Object)
- `s5p:ch4` (CH4 Object)
- `s5p:cloud` (Cloud Object)
- `s5p:co` (CO Object)
- `s5p:hcho` (HCHO Object)
- `s5p:no2` (NO2 Object)
- `s5p:npbd3` (NPBD Object)
- `s5p:npbd6` (NPBD Object)
- `s5p:npbd7` (NPBD Object)
- `s5p:o3` (O2 Object)
- `s5p:o3_tcl` (O3 TCL Object)
- `s5p:so2` (SO2 Object)

**Sentinel‑5P container object fields** (appear in at least one container object)

- `input_band` (string / [string]) — No
- `irradiance_accompanied` (string) — No?
- `geolocation_grid_from_band` (integer) — No?
- `cloud_mode` (string) — No?
- `shape_ccd` ([integer]) — No?
- `shape_csa` ([integer]) — No?
- `stratosphere_start_datetime` (string?)
- `stratosphere_end_datetime` (string?)
- `troposphere_start_datetime` (string?)
- `troposphere_end_datetime` (string?)
- `input_orbits` ([integer]) — No?
- `input_files` ([string]) — No
- `analysed_s5p_band` (integer) — No?
- `VIIRS_band` ([integer]) — No?
- `number_of_scaled_fov` (integer) — No?

---

## Percentages

**Columns:** Field name · Relevant to general public? · Potential future extension or field · Comments

| Field name | Relevant to general public? | Potential future extension or field | Comments |
|---|---|---|---|
| **General and Other** ||||
| s3:land? | — | — | — |
| s2:unclassified_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| **Clouds** ||||
| s2:cloud_shadow_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| s2:high_proba_clouds_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| s2:medium_proba_clouds_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| s2:thin_cirrus_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| **Water and Coastal** ||||
| s2:water_percentage | Yes, queryable | new: eo:water_cover ? + classification:classes[*].percentage | — |
| s3:closed_sea? | — | — | — |
| s3:fresh_inland_water? | — | — | — |
| s3:open_ocean? | — | — | — |
| s3:saline_water? | — | — | — |
| s3:tidal_region? | — | — | — |
| s3:coastal? | — | — | — |
| s3:continental_ice? | — | — | — |
| **Unusable** ||||
| s2:nodata_pixel_percentage | Yes, queryable | new: raster:nodata_percentage ? + classification:classes[*].percentage | — |
| s3:bright? | — | — | — |
| s3:dubious_samples? | — | — | — |
| s3:duplicated? | — | — | — |
| s3:invalid? | — | — | — |
| s3:out_of_range? | — | — | — |
| s2:dark_features_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| s3:saturated | — | — | — |
| s2:saturated_defective_pixel_percentage | Yes, not queryable | classification:classes[*].percentage | — |
| **Vegetation** ||||
| s2:vegetation_percentage | Yes, queryable? | new: eo:vegetation_cover ? + classification:classes[*].percentage | — |
| s2:not_vegetated_percentage | Yes, not queryable | classification:classes[*].percentage | — |

> Depending on the asset structure, some percentages may be provided as classification percentages as proposed in <https://github.com/stac-extensions/classification/pull/49>.

---

## Deprecated

For completeness, the following fields did exist in the past and are already deprecated in favor of existing STAC fields.

| Field name | Data Type | New field name |
|---|---|---|
| s2:granule_id | string | Removed |
| s2:mgrs_tile | string | mgrs:* |
| s2:mean_solar_zenith | number | view:sun_azimuth |
| s2:mean_solar_azimuth | number | view:sun_elevation |
| s2:snow_ice_percentage | — | — |
| s3:snow_or_ice | number | eo:snow_cover |
| s1:shape | [integer] | proj:shape |
| s1:processing_level | string | processing:level |
| s5p:shape | [integer] | proj:shape |
| s3:shape (in assets) | [integer] | proj:shape |

---

## CDSE querables attributes for Sentinel‑2 L1C

![CDSE querables attributes for Sentinel-2 L1C](image-2024-3-25_14-54-56.png "Referenced from the Confluence page attachments")

---

## CDSE STAC development roadmap

0. Simplify the geofootprint which is the largest attribute in the STAC response and slows down spatial querying (especially relevant for S‑3 and S5P) ← to be provided by the Bureau d'Etude
1. Disable the overview displaying on items/assets level for selected collections e.g. Senitnel‑3 where overviews generated in satellite projection is not displayed correctly.
2. **[Done at the collection level]** Implement the CEOS‑ARD extension for Level‑2 and Level‑3 products <https://github.com/stac-extensions/ceos-ard> (STAC item example <https://github.com/stac-extensions/ceos-ard/blob/main/examples/optical-sr/item.json>). First Sentinel‑2 L2A, then Sentinel‑3 and Sentinel‑5P products. There is no CEOS ARD for radar data yet. Currently it is only for CEOS ARD PFSes (surface reflectance and temperature, and aquatic reflectance).
3. Populate the development catalogue with the Sentinel‑2 L1C and L2A products and make the online version of the catalogue publicly available for testing
4. ~~Add new collections based on the on the stac-tools for Sentinel‑1 (<https://github.com/stactools-packages/sentinel1>), Sentinel‑3 (<https://github.com/stactools-packages/sentinel3>), Sentinel‑5P (<https://github.com/stactools-packages/sentinel5p>). These collections will conform to the new Sentinel extensions: <https://github.com/stac-extensions/sentinel-1> , <https://github.com/stac-extensions/sentinel-3> , <https://github.com/stac-extensions/sentinel-5p>.~~
5. Update ASAP current "more generic" extensions: EO, SAR, etc. Add new Sentinel collections excluding the Sentinel specific extensions.
6. **[In progress]** Migrate some generic attributes from platform specific extension to more general extensions such as `eo` and `sar`. The rest of mission specific attributes (red crosses) should be maintained in the mission specific extensions not in the EOPF extension: <https://github.com/CS-SI/eopf-stac-extension>
7. Add to STAC functionality of online/offline products. Add on demand product generation (url‑s)

---

## Missing STAC API functionalities to be potentially implemented in new STAC extensions

- Hiding entire extensions in the Fields API (<https://github.com/stac-api-extensions/fields>) — could mimic the OData `$expand` option for advanced, ESA internal extensions.
- Hiding items and assets within a Collection by an AOI
- User levels and permissions to filter the JSON response for general & expert CDSE users.

---

## Modification of current STAC extensions

- Add `processing:version` and `processing:datetime`: <https://github.com/stac-extensions/processing/pull/32>
- Deprecate `s1:processing_datetime` in favor of `processing:datetime`: <https://github.com/stac-extensions/sentinel-1/pull/1>
- Deprecate baseline and generation time: <https://github.com/stac-extensions/sentinel-2/pull/14>
- Deprecate snow/ice cover: <https://github.com/stac-extensions/sentinel-2/pull/13>

---

## Various issues related to population of the STAC catalogue

1. **NaN values in the Sentinel‑2 viewing geometry:** <https://esa-cams.atlassian.net/browse/GSANOM-15086>

   **Coordination desk reply:**

   This product is absolutely normal with respect to the current IPF implementation. It is really small as only few pixels from the datastrip intersect this tile as you can see in the CDSE and QGIS screenshots attached (the rainbow effect visible for the TCI displayed in QGIS is normal, and due to the fact that the different spectral bands do not share exactly the same footprint).

   A consequence of this very limited intersection between the tile footprint and the datastrip footprint is that we get only NaN viewing incidence values for several bands in the tile metadata, resulting in NaN mean viewing incidence values for these bands. This is because the grid on which the viewing incidence values are computed is very coarse (5 km × 5 km).

   Then this behaviour could happen sometimes for this kind of products (with limited intersection between the tile and the datastrip), and did happen before.

---

**Source:** Copernicus Data Space Ecosystem (CDSE) STAC catalogue — Confluence page at <https://eoframework.esa.int/display/CDSE/Copernicus+Data+Space+Ecosystem+%28CDSE%29+STAC+catalogue>

