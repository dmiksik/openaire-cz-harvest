The working schema described below is based on the OpenAIRE Graph 10.6 dump downloaded from Manghi, P., et al. OpenAIRE Graph Dataset. 10.6.0, OpenAIRE, 1 Dec. 2025, https://doi.org/10.5281/zenodo.17725827.  
All `dataset_*.tar`, `meta_*.tar`, and `relation_*.tar` archives were unpacked to an S3-mounted filesystem, and the JSON(.gz) parts were ingested into a single DuckDB database file `openaire_10_6.duckdb` (DuckDB v1.1.3) using `read_json_auto()` to create the core tables (`dataset`, `organization`, `datasource`, `relation`).  
On top of this raw snapshot we added several CZ-focused helper tables and exports (stored in this directory) to analyse Czech-affiliated datasets, their persistent identifiers (DOI, handle, …), and the repositories / datasources hosting them.

# OpenAIRE Graph – CZ DuckDB working schema
This document describes the tables currently stored in the DuckDB database  
`openaire_10_6.duckdb`, with a focus on:

- identifying datasets with Czech (CZ) affiliations,
- working with different PID schemes (DOI, handle, …),
- connecting datasets to repositories / datasources,
- computing PID scheme statistics for CZ datasets.

The database is available for download using the link shared by email, its size is **256 GB**; sha256 checksum is available [here](https://s3.cl4.du.cesnet.cz/openaire-10-6-duckdb/openaire_10_6.duckdb.sha256?AWSAccessKeyId=G53582KZZG0YBSMOWTNS&Signature=WKpQe1tCquT25MN9NkJQUulW6oI%3D&Expires=1767979826).  
For info on querying the db directly, see the [how-to](#how-to-query-the-shared-openaire-duckdb-from-s3-read-only) at the bottom of this page.

## 1. Core OpenAIRE Graph tables

### `dataset`

Products/datasets from the OpenAIRE Graph.

- **Row count**: ~86 million (`COUNT(*) ≈ 86 236 354`)
- **Source**: JSON dump `dataset/*.json.gz` from the official OpenAIRE Graph dump.
- **Important columns**:
  - `id` – internal OpenAIRE product ID  
    (e.g. `doi_dedup___::…`, `r3f52792889d::…`, `475c1990cbb2::…`).
  - `type` – product type (for us typically `dataset`).
  - `mainTitle` – dataset title.
  - `publicationDate` – publication date (`DATE`).
  - `publisher` – publisher name (if present).
  - `pids` – array of PIDs:
    ```text
    STRUCT(scheme VARCHAR, "value" VARCHAR)[]
    ```
    where `scheme` can be e.g.:
    - `doi`, `handle`, `uniprot`, `ena`, `pdb`,
    - `mag_id`, `pmid`, `pmc`, `w3id`.
  - `instances` – array describing dataset instances (URLs, access rights, license, …).
  - `originalIds` – original identifiers from source systems.

---

### `organization`

Organizations from OpenAIRE.

- **Row count**: ~448k (`COUNT(*) = 448 161`)
- **Important columns**:
  - `id` – organization ID  
    (e.g. `openorgs____::…`, `pending_org_::…`).
  - `legalShortName` – short name.
  - `legalName` – full legal name.
  - `country` – structure:
    ```text
    STRUCT(code VARCHAR, "label" VARCHAR)
    ```
  - `pids` – array of organization PIDs (e.g. ROR), if any.

---

### `datasource`

Data sources / repositories / CRIS systems registered in OpenAIRE.

- **Row count**: ~157k (`COUNT(*) = 157 392`)
- **Important columns**:
  - `id` – datasource ID  
    (e.g. `openaire____::…`, `re3data_____::…`, `opendoar____::…`, `eurocrisdris::…`).
  - `officialName` – official name of the repository/source.
  - `englishName` – English name (if present).
  - `websiteUrl` – website URL.
  - `type` – structure
    ```text
    STRUCT(scheme VARCHAR, "value" VARCHAR)
    ```
    where `value` can be e.g. `Data Repository`, `Publication Repository`, `Regional CRIS`, …
  - further JSON columns for policies, certifications, PID systems, etc.

---

### `relation`

Directed edges between nodes (products, organizations, datasources, communities, …).

- **Row count**: ~7.38 billion (`COUNT(*) = 7 378 579 759`)
- **Important columns**:
  - `source`, `sourceType` – ID and type of the source node  
    (e.g. `product`, `datasource`, `organization`, `community`, …).
  - `target`, `targetType` – ID and type of the target node.
  - `relType` – JSON object
    ```json
    {"name": "...", "type": "..."}
    ```
    examples:
    - `{"name": "hasAuthorInstitution", "type": "affiliation"}`
    - `{"name": "isHostedBy", "type": "provision"}`
  - `provenance` – information about the origin of the edge  
    (e.g. `"Harvested"`, `"Inferred by OpenAIRE"`).
  - `validated`, `validationDate` – validation metadata (mostly unused in practice).

---

## 2. Helper tables for CZ organizations and PIDs

### `cz_org`

Subset of `organization` containing only organizations located in Czechia.

```sql
CREATE TABLE cz_org AS
SELECT
  id,
  legalShortName,
  legalName,
  country.code  AS country_code,
  country.label AS country_name
FROM organization
WHERE country.code = 'CZ';
````

* **Row count**: 5 007
* **Content**: all organizations with `country.code = 'CZ'`.

---

### `dataset_pids`

Expanded PIDs extracted from `dataset.pids`.
This is the main generic table for all PID-scheme analyses.

```sql
CREATE TABLE dataset_pids AS
SELECT
  d.id        AS dataset_id,
  pid.scheme  AS pid_scheme,
  pid.value   AS pid_value
FROM dataset d,
UNNEST(d.pids) AS t(pid);
```

* **Row count**: 89 962 856
* **Schema**:

  * `dataset_id` – reference to `dataset.id`.
  * `pid_scheme` – e.g. `doi`, `handle`, `uniprot`, `ena`, `pdb`, `mag_id`, `pmid`, `pmc`, `w3id`.
  * `pid_value` – concrete PID value (e.g. `10.1234/abcd`, `10261/360124`, `20.500.14352/118657`).

---

### `cz_dataset_aff`

CZ-affiliated products/datasets based on the OpenAIRE relation `hasAuthorInstitution`.

```sql
CREATE TABLE cz_dataset_aff AS
SELECT DISTINCT
  r.source AS dataset_id,
  r.target AS org_id
FROM relation r
JOIN cz_org  o ON o.id = r.target
JOIN dataset d ON d.id = r.source
WHERE r.sourceType = 'product'
  AND r.targetType = 'organization'
  AND json_extract_string(r.relType, '$.name') = 'hasAuthorInstitution';
```

* **Row count**: 14 799
* **Interpretation**:

  * each row represents one *(dataset, CZ organization)* pair,
  * a single dataset may have multiple CZ affiliations ⇒ multiple rows here.
* **Derived counts**:

  * `COUNT(*) = 14 799` – **“full” view**: the number of all (dataset, CZ organization) pairs,
  * `COUNT(DISTINCT dataset_id) = 10 315` – number of **unique CZ datasets** in the OpenAIRE Graph (deduplicated view).

This **full vs. dedup** distinction is reused in the PID statistics.

---

## 3. Handle-specific tables (CZ + handle + repositories)

These tables belong to the first analysis phase that focused specifically on handle PIDs.
Later tables (sections 4 and 5) generalize to arbitrary PID schemes.

### `dataset_handles`

All datasets (globally) that have a handle PID.

```sql
CREATE TABLE dataset_handles AS
SELECT
  dataset_id,
  pid_value AS handle
FROM dataset_pids
WHERE pid_scheme = 'handle';
```

* **Row count**: 147 627
* **Content**: only rows with `pid_scheme = 'handle'`.

---

### `cz_dataset_handles`

CZ-affiliated products that also have a handle PID.

```sql
CREATE TABLE cz_dataset_handles AS
SELECT DISTINCT
  a.dataset_id,
  h.handle,
  a.org_id
FROM cz_dataset_aff a
JOIN dataset_handles h ON h.dataset_id = a.dataset_id;
```

* **Row count**: 635
* **Content**:

  * `dataset_id` – product/dataset,
  * `handle` – handle PID (e.g. `10261/...`, `20.500....`, or sometimes directly a URL `https://hdl.handle.net/...`),
  * `org_id` – CZ organization to which the dataset is affiliated.

---

### `cz_dataset_ids`

Helper table with the list of datasets (products) that are CZ-affiliated **and** have a handle PID.
*(Historical name – this table is handle-specific; for the generalized version see `cz_dataset_ids_all` in section 4.)*

```sql
CREATE TABLE cz_dataset_ids AS
SELECT DISTINCT dataset_id
FROM cz_dataset_handles;
```

* **Row count**: ≤ 635
* **Usage**: restricts `relation` queries to “CZ + handle” datasets when finding hosting datasources.

---

### `cz_dataset_datasource`

Hosting datasources for CZ-affiliated datasets with handle PIDs.
*(Handle-specific version; for the generalized variant see `cz_dataset_datasource_all` in section 4.)*

```sql
CREATE TABLE cz_dataset_datasource AS
SELECT DISTINCT
  r.source AS dataset_id,
  r.target AS datasource_id
FROM relation r
JOIN cz_dataset_ids z ON z.dataset_id = r.source
WHERE r.sourceType = 'product'
  AND r.targetType = 'datasource'
  AND json_extract_string(r.relType, '$.name') = 'isHostedBy';
```

* **Row count**: 402
* **Content**:

  * `dataset_id` – handle + CZ-affiliated dataset,
  * `datasource_id` – repository/source ID (`datasource.id`) that *hosts* the dataset (`isHostedBy`).

---

### `cz_handles_enriched`

“Full” table: CZ datasets with handle PIDs + CZ organizations + hosting repositories.

```sql
CREATE TABLE cz_handles_enriched AS
SELECT DISTINCT
  h.dataset_id,
  h.handle,
  d.mainTitle,
  d.publicationDate,
  org.legalShortName    AS org_short_name,
  org.legalName         AS org_name,
  org.country_code      AS org_country,
  ds.id                 AS datasource_id,
  ds.officialName       AS datasource_name,
  ds.englishName        AS datasource_eng_name,
  ds.websiteUrl         AS datasource_url,
  ds.type.value         AS datasource_type
FROM cz_dataset_handles      h
JOIN dataset                 d   ON d.id = h.dataset_id
JOIN cz_org                  org ON org.id = h.org_id
LEFT JOIN cz_dataset_datasource cd ON cd.dataset_id = h.dataset_id
LEFT JOIN datasource          ds  ON ds.id = cd.datasource_id;
```

* **Row count**: 1 275
* **Why more than 635 rows?**

  * one dataset can be affiliated with multiple CZ organizations,
  * one dataset can be linked to multiple datasources.
* **Content**:

  * dataset identity + handle (`dataset_id`, `handle`),
  * basic dataset metadata (`mainTitle`, `publicationDate`),
  * CZ institution (`org_short_name`, `org_name`, `org_country`),
  * hosting datasource (`datasource_id`, `datasource_name`, `datasource_eng_name`, `datasource_url`, `datasource_type`).

---

### `cz_handles_enriched_dedup`

Deduplicated version of the above – at most one row per `(dataset_id, handle)`.

```sql
CREATE TABLE cz_handles_enriched_dedup AS
SELECT * EXCLUDE rn
FROM (
  SELECT
    h.*,
    ROW_NUMBER() OVER (
      PARTITION BY h.dataset_id, h.handle
      ORDER BY h.dataset_id
    ) AS rn
  FROM cz_handles_enriched h
)
WHERE rn = 1;
```

* **Row count**: `COUNT(DISTINCT dataset_id, handle)` – i.e. one row per dataset + handle.
* **Schema**: same columns as `cz_handles_enriched`, without the helper `rn`.
* **Usage**:

  * exporting “one row per dataset+handle” CSV,
  * subsequent enrichment (e.g. adding DOI info).

---

### `cz_handles_enriched_dedup_with_doi`

Deduplicated handle-dataset table enriched with whether and which DOIs the dataset has.

It was built via a query of this form:

```sql
CREATE TABLE cz_handles_enriched_dedup_with_doi AS
SELECT
  h.*,
  (
    SELECT string_agg(p.pid_value, ';')
    FROM dataset_pids p
    WHERE p.dataset_id = h.dataset_id
      AND p.pid_scheme = 'doi'
  ) AS doi_list,
  (
    SELECT COUNT(*)
    FROM dataset_pids p
    WHERE p.dataset_id = h.dataset_id
      AND p.pid_scheme = 'doi'
  ) > 0 AS has_doi
FROM cz_handles_enriched_dedup h;
```

* **Additional columns**:

  * `doi_list` – semicolon-separated list of all DOIs for the dataset, or `NULL` if none.
  * `has_doi` – boolean flag (`TRUE`/`FALSE`) indicating presence of at least one DOI.
* **Usage**:

  * quick filtering of handle datasets with / without DOI,
  * analyses like “how many CZ handle datasets also have DOI, and in which repositories”.

---

## 4. General CZ dataset / datasource tables (PID-agnostic)

In the next phase we generalized CZ dataset handling so it’s not tied to handle PIDs only, but works for any PID scheme.

### `cz_dataset_ids_all`

All unique CZ datasets (regardless of which PIDs they have).

```sql
CREATE TABLE cz_dataset_ids_all AS
SELECT DISTINCT dataset_id
FROM cz_dataset_aff;
```

* **Row count**: 10 315
* **Content**: one row per dataset with at least one CZ affiliation.

---

### `cz_dataset_datasource_all`

Hosting datasources for **all** CZ datasets (not just those with handle PIDs).

```sql
CREATE TABLE cz_dataset_datasource_all AS
SELECT DISTINCT
  r.source AS dataset_id,
  r.target AS datasource_id
FROM relation r
JOIN cz_dataset_ids_all z ON z.dataset_id = r.source
WHERE r.sourceType = 'product'
  AND r.targetType = 'datasource'
  AND json_extract_string(r.relType, '$.name') = 'isHostedBy';
```

* **Content**:

  * `dataset_id` – any CZ dataset (same set as `cz_dataset_ids_all`),
  * `datasource_id` – ID of the repository/source (`datasource.id`) that hosts the dataset.

These tables are used as the general basis for PID-agnostic CZ analyses (incl. non-DOI schemes).

---

## 5. PID scheme statistics for CZ datasets

### `cz_pid_scheme_stats`

Summary statistics of PID schemes for CZ datasets.

Built conceptually as follows:

1. Take all `dataset_pids` where `dataset_id` appears in `cz_dataset_aff`
   (i.e. datasets with at least one CZ affiliation).
2. For each PID scheme (`pid_scheme`) compute:

   * how many PID occurrences exist,
   * how many affiliation rows exist,
   * how many unique datasets use the scheme,
   * how many of these also have DOI,
   * the relative shares.

The resulting table contains (among others) these columns:

* `pid_scheme` – e.g. `doi`, `handle`, `mag_id`, `pmid`, `pmc`, `pdb`.
* `n_pid_rows`
  – number of rows in `dataset_pids` for the given scheme and CZ datasets
  (= **number of (dataset, PID) pairs** of that scheme).
* `n_aff_rows_full`
  – number of rows in `cz_dataset_aff` that belong to datasets using this scheme
  (= full view: datasets with multiple CZ institutions contribute multiple rows).
* `n_datasets_with_scheme_dedup`
  – number of **unique CZ datasets** (`dataset_id`) that have at least one PID of this scheme.
* `n_datasets_with_scheme_and_doi_dedup`
  – number of unique CZ datasets that have this scheme **and** at least one DOI PID.
* `share_datasets_of_all_dedup`
  – `n_datasets_with_scheme_dedup` divided by the total number of CZ datasets (10 315).
* `share_aff_rows_of_all_full`
  – `n_aff_rows_full` divided by the total number of rows in `cz_dataset_aff` (14 799).

From this table we export a CSV:

### `cz_pid_scheme_stats_full_vs_dedup.csv`

Export including one derived column:

* `n_datasets_with_non-doi_scheme_only = n_datasets_with_scheme_dedup - n_datasets_with_scheme_and_doi_dedup`

CSV header:

```text
pid_scheme,
n_pid_rows,
n_aff_rows_full,
n_datasets_with_scheme_dedup,
n_datasets_with_scheme_and_doi_dedup,
n_datasets_with_non-doi_scheme_only
```

Current values (from the CSV):

| pid_scheme | n_pid_rows | n_aff_rows_full | n_datasets_with_scheme_dedup | n_datasets_with_scheme_and_doi_dedup | n_datasets_with_non-doi_scheme_only |
| ---------: | ---------: | --------------: | ---------------------------: | -----------------------------------: | ----------------------------------: |
|        doi |     15 892 |          14 707 |                       10 271 |                               10 271 |                                   0 |
|     handle |        223 |             556 |                          197 |                                  179 |                                  18 |
|     mag_id |         46 |              61 |                           46 |                                   46 |                                   0 |
|       pmid |         11 |              25 |                           11 |                                    0 |                                  11 |
|        pmc |          6 |              13 |                            6 |                                    0 |                                   6 |
|        pdb |          5 |               9 |                            5 |                                    5 |                                   0 |

Interpretation:

* **`n_pid_rows`**
  – number of PID occurrences of the scheme on CZ datasets (rows in `dataset_pids`).

* **`n_aff_rows_full`**
  – number of rows in `cz_dataset_aff` (dataset × CZ institution) that belong to datasets using this scheme.

* **`n_datasets_with_scheme_dedup`**
  – number of unique CZ datasets that have at least one PID of this scheme.

* **`n_datasets_with_scheme_and_doi_dedup`**
  – number of unique CZ datasets that have this scheme **and** at least one DOI.

* **`n_datasets_with_non-doi_scheme_only`**
  – number of unique CZ datasets that have this scheme **and do not have any DOI**
  (= “pure non-DOI” datasets with respect to this scheme).

On top of this table, a Markdown summary was generated:

* an introductory summary table (Markdown rendering of `cz_pid_scheme_stats_full_vs_dedup.csv`),
* textual explanation of each column,
* lists of datasets that only have non-DOI PIDs (i.e. `n_datasets_with_non-doi_scheme_only`), grouped by scheme (handle-only, pmid-only, pmc-only), with clickable URLs.

---

## 6. CSV exports for further work

CSV exports are stored in the repository under:

```text
openaire_cz_data/dump/
```

Typically there are:

* **“full” exports**
  – multiple rows per dataset (because of multiple CZ institutions and/or multiple datasources).

* **“dedup” exports**
  – deduplicated records, usually “at most one row per (dataset_id, PID value)”
  or extended with DOI flags.

Examples of key files:

* `cz_handles_enriched_full.csv`
  – full export of CZ datasets with handle PIDs
  (multiple rows per dataset due to multiple CZ institutions / datasources).

* `cz_handles_enriched_dedup_with_doi.csv`
  – deduplicated export of CZ handle datasets
  (“one row per dataset + handle”), enriched with:

  * `doi_list` – list of DOIs,
  * `has_doi` – boolean indicator.

* `cz_pid_scheme_stats_full_vs_dedup.csv`
  – aggregated PID scheme statistics for CZ datasets (see section 5).

* Markdown listing of datasets with only non-DOI PIDs
  – summary table plus lists of concrete datasets grouped by PID scheme.

These files serve as **stable inputs** for downstream tooling
(Python notebooks, R scripts, dashboards, …), so that heavy queries
against the 250+ GiB DuckDB database do not have to be rerun every time.

The folder also contains three CSV exports that combine information about
Czech-affiliated datasets, their institutions, and their authors, using
both **OpenAIRE Graph 10.6.0** and **DataCite** as sources.

All three files work with the same basic concepts:

- **“CZ dataset” (OpenAIRE side)** – a dataset that has at least one
  affiliation in `cz_dataset_aff` (i.e. linked in OpenAIRE to an
  organization with country code `CZ`).
- **Institution** – taken from the OpenAIRE `organization` table via the
  helper table `cz_org_with_ror`; whenever possible we attach a
  **ROR ID** for the institution.
- **Author** – taken either
  - from **DataCite** (`datacite.datacite_creators` +
    `datacite.datacite_creator_affiliations`), where authors are already
    explicitly linked to ROR-based affiliations, or
  - from **OpenAIRE** (`dataset.authors`), where all authors and all
    affiliations are “flattened” and we cannot reliably say which author
    belongs to which institution.
- **PIDs** – collected from the OpenAIRE `dataset_pids` table and
  aggregated per dataset into a single string:
  `scheme:value, scheme:value, …`  
  (e.g. `doi:10.5061/dryad.332dj, handle:123456789/12345, pmid:12345678`),
  with DOIs listed first.

### `cz_datacite_institution_author_datasets.csv`

**Granularity**

One row ≈ one **(institution, author, DOI)** triple coming from
**DataCite**, optionally enriched by the corresponding OpenAIRE dataset.

Only DataCite records that carry at least one **Czech ROR** in their
affiliations are included.

**Columns**

- `institution` – short name of the Czech institution
  (`cz_org.legalShortName`), e.g. `Charles University`, `CRI`, `JČU`.
- `institution_full` – full legal name
  (`cz_org.legalName`).
- `institution_ror` – ROR ID of the institution, if known, e.g.
  `https://ror.org/024d6js02`.
- `dataset_id` – OpenAIRE `dataset.id` if we could match this DOI to an
  OpenAIRE product; otherwise **NULL** (DataCite-only records).
- `doi` – DOI string as given in the DataCite JSON (concept DOI in the
  “concept” input, version DOI in the “full” input, depending on which
  JSONL was loaded).
- `creator_order` – position of the author in the DataCite `creators[]`
  array (1-based).
- `given_name` – DataCite `givenName` (if present).
- `family_name` – DataCite `familyName` (if present).
- `author_name` – simple concatenation `given_name || ' ' || family_name`
  for convenience.
- `orcid` – ORCID iD of the author, if present in DataCite
  (`nameIdentifiers`), otherwise empty.
- `pids` – aggregated list of all PIDs for the matched OpenAIRE dataset,
  or empty if we did not find a corresponding OpenAIRE `dataset_id`
  for this DOI.

**How it is built (high-level)**

1. DataCite JSONL is loaded into `datacite.datacite_dois_raw`.
2. Creator records and their ROR-based affiliations are flattened into
   `datacite.datacite_creators` and
   `datacite.datacite_creator_affiliations`.
3. A mapping `cz_datacite_dataset_map` links (normalised) DOIs from
   DataCite to OpenAIRE `dataset_id` via `dataset_pids`.
4. `cz_org_with_ror` provides the mapping from ROR → Czech institutions.
5. `cz_dataset_pid_list` aggregates all PIDs for each CZ dataset.
6. `cz_datacite_institution_author_datasets` combines all of the above:
   for each (DOI, creator, affiliation ROR) it attaches the matching CZ
   institution, OpenAIRE `dataset_id` (if any), ORCID, and the aggregated
   PID list.

**Typical use**

- “Clean” view of how DataCite itself sees **CZ-related datasets**:
  which authors and which ROR-identified institutions are attached to a
  DOI, with OpenAIRE context added where possible.
- Good starting point if you trust DataCite’s affiliation modelling and
  want an author–institution–DOI matrix that is not influenced by
  OpenAIRE’s more approximate affiliation logic.

---

### `cz_institution_author_datasets.csv`

**Granularity**

One row ≈ one **(institution, author, dataset)** triple **backed by an
OpenAIRE dataset_id**.

This file only contains rows where we *do* know the OpenAIRE dataset
(`dataset_id` is not NULL). It merges:

- DataCite-backed affiliations (where a DOI could be matched to an
  OpenAIRE dataset), and
- OpenAIRE-only datasets (CZ datasets that have no matching DOI in the
  DataCite input), using authors and affiliations directly from the
  OpenAIRE Graph dump.

In other words: this is the “safe core” view if you want to be sure that
every row corresponds to a product present in `dataset` and
`dataset_pids`.

**Columns**

The exact header mirrors the underlying table
`cz_institution_author_datasets`, but conceptually the columns are:

- `institution` – short name of the institution (as above).
- `institution_full` – full legal name.
- `institution_ror` – ROR ID of the institution (if known).
- `dataset_id` – OpenAIRE dataset identifier (always filled in this CSV).
- `doi` – DOI if known:
  - for rows coming from DataCite: DOI from DataCite (matching OpenAIRE);
  - for rows coming only from OpenAIRE: the DOI from `dataset_pids`
    (if any; may be empty if the dataset has only non-DOI PIDs).
- `creator_order` – author order (from DataCite where available, from
  OpenAIRE `authors.rank` otherwise).
- `given_name` / `family_name` / `author_name` – author information;
  for OpenAIRE-only rows `given_name` may be empty and we rely on
  `author_name` and/or `family_name`.
- `orcid` – ORCID if present (either from DataCite or from
  `dataset.authors[].pid` in OpenAIRE).
- `pids` – aggregated PID list for the OpenAIRE dataset:
  `scheme:value, scheme:value, …`  
  (can contain DOI, handle, pmid, pmc, etc.).

Depending on how you exported it, there may or may not be an
`affiliation_source` column; if it is present, values are:

- `datacite` – row is primarily based on DataCite affiliations.
- `openaire` – row is based only on OpenAIRE metadata.

**How it is built (high-level)**

- Start from `cz_datacite_institution_author_datasets` (only rows with a
  non-NULL `dataset_id`).
- Add `cz_openaire_only_institution_author_datasets`, i.e. datasets that:
  - appear in `cz_dataset_aff` (CZ affiliation),
  - have no matching DOI in the DataCite input, and
  - have authors in `dataset.authors`.
- For both parts, attach the aggregated PID list from
  `cz_dataset_pid_list`.

**Typical use**

- “Best effort” **institution–author–dataset list** for CZ datasets,
  restricted to products that actually exist in the OpenAIRE Graph
  database.
- Suitable for:
  - institutional overviews (“which datasets are linked to our ROR, and
    which authors are involved?”),
  - counting datasets per (institution, author),
  - further joining on `dataset_id` to other OpenAIRE tables.

---

### `cz_institution_author_datasets_all.csv`

**Granularity**

One row ≈ one **(institution, author, dataset/DOI)** triple, for *all*
CZ-related datasets we can see in either OpenAIRE or DataCite.

This file is a **superset** of `cz_institution_author_datasets.csv`:

- it includes all rows backed by an OpenAIRE `dataset_id` (same as the
  previous file), **plus**
- **DataCite-only** rows: DOIs that have Czech ROR affiliations in
  DataCite but that we could not match to any product in the OpenAIRE
  dump.

These DataCite-only rows are exactly the ones where:

- `dataset_id` is empty,
- `pids` is empty, and
- `doi` is filled.

That explains why you see some rows with neither DOI-based nor
non-DOI PIDs in the `pids` column: for those DOIs, there is no matching
OpenAIRE product in the version 10.6.0 dump.

**Columns**

Same as in `cz_institution_author_datasets.csv`, typically including:

- `institution`
- `institution_full`
- `institution_ror`
- `dataset_id` (may be NULL for DataCite-only rows)
- `doi`
- `creator_order`
- `given_name`
- `family_name`
- `author_name`
- `orcid`
- `pids` (may be empty if there is no OpenAIRE match)
- `affiliation_source` – explicitly tells you where the row comes from:
  - `datacite` – derived from DataCite creators + ROR affiliations;
    `dataset_id`/`pids` may or may not be present depending on OpenAIRE
    coverage;
  - `openaire` – derived only from OpenAIRE (`dataset`, `dataset_pids`,
    `dataset.authors`, `cz_dataset_aff`, `cz_org_with_ror`).

**How it is built (high-level)**

- Union of:
  - all rows from `cz_datacite_institution_author_datasets`
    (DataCite-backed, including DOIs without any OpenAIRE product), and
  - all rows from `cz_openaire_only_institution_author_datasets`.
- Column `affiliation_source` is used to keep the provenance of the
  affiliation information.

**Typical use**

- “Maximal coverage” view of CZ-related datasets and authors from **both
  DataCite and OpenAIRE**, regardless of whether a given DOI appears in
  the OpenAIRE Graph dump.
- Good for:
  - sanity-checking coverage of OpenAIRE vs DataCite (e.g. which DOIs
    with CZ RORs are **missing** from the OpenAIRE dump),
  - building lists of CZ-related datasets where OpenAIRE coverage is
    incomplete or lagging.


# How to query the shared OpenAIRE DuckDB from S3 (read-only)

## 1. Prerequisites

- DuckDB **CLI** installed (version **1.1.3 or newer**)
  - Check with:
    ```bash
    duckdb --version
    ```
- Internet access to the CESNET S3 endpoint.

You got a **pre-signed URL** to the database file, looking roughly like:

```text
https://s3.cl4.du.cesnet.cz/openaire-10-6-duckdb/openaire_10_6.duckdb?...signature-and-expires...
````

> ⚠️ Treat this URL as sensitive (it contains an access token).
> Do **not** publish it publicly or commit it to Git.

---

## 2. Open DuckDB and attach the remote database

Start DuckDB (without opening any local file):

```bash
duckdb
```

Then, inside the DuckDB prompt, run:

```sql
INSTALL httpfs;
LOAD httpfs;

-- reset S3-related settings (just to be safe)
RESET s3_endpoint;
RESET s3_access_key_id;
RESET s3_secret_access_key;

-- attach the remote database in READ ONLY mode
ATTACH '<PRESIGNED_URL>' AS openaire (READ_ONLY);

-- switch to the attached database
USE openaire;

-- sanity checks
SHOW TABLES;
SELECT COUNT(*) FROM dataset;
SELECT COUNT(*) FROM cz_org;
```

Replace `<PRESIGNED_URL>` with the full pre-signed URL you received.

If `SHOW TABLES;` works and the example `SELECT` returns a number, the connection is fine and you can start running your own queries.

---

## 3. Example queries

A few simple examples:

```sql
-- list CZ organisations
SELECT * FROM cz_org LIMIT 20;

-- see PID scheme stats
SELECT * FROM cz_pid_scheme_stats;

-- show some CZ handle records (deduplicated)
SELECT *
FROM cz_handles_enriched_dedup
LIMIT 20;
```

---

## 4. Notes and recommendations

* The database is ~250 GiB and is accessed over the network.
  For heavy analysis, it may be more efficient to **download the `.duckdb` file once** and work locally.
* The database is attached as **READ_ONLY** – this is intentional, so nobody can accidentally modify the shared snapshot.
* The pre-signed URL may **expire**.
  If you suddenly get `AccessDenied` or similar errors, ask for a fresh URL.

