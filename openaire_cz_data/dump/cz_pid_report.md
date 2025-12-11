# CZ datasets in OpenAIRE with non-DOI PIDs

This page documents persistent identifier (PID) schemes used for datasets that are affiliated with Czech institutions in the OpenAIRE Graph, and highlights those datasets that only have non-DOI PIDs.

---

## Summary by PID scheme

Source: `cz_pid_scheme_stats_full_vs_dedup.csv`.

| pid_scheme | n_pid_rows | n_aff_rows_full | n_datasets_with_scheme_dedup | n_datasets_with_scheme_and_doi_dedup | n_datasets_with_non-doi_scheme_only |
|-----------:|-----------:|----------------:|------------------------------:|--------------------------------------:|-------------------------------------:|
| doi       |    15 892 |         14 707 |                       10 271 |                                 10 271 |                                     0 |
| handle    |       223 |            556 |                          197 |                                    179 |                                    18 |
| mag_id    |        46 |             61 |                           46 |                                     46 |                                     0 |
| pmid      |        11 |             25 |                           11 |                                      0 |                                    11 |
| pmc       |         6 |             13 |                            6 |                                      0 |                                     6 |
| pdb       |         5 |              9 |                            5 |                                      5 |                                     0 |

Totals:

- number of CZ affiliation rows in `cz_dataset_aff` (full, with duplicates): **14 799**
- number of unique CZ datasets (distinct `dataset_id`): **10 315**

---

## Column descriptions

All counts are computed over datasets that have at least one affiliation to a Czech organisation (`cz_dataset_aff`), i.e. datasets that are related to at least one organisation with `country.code = 'CZ'` in the OpenAIRE Graph.

- **`pid_scheme`**  
  PID scheme as it appears in `dataset_pids.pid_scheme`, e.g. `doi`, `handle`, `pmid`, `pmc`, `pdb`, `mag_id`.

- **`n_pid_rows`**  
  Number of PID rows in `dataset_pids` for the given `pid_scheme`, restricted to datasets that have at least one Czech affiliation. One row ≙ one `(dataset_id, pid_scheme, pid_value)` triple.

- **`n_aff_rows_full`**  
  Number of affiliation rows (full, not deduplicated) for datasets that have at least one PID of the given scheme. Concretely: count of rows in `cz_dataset_aff` for all datasets that appear in `dataset_pids` with this `pid_scheme`. One row ≙ one `(dataset_id, CZ organisation)` pair.

- **`n_datasets_with_scheme_dedup`**  
  Number of **distinct datasets** that have at least one PID of the given scheme and at least one Czech affiliation. Each dataset is counted at most once per scheme, even if it has multiple PIDs of that scheme (e.g. multiple DOIs).

- **`n_datasets_with_scheme_and_doi_dedup`**  
  Number of **distinct datasets** that have at least one PID of the given `pid_scheme` *and* at least one DOI (`pid_scheme = 'doi'`), and at least one Czech affiliation.

- **`n_datasets_with_non-doi_scheme_only`**  
  Number of **distinct datasets** that have at least one PID of the given `pid_scheme`, have **no DOI** (`pid_scheme = 'doi'`), and at least one Czech affiliation.  
  By construction:
  ```text
  n_datasets_with_non-doi_scheme_only
    = n_datasets_with_scheme_dedup
      - n_datasets_with_scheme_and_doi_dedup
  ```
  For `doi` itself this value is always `0` (a dataset cannot “have a DOI but no DOI”).

---

## CZ datasets with non-DOI PIDs only

This section lists individual CZ datasets that have **only non-DOI PIDs** of a given scheme, i.e. they have at least one PID of the given scheme (`handle`, `pmid`, `pmc`), but **no DOI** in the OpenAIRE Graph.

Formally, a dataset appears below for a given `pid_scheme` if:

- it has at least one row in `dataset_pids` with this `pid_scheme`, and
- it has **no** row in `dataset_pids` with `pid_scheme = 'doi'`, and
- it has at least one row in `cz_dataset_aff` (Czech affiliation).

For each dataset we show:

- main title and publication date,
- OpenAIRE dataset identifier,
- non-DOI PID values (with clickable PID URLs where applicable),
- affiliated Czech organisations,
- and repository / datasource information, where available.

### Datasets with handle only (no DOI)

_Total: 18 CZ datasets with `handle` PIDs and no DOI._

### Datasets with PMID only (no DOI)

_Total: 11 CZ datasets with `pmid` PIDs and no DOI._

PMID values are linked to PubMed using the pattern <https://pubmed.ncbi.nlm.nih.gov/PMID/>.

### Datasets with PMC only (no DOI)

_Total: 6 CZ datasets with `pmc` PIDs and no DOI._

PMC IDs are linked to PubMed Central using the pattern <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC…/>.

- **Fine tuning of surface CRLF2 expression and its associated signaling profile in childhood B-cell precursor acute lymphoblastic leukemia.** (2016-02-12)  
  OpenAIRE Dataset ID: [pmid________::3ae470aea0c87c521af6cc1e227cd970](https://explore.openaire.eu/search/dataset?datasetId=pmid________::3ae470aea0c87c521af6cc1e227cd970)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4450636/>  
  CZ organisations (short): `Charles University`  
  CZ organisations (full): `Charles University`  
  Repositories: Unknown Repository – Publication Repository

- **Long-term treatment results of Polish pediatric and adolescent patients enrolled in the ALL IC-BFM 2002 trial.** (2020-03-26)  
  OpenAIRE Dataset ID: [pmid________::f0bb79901320c25b0267b6861930658a](https://explore.openaire.eu/search/dataset?datasetId=pmid________::f0bb79901320c25b0267b6861930658a)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6852109/>  
  CZ organisations (short): `Charles University; University Hospital in Motol`  
  CZ organisations (full): `Charles University; University Hospital in Motol`  
  Repositories: Unknown Repository – Publication Repository

- **Long-term follow up of pediatric Philadelphia positive acute lymphoblastic leukemia treated with the EsPhALL2004 study: high white blood cell count at diagnosis is the strongest prognostic factor.** (2020-06-15)  
  OpenAIRE Dataset ID: [pmid________::114423b20d2641a0a80ca178f9675f87](https://explore.openaire.eu/search/dataset?datasetId=pmid________::114423b20d2641a0a80ca178f9675f87)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6312020/>  
  CZ organisations (short): `University Hospital in Motol`  
  CZ organisations (full): `University Hospital in Motol`  
  Repositories: Unknown Repository – Publication Repository

- **Successful early treatment combining remdesivir with high-titer convalescent plasma among COVID-19-infected hematological patients.** (2021-12-14)  
  OpenAIRE Dataset ID: [pmid________::60771a5dd35052f127c28a112a589a28](https://explore.openaire.eu/search/dataset?datasetId=pmid________::60771a5dd35052f127c28a112a589a28)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8426890/>  
  CZ organisations (short): `BC; JČU; MU; University Hospital Brno; VRI`  
  CZ organisations (full): `Biology Centre; Masaryk University; University Hospital Brno; University of South Bohemia in České Budějovice; Veterinary Research Institute`  
  Repositories: Unknown Repository – Publication Repository

- **Kinetics of anti-SARS-CoV-2 neutralizing antibodies development after BNT162b2 vaccination in patients with amyloidosis and the impact of therapy.** (2021-12-27)  
  OpenAIRE Dataset ID: [pmid________::2c97baf40c753ce5b0287105b6258036](https://explore.openaire.eu/search/dataset?datasetId=pmid________::2c97baf40c753ce5b0287105b6258036)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8646930/>  
  CZ organisations (short): `SEVEN; Seven`  
  CZ organisations (full): `SEVEN, THE ENERGY EFFICIENCY CENTER Z.U.; Seven`  
  Repositories: Unknown Repository – Publication Repository

- **COVID-19 in vaccinated adult patients with hematological malignancies: preliminary results from EPICOVIDEHA.** (2022-03-21)  
  OpenAIRE Dataset ID: [pmid________::e359ef59404e0a39d48d4e9235a1f28a](https://explore.openaire.eu/search/dataset?datasetId=pmid________::e359ef59404e0a39d48d4e9235a1f28a)  
  PMC ID(s): <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8577877/>  
  CZ organisations (short): `MU; University Hospital Brno`  
  CZ organisations (full): `Masaryk University; University Hospital Brno`  
  Repositories: Unknown Repository – Publication Repository

---

## Reproducibility notes

- All numbers above are derived from the DuckDB database `openaire_10_6.duckdb` created from the OpenAIRE Graph dumps, using the
  helper tables described in the project documentation (`cz_org`, `cz_dataset_aff`, `dataset_pids`, `cz_dataset_datasource_all`, …).

- The queries embedded in this script can be used to regenerate the lists of non-DOI-only datasets and to update this Markdown page after future re-harvests of the OpenAIRE Graph.
