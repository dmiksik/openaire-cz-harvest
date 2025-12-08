# OpenAIRE CZ harvest & PID analysis

This repository contains small Python and shell utilities, plus derived data,
used to **harvest and analyse OpenAIRE records for datasets related to Czech
research** (countryCode = `CZ`), with a special focus on **persistent identifier
(PID) schemes** (DOI, Handle, and others) and on **non-DOI PIDs**.

The repo is meant as a reproducible, versioned notebook:
- harvesting all dataset records with `countryCode=CZ` from OpenAIRE,
- extracting subsets of records with non-DOI PIDs,
- generating human-readable Markdown reports (including per-record, clickable
  link lists).

> **Note:** This is exploratory / research code, not a polished library.  
> Commands below are examples – always check `-h/--help` of each script for the
> exact, up-to-date CLI options.

---

## Repository layout

Top-level:

- `harvest-cz-dataset-records-ChatGPT.py`  
  Main harvester script for OpenAIRE research products (datasets) with
  `countryCode=CZ`.

- `harvest-cz-dataset-records-Claude.py`  
  Alternative version of the harvester kept for comparison and
  provenance.

- `openaire_cz_data/`  
  Working data directory, split by “assistant” used when the code / scripts
  were drafted:

  - `openaire_cz_data/chatgpt/`
    - `cz_datasets_countryCZ.jsonl` (and/or `.jsonl.gz`)  
      Raw harvest of all OpenAIRE records with `type=dataset` and
      `countryCode=CZ`.

    - `cz_datasets_countryCZ_non_doi_pids.jsonl`  
      Subset of records where at least one PID has a scheme **other than**
      `doi` (non-DOI PIDs).

    - `non_doi_records_table.md`  
      Markdown report with:
      - overview statistics and PID scheme combinations, and  
      - a two-row table per record with clickable URLs.

    - `scripts/generate_non_doi_markdown_table.py`  
      Script generating the Markdown report (statistics + per-record table)
      from the JSONL inputs.

    - `filter_cz_datasets_non_doi_pids.py`  
      Helper script to filter the harvest down to records with non-DOI PIDs.

  - `openaire_cz_data/claude/`  
    Parallel analysis outputs and helper scripts (JSON/CSV exports,
    HTML/Markdown tables, shell helpers). Kept for provenance and comparison.

Exact filenames may evolve over time, but the general pattern is:

- full harvest → JSONL (`cz_datasets_countryCZ.*`)  
- filtered subset → JSONL (`*_non_doi_pids.jsonl`)  
- report(s) → Markdown / HTML (`*_records_table.*`)  
- helper code → `scripts/` or small shell scripts.

---

## Requirements

- Python **3.9+**
- Standard library (json, gzip, argparse, etc.)
- Plus, for HTTP access to the OpenAIRE API:
  - [`requests`](https://pypi.org/project/requests/) (recommended)

You can install dependencies into a virtualenv, e.g.:

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests
