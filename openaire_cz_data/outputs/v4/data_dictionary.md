# v4 data dictionary

CSV format: UTF-8, `;` delimiter.

## Columns

- `institution` – short label (helper field; not stable identifier)
- `institution_full` – human-readable institution name
- `institution_ror` – ROR URL (recommended institution identifier)
- `dataset_id` – internal dataset identifier used in the processing pipeline
- `doi` – dataset DOI used in the export
- `creator_order` – author order (typically 1-based; may differ across sources)
- `given_name`, `family_name`, `author_name` – author name fields (sometimes only `author_name`)
- `orcid` – ORCID identifier, if present
- `pids.1` … `pids.4` – additional PID strings found in metadata (not necessarily normalized)
- `affiliation_source` – origin of the author↔Czech-institution link:
  - `datacite` – author-level affiliation from DataCite (creator + affiliation string), mapped to CZ institution (ROR)
  - `datacite_only` – same as `datacite`, but the DOI/dataset is present only via the DataCite branch (no OpenAIRE branch record used)
  - `openaire` – derived from OpenAIRE Graph; OpenAIRE may not provide explicit author↔institution links (Cartesian-product risk).
    In v4, OpenAIRE-derived rows are restricted using DataCite where possible to reduce false author↔institution assignments.

## Recommended use
- Aggregate institutions by `institution_ror`, not by name strings.
- For dataset counts use `COUNT(DISTINCT dataset_id)` (not row count).
- For highest-confidence author↔institution analysis, prefer `affiliation_source in ('datacite','datacite_only')`.
