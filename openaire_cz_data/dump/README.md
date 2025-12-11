# OpenAIRE Graph – CZ DuckDB working schema

Tento dokument shrnuje, jaké tabulky jsou aktuálně v DuckDB databázi `openaire_10_6.duckdb` a k čemu slouží, se zaměřením na identifikaci datasetů s handle PIDy a CZ afiliací.

## 1. Základní tabulky z OpenAIRE Graphu

### `dataset`

Produkty/datasety z OpenAIRE Graphu.

- **Počet řádků**: ~86 mil.
- **Zdroje dat**: JSON dump `dataset/*.json.gz` z oficiálního OpenAIRE Graph dumpu.
- **Důležité sloupce**:
  - `id` – interní OpenAIRE ID produktu (např. `doi_dedup___::...`, `r3f52792889d::...`).
  - `type` – typ produktu (pro nás typicky `dataset`).
  - `mainTitle` – název datasetu.
  - `publicationDate` – datum publikace (typ `DATE`).
  - `publisher` – jméno vydavatele (pokud je).
  - `pids` – pole PIDů: `STRUCT(scheme VARCHAR, "value" VARCHAR)[]`.
    - Schémata: `doi`, `handle`, `uniprot`, `ena`, `pdb`, `mag_id`, `pmid`, `pmc`, `w3id`.
  - `instances` – pole instancí datasetu (URL, přístupová práva, licence apod.).
  - `originalIds` – původní identifikátory z harvestovaných zdrojů.

---

### `organization`

Organizace z OpenAIRE.

- **Počet řádků**: ~448 tis.
- **Důležité sloupce**:
  - `id` – ID organizace (např. `openorgs____::...`, `pending_org_::...`).
  - `legalShortName` – zkrácený název.
  - `legalName` – plný název.
  - `country` – struktura `STRUCT(code VARCHAR, "label" VARCHAR)`.
  - `pids` – případné PIDy organizace (např. ROR).

---

### `datasource`

Zdroje / repozitáře / CRISy evidované v OpenAIRE.

- **Počet řádků**: ~157 tis.
- **Důležité sloupce**:
  - `id` – ID datasource (např. `openaire____::...`, `re3data_____::...`, `opendoar____::...`, `eurocrisdris::...`).
  - `officialName` – oficiální název repozitáře/zdroje.
  - `englishName` – anglický název (pokud je).
  - `websiteUrl` – webová adresa zdroje.
  - `type` – struktura `STRUCT(scheme VARCHAR, "value" VARCHAR)` – např. `Data Repository`, `Publication Repository`, `Regional CRIS` apod.
  - další JSON sloupce pro politika, certifikace, PID systémy atd.

---

### `relation`

Orientované hrany grafu mezi uzly (produkty, organizace, datasourcy, komunity, …).

- **Počet řádků**: ~7,38 miliardy.
- **Důležité sloupce**:
  - `source`, `sourceType` – ID a typ zdrojového uzlu (`product`, `datasource`, `organization`, `community`, …).
  - `target`, `targetType` – ID a typ cílového uzlu.
  - `relType` – JSON objekt se strukturou `{"name": "...", "type": "..."}`.
    - příklady:  
      - `name = 'hasAuthorInstitution', type = 'affiliation'`  
      - `name = 'isHostedBy', type = 'provision'`
  - `provenance` – informuje o původu hrany (např. `Harvested`, `Inferred by OpenAIRE`).
  - `validated`, `validationDate` – validační metadata (většinou nevyužita).

---

## 2. Pomocné tabulky pro CZ organizace a PIDy

### `cz_org`

Podmnožina `organization` obsahující pouze organizace v ČR.

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

* **Počet řádků**: 5 007.
* **Obsah**: všechny organizace s `country.code = 'CZ'`.

---

### `dataset_pids`

Rozbalené PIDy z pole `dataset.pids`.

```sql
CREATE TABLE dataset_pids AS
SELECT
  d.id       AS dataset_id,
  pid.scheme AS pid_scheme,
  pid.value  AS pid_value
FROM dataset d,
UNNEST(d.pids) AS t(pid);
```

* **Počet řádků**: 89 962 856.
* **Důležité schéma**:

  * `dataset_id` – odkaz na `dataset.id`.
  * `pid_scheme` – např. `doi`, `handle`, `uniprot`, `ena`, `pdb`, `mag_id`, `pmid`, `pmc`, `w3id`.
  * `pid_value` – konkrétní hodnota PID (např. `10.1234/abcd`, `10261/360124`, `20.500.14352/118657`).

Tohle je univerzální tabulka pro analýzy podle PID schémat.

---

### `dataset_handles`

Datasety, které mají handle PID.

```sql
CREATE TABLE dataset_handles AS
SELECT
  dataset_id,
  pid_value AS handle
FROM dataset_pids
WHERE pid_scheme = 'handle';
```

* **Počet řádků**: 147 627.
* **Obsah**: pouze záznamy s `pid_scheme = 'handle'`.

---

### `cz_dataset_aff`

CZ-afiliované produkty/datasety podle OpenAIRE relace `hasAuthorInstitution`.

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

* **Počet řádků**: 14 799.
* **Obsah**:

  * `dataset_id` – produkt/dataset v OpenAIRE Graphu.
  * `org_id` – CZ organizace (`cz_org.id`).
* Každý pár říká, že daný produkt má autora afiliovaného v dané CZ organizaci.

---

## 3. Handle-specifické tabulky (CZ + handle + repozitáře)

### `cz_dataset_handles`

CZ-afiliované produkty, které mají zároveň handle PID.

```sql
CREATE TABLE cz_dataset_handles AS
SELECT DISTINCT
  a.dataset_id,
  h.handle,
  a.org_id
FROM cz_dataset_aff a
JOIN dataset_handles h ON h.dataset_id = a.dataset_id;
```

* **Počet řádků**: 635.
* **Obsah**:

  * `dataset_id` – produkt/dataset.
  * `handle` – hodnota handle PIDu (typicky `10261/...`, `20.500....`, někdy přímo URL `https://hdl.handle.net/...`).
  * `org_id` – CZ organizace, ke které je dataset afiliován.

---

### `cz_dataset_ids`

Pomocná tabulka se seznamem datasetů (produkty), které jsou CZ-afiliované a mají handle.

```sql
CREATE TABLE cz_dataset_ids AS
SELECT DISTINCT dataset_id
FROM cz_dataset_handles;
```

* **Počet řádků**: ≤ 635.
* Používá se k omezení dotazů na `relation` při hledání hostujících datasourců.

---

### `cz_dataset_datasource`

Hostující datasourcy (`datasource`) pro CZ-afiliované datasety s handle PIDy.

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

* **Počet řádků**: 402.
* **Obsah**:

  * `dataset_id` – dataset s handle a CZ afiliací.
  * `datasource_id` – ID repozitáře / zdroje (`datasource.id`), který dataset hostuje (`isHostedBy`).

---

### `cz_handles_enriched`

„Plná“ tabulka: CZ datasety s handle PIDem + CZ organizace + hostující repozitáře.

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

* **Počet řádků**: 1 275.
* **Důvod vyššího počtu než 635**:

  * dataset může mít více CZ afiliovaných organizací,
  * dataset může být spojen s více datasourcy.
* **Obsah**:

  * identita datasetu + handle (`dataset_id`, `handle`),
  * základní metadata datasetu (`mainTitle`, `publicationDate`),
  * CZ organizace (`org_short_name`, `org_name`, `org_country`),
  * hostující repozitář (`datasource_id`, `datasource_name`, `datasource_eng_name`, `datasource_url`, `datasource_type`).

---

### `cz_handles_enriched_dedup`

Deduplicovaná verze výše – maximálně jedna řádka pro každou dvojici `(dataset_id, handle)`.

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

* **Počet řádků**: `COUNT(DISTINCT dataset_id, handle)` (jedna řádka na dataset + handle).
* **Struktura**: stejné sloupce jako `cz_handles_enriched`, jen bez pomocného `rn`.
* **Použití**:

  * export „jedna řádka na dataset+handle“ do CSV,
  * další enrichment (např. DOI).

---

### `cz_handles_enriched_dedup_with_doi`

Deduplicovaná tabulka handle-datasetů doplněná o informaci, zda má dataset také DOI a jaké.

Vznikla dotazem typu:

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

* **Sloupce navíc**:

  * `doi_list` – seznam všech DOI pro daný dataset (oddělený `;`), nebo `NULL`, pokud dataset žádný DOI nemá.
  * `has_doi` – `TRUE`/`FALSE` (resp. 1/0) podle toho, zda existuje alespoň jeden DOI PID.

* **Použití**:

  * rychlá filtrace handle-datasetů s/bez DOI,
  * analýzy typu „kolik CZ handle-datasetů má paralelně také DOI a v jakých repozitářích“.

---

## 4. CSV exporty pro další práci

Pro další práci se používají CSV exporty uložené v repozitáři pod:

`openaire_cz_data/dump/`

Typicky zahrnují:

* **„full“ exporty** s více řádků na dataset (kvůli vícenásobným CZ institucím a více datasourcům),
* **„dedup“ exporty** ve smyslu „maximálně jedna řádka na `(dataset_id, handle)`“,
* a u deduplikované verze i informaci o existenci a hodnotách DOI (`doi_list`, `has_doi`).

Konkrétní soubory v tomto adresáři odrážejí aktuální stav analýzy (např. deduplikované handle datasety s DOI enrichmentem) a slouží jako stabilní vstupy pro další nástroje (Python notebooky, R skripty, dashboardy atd.).
