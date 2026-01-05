# OpenAIRE CZ harvest – public output v4

This folder contains the **v4** public output: links
**(Czech institution – author – dataset/DOI)** for datasets with `publicationDate >= 2021-01-01`.

## Files
- `cz_institution_author_datasets_all_2021plus_dedup_clean_v4.csv` – main output (CSV, UTF-8, `;` delimiter)
- `cz_institution_author_datasets_all_2021plus_dedup_clean_v4.csv.gz` – compressed version
- `checksums.sha256` – SHA256 checksums
- `data_dictionary.md` – column meanings, caveats, recommended use

## Coverage and counts (v4)
Distinct datasets (`dataset_id`): **7,853**

Rows by `affiliation_source`:
- `datacite`: 17,234
- `datacite_only`: 2,358
- `openaire`: 18,598

## Key caveats (short)
- OpenAIRE Graph often provides dataset↔organization and dataset↔authors separately; explicit author↔organization links are not guaranteed.
  In v4, OpenAIRE-derived rows are additionally restricted using DataCite where DataCite can identify Czech authors for the same DOI.
- DataCite affiliations are free-text strings; mapping to Czech institutions involves heuristics and manual review (false negatives possible).

