#!/usr/bin/env python3
"""
Generate Markdown report for CZ PID schemes and non-DOI-only datasets.

- Reads data from DuckDB database `openaire_10_6.duckdb`
- Writes a Markdown file with:
  - summary table by PID scheme
  - column explanations
  - three detailed lists of datasets:
      * handle-only (no DOI)
      * pmid-only (no DOI)
      * pmc-only (no DOI)
"""

from pathlib import Path
import duckdb
from datetime import date

# --- CONFIG -------------------------------------------------------------

# Path to DuckDB database
DB_PATH = Path("/home/ubuntu/duckdb/openaire_10_6.duckdb")

# Output markdown file
OUT_PATH = Path("/home/ubuntu/open-aire-harvest/openaire_cz_data/dump/cz_pid_report.md")

# ------------------------------------------------------------------------


def format_int(n):
    """Format integer with thin spaces for readability."""
    if n is None:
        return ""
    return f"{n:,}".replace(",", " ")


def make_handle_url(value: str) -> str:
    """Return clickable handle URL for a given handle value."""
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return f"<{value}>"
    # default: assume bare handle
    return f"<https://hdl.handle.net/{value}>"


def make_pmid_url(value: str) -> str:
    """Return clickable PubMed URL for a given PMID value."""
    if not value:
        return ""
    core = value.replace("PMID:", "").strip()
    return f"<https://pubmed.ncbi.nlm.nih.gov/{core}/>"


def make_pmc_url(value: str) -> str:
    """Return clickable PMC URL for a given PMC ID value."""
    if not value:
        return ""
    core = value.strip()
    if not core.upper().startswith("PMC"):
        core = "PMC" + core
    return f"<https://www.ncbi.nlm.nih.gov/pmc/articles/{core}/>"


def mk_repo_md(name: str | None, url: str | None, rtype: str | None) -> str:
    """Format repository/datasource info as Markdown."""
    name = (name or "").strip()
    url = (url or "").strip()
    rtype = (rtype or "").strip()

    label = name or url or ""
    if url:
        main = f"[{label}]({url})"
    elif label:
        main = label
    else:
        main = ""

    if rtype:
        if main:
            return f"{main} – {rtype}"
        else:
            return rtype
    return main


def section_header_for_scheme(scheme: str) -> str:
    if scheme == "handle":
        return "### Datasets with handle only (no DOI)\n"
    elif scheme == "pmid":
        return "### Datasets with PMID only (no DOI)\n"
    elif scheme == "pmc":
        return "### Datasets with PMC only (no DOI)\n"
    else:
        return f"### Datasets with {scheme} only (no DOI)\n"


def pid_label_for_scheme(scheme: str) -> str:
    if scheme == "handle":
        return "Handle(s)"
    elif scheme == "pmid":
        return "PMID(s)"
    elif scheme == "pmc":
        return "PMC ID(s)"
    else:
        return f"{scheme} PID(s)"


def make_pid_md(scheme: str, values: list[str]) -> str:
    """Format PID values for a given scheme as Markdown with clickable URLs."""
    urls = []
    for v in sorted({(v or "").strip() for v in values if v}):
        if scheme == "handle":
            urls.append(make_handle_url(v))
        elif scheme == "pmid":
            urls.append(make_pmid_url(v))
        elif scheme == "pmc":
            urls.append(make_pmc_url(v))
        else:
            # fallback: just show raw value
            urls.append(v)
    return " ; ".join(urls)


def fetch_summary_stats(con):
    """Fetch summary stats for the top table and some totals."""
    stats = con.execute(
        """
        SELECT
          pid_scheme,
          n_pid_rows,
          n_aff_rows_full,
          n_datasets_with_scheme_dedup,
          n_datasets_with_scheme_and_doi_dedup,
          n_datasets_with_non_doi_scheme_only
        FROM cz_pid_scheme_stats
        ORDER BY n_datasets_with_scheme_dedup DESC;
        """
    ).fetchall()

    totals = con.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM cz_dataset_aff)              AS n_aff_rows_full,
          (SELECT COUNT(DISTINCT dataset_id) FROM cz_dataset_aff) AS n_datasets_cz
        """
    ).fetchone()

    return stats, totals


def fetch_non_doi_datasets_for_scheme(con, scheme: str):
    """
    Return list of dicts with dataset-level info for datasets that:
    - have given pid_scheme
    - have NO doi
    - have at least one CZ affiliation
    """
    rows = con.execute(
        """
        WITH non_doi_only AS (
          SELECT DISTINCT p.dataset_id
          FROM dataset_pids p
          JOIN cz_dataset_aff a ON a.dataset_id = p.dataset_id
          WHERE p.pid_scheme = ?
            AND NOT EXISTS (
              SELECT 1
              FROM dataset_pids p2
              WHERE p2.dataset_id = p.dataset_id
                AND p2.pid_scheme = 'doi'
            )
        ),
        base AS (
          SELECT
            d.id AS dataset_id,
            d.mainTitle,
            d.publicationDate,
            p.pid_value,
            org.legalShortName,
            org.legalName,
            COALESCE(ds.officialName, ds.englishName) AS datasource_name,
            ds.type.value                              AS datasource_type,
            ds.websiteUrl                              AS datasource_url
          FROM non_doi_only n
          JOIN dataset d
            ON d.id = n.dataset_id
          LEFT JOIN dataset_pids p
            ON p.dataset_id = n.dataset_id
           AND p.pid_scheme = ?
          LEFT JOIN cz_dataset_aff a
            ON a.dataset_id = n.dataset_id
          LEFT JOIN cz_org org
            ON org.id = a.org_id
          LEFT JOIN cz_dataset_datasource_all cdd
            ON cdd.dataset_id = n.dataset_id
          LEFT JOIN datasource ds
            ON ds.id = cdd.datasource_id
        )
        SELECT * FROM base
        ORDER BY publicationDate, dataset_id;
        """,
        [scheme, scheme],
    ).fetchall()

    # Column order must match SELECT above
    datasets = {}
    for (
        dataset_id,
        main_title,
        pub_date,
        pid_value,
        org_short,
        org_name,
        ds_name,
        ds_type,
        ds_url,
    ) in rows:
        if dataset_id not in datasets:
            datasets[dataset_id] = {
                "dataset_id": dataset_id,
                "mainTitle": main_title,
                "publicationDate": pub_date,
                "pid_values": set(),
                "cz_org_short": set(),
                "cz_org_names": set(),
                "ds_names": set(),
                "ds_types": set(),
                "ds_urls": set(),
            }
        d = datasets[dataset_id]
        if pid_value:
            d["pid_values"].add(pid_value)
        if org_short:
            d["cz_org_short"].add(org_short)
        if org_name:
            d["cz_org_names"].add(org_name)
        if ds_name:
            d["ds_names"].add(ds_name)
        if ds_type:
            d["ds_types"].add(ds_type)
        if ds_url:
            d["ds_urls"].add(ds_url)

    # Return as list sorted by publicationDate, dataset_id
    def sort_key(item):
        d = item[1]
        return (d["publicationDate"] or date.min, d["dataset_id"])

    return [d for _, d in sorted(datasets.items(), key=sort_key)]


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(DB_PATH.as_posix())

    stats, totals = fetch_summary_stats(con)
    n_aff_rows_full, n_datasets_cz = totals

    lines: list[str] = []

    # --- Header & intro -------------------------------------------------
    lines.append("# CZ datasets in OpenAIRE with non-DOI PIDs\n")
    lines.append(
        "This page documents persistent identifier (PID) schemes used for "
        "datasets that are affiliated with Czech institutions in the "
        "OpenAIRE Graph, and highlights those datasets that only have "
        "non-DOI PIDs.\n"
    )
    lines.append("---\n")

    # --- Summary table --------------------------------------------------
    lines.append("## Summary by PID scheme\n")
    lines.append("Source: `cz_pid_scheme_stats_full_vs_dedup.csv`.\n")

    # Header
    lines.append(
        "| pid_scheme | n_pid_rows | n_aff_rows_full | "
        "n_datasets_with_scheme_dedup | "
        "n_datasets_with_scheme_and_doi_dedup | "
        "n_datasets_with_non-doi_scheme_only |"
    )
    lines.append(
        "|-----------:|-----------:|----------------:|"
        "------------------------------:|"
        "--------------------------------------:|"
        "-------------------------------------:|"
    )

    for (
        pid_scheme,
        n_pid_rows,
        n_aff_rows_full_scheme,
        n_datasets_with_scheme_dedup,
        n_datasets_with_scheme_and_doi_dedup,
        n_non_doi_only,
    ) in stats:
        lines.append(
            "| {scheme:<9} | {pid:>9} | {aff:>14} | {ndedup:>28} | {ndoidedup:>38} | {nnon:>37} |".format(
                scheme=pid_scheme,
                pid=format_int(n_pid_rows),
                aff=format_int(n_aff_rows_full_scheme),
                ndedup=format_int(n_datasets_with_scheme_dedup),
                ndoidedup=format_int(n_datasets_with_scheme_and_doi_dedup),
                nnon=format_int(n_non_doi_only),
            )
        )

    lines.append("")
    lines.append("Totals:\n")
    lines.append(
        f"- number of CZ affiliation rows in `cz_dataset_aff` "
        f"(full, with duplicates): **{format_int(n_aff_rows_full)}**"
    )
    lines.append(
        f"- number of unique CZ datasets (distinct `dataset_id`): "
        f"**{format_int(n_datasets_cz)}**\n"
    )
    lines.append("---\n")

    # --- Column descriptions --------------------------------------------
    lines.append("## Column descriptions\n")
    lines.append(
        "All counts are computed over datasets that have at least one "
        "affiliation to a Czech organisation (`cz_dataset_aff`), i.e. "
        "datasets that are related to at least one organisation with "
        "`country.code = 'CZ'` in the OpenAIRE Graph.\n"
    )

    lines.append("- **`pid_scheme`**  \n"
                 "  PID scheme as it appears in `dataset_pids.pid_scheme`, "
                 "e.g. `doi`, `handle`, `pmid`, `pmc`, `pdb`, `mag_id`.\n")
    lines.append("- **`n_pid_rows`**  \n"
                 "  Number of PID rows in `dataset_pids` for the given "
                 "`pid_scheme`, restricted to datasets that have at least "
                 "one Czech affiliation. One row ≙ one "
                 "`(dataset_id, pid_scheme, pid_value)` triple.\n")
    lines.append("- **`n_aff_rows_full`**  \n"
                 "  Number of affiliation rows (full, not deduplicated) for "
                 "datasets that have at least one PID of the given scheme. "
                 "Concretely: count of rows in `cz_dataset_aff` for all "
                 "datasets that appear in `dataset_pids` with this "
                 "`pid_scheme`. One row ≙ one `(dataset_id, CZ organisation)` "
                 "pair.\n")
    lines.append("- **`n_datasets_with_scheme_dedup`**  \n"
                 "  Number of **distinct datasets** that have at least one "
                 "PID of the given scheme and at least one Czech affiliation. "
                 "Each dataset is counted at most once per scheme, even if it "
                 "has multiple PIDs of that scheme (e.g. multiple DOIs).\n")
    lines.append("- **`n_datasets_with_scheme_and_doi_dedup`**  \n"
                 "  Number of **distinct datasets** that have at least one "
                 "PID of the given `pid_scheme` *and* at least one DOI "
                 "(`pid_scheme = 'doi'`), and at least one Czech affiliation.\n")
    lines.append("- **`n_datasets_with_non-doi_scheme_only`**  \n"
                 "  Number of **distinct datasets** that have at least one "
                 "PID of the given `pid_scheme`, have **no DOI** "
                 "(`pid_scheme = 'doi'`), and at least one Czech affiliation.  \n"
                 "  By construction:\n"
                 "  ```text\n"
                 "  n_datasets_with_non-doi_scheme_only\n"
                 "    = n_datasets_with_scheme_dedup\n"
                 "      - n_datasets_with_scheme_and_doi_dedup\n"
                 "  ```\n"
                 "  For `doi` itself this value is always `0` "
                 "(a dataset cannot “have a DOI but no DOI”).\n")

    lines.append("---\n")

    # --- Non-DOI-only datasets per scheme -------------------------------
    lines.append("## CZ datasets with non-DOI PIDs only\n")
    lines.append(
        "This section lists individual CZ datasets that have **only "
        "non-DOI PIDs** of a given scheme, i.e. they have at least one PID "
        "of the given scheme (`handle`, `pmid`, `pmc`), but **no DOI** in "
        "the OpenAIRE Graph.\n"
    )
    lines.append(
        "Formally, a dataset appears below for a given `pid_scheme` if:\n\n"
        "- it has at least one row in `dataset_pids` with this `pid_scheme`, and\n"
        "- it has **no** row in `dataset_pids` with `pid_scheme = 'doi'`, and\n"
        "- it has at least one row in `cz_dataset_aff` (Czech affiliation).\n"
    )
    lines.append(
        "For each dataset we show:\n\n"
        "- main title and publication date,\n"
        "- OpenAIRE dataset identifier,\n"
        "- non-DOI PID values (with clickable PID URLs where applicable),\n"
        "- affiliated Czech organisations,\n"
        "- and repository / datasource information, where available.\n"
    )

    for scheme in ("handle", "pmid", "pmc"):
        datasets = fetch_non_doi_datasets_for_scheme(con, scheme)
        header = section_header_for_scheme(scheme)
        lines.append(header)

        label = pid_label_for_scheme(scheme)
        lines.append(
            f"_Total: {len(datasets)} CZ datasets with `{scheme}` PIDs and no DOI._\n"
        )

        if scheme == "pmid":
            lines.append(
                "PMID values are linked to PubMed using the pattern "
                "<https://pubmed.ncbi.nlm.nih.gov/PMID/>.\n"
            )
        elif scheme == "pmc":
            lines.append(
                "PMC IDs are linked to PubMed Central using the pattern "
                "<https://www.ncbi.nlm.nih.gov/pmc/articles/PMC…/>.\n"
            )

        if not datasets:
            lines.append("_No datasets found for this scheme._\n")
            continue

    for d in datasets:
        title = d["mainTitle"] or "(no title)"
        pub_date = d["publicationDate"]
        pub_str = pub_date.isoformat() if isinstance(pub_date, date) else "n.d."
        dataset_id = d["dataset_id"]

        pid_md = make_pid_md(scheme, list(d["pid_values"]))
        org_short = "; ".join(sorted(d["cz_org_short"])) or "(none)"
        org_names = "; ".join(sorted(d["cz_org_names"])) or "(none)"

        # repositories
        repo_items = []
        for name in d["ds_names"] or {""}:
            for url in d["ds_urls"] or {""}:
                repo_items.append(
                    mk_repo_md(
                        name,
                        url,
                        "; ".join(sorted(d["ds_types"])) if d["ds_types"] else "",
                    )
                )
        repo_items = [r for r in sorted(set(repo_items)) if r]
        repos_md = " ; ".join(repo_items) if repo_items else "(no repository info)"

        dataset_url = (
            f"https://explore.openaire.eu/search/dataset?datasetId={dataset_id}"
        )

        lines.append(f"- **{title}** ({pub_str})  ")
        lines.append(
            f"  OpenAIRE Dataset ID: [{dataset_id}]({dataset_url})  "
        )
        if pid_md:
            lines.append(f"  {label}: {pid_md}  ")
        else:
            lines.append(f"  {label}: *(no PID values found)*  ")
        lines.append(f"  CZ organisations (short): `{org_short}`  ")
        lines.append(f"  CZ organisations (full): `{org_names}`  ")
        lines.append(f"  Repositories: {repos_md}\n")


    # --- Reproducibility notes ------------------------------------------
    lines.append("---\n")
    lines.append("## Reproducibility notes\n")
    lines.append(
        "- All numbers above are derived from the DuckDB database "
        "`openaire_10_6.duckdb` created from the OpenAIRE Graph dumps, using the\n"
        "  helper tables described in the project documentation "
        "(`cz_org`, `cz_dataset_aff`, `dataset_pids`, "
        "`cz_dataset_datasource_all`, …).\n"
    )
    lines.append(
        "- The queries embedded in this script can be used to regenerate the "
        "lists of non-DOI-only datasets and to update this Markdown page "
        "after future re-harvests of the OpenAIRE Graph.\n"
    )

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written Markdown report to {OUT_PATH}")


if __name__ == "__main__":
    main()

