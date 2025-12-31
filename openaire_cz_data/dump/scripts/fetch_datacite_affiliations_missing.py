#!/usr/bin/env python3
import csv
import os
import sys
import time
from urllib.parse import quote

import requests

# Vstupní soubory (relativně k adresáři dump/)
OPENAIRE_DOIS_CSV = "openaire_minus_datacite_dois_norm.csv"
HARVESTED_AFFILS_CSV = "datacite_affiliations_for_openaire_minus_datacite.csv"

# Výstup – nově sklizené afiliace (jen pro chybějící DOIs)
OUTPUT_CSV = "datacite_affiliations_for_openaire_minus_datacite_missing.csv"

DATACITE_API_TEMPLATE = "https://api.datacite.org/dois/{}"

# Základní pauza mezi požadavky
SLEEP_SECONDS = 0.7  # můžeš si pohrát, když budeš chtít být šetrnější


def normalize_doi(doi: str) -> str:
    """Znormalizuje DOI do tvaru '10.xxxx/...' (bez http(s), dx., doi: atd.)."""
    if not doi:
        return ""
    d = doi.strip()

    prefixes = [
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
    ]
    for pref in prefixes:
        if d.lower().startswith(pref):
            d = d[len(pref):]
            break

    if d.lower().startswith("doi:"):
        d = d[4:]

    return d.strip().lower()


def load_openaire_dois(path: str) -> set[str]:
    """Načte množinu všech DOIs (doi_norm) z openaire_minus_datacite_dois_norm.csv."""
    dois: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("doi_norm") or row.get("doi") or ""
            norm = normalize_doi(raw)
            if norm:
                dois.add(norm)
    return dois


def load_harvested_dois(path: str) -> set[str]:
    """Načte množinu už sklizených DOIs z datacite_affiliations_for_openaire_minus_datacite.csv."""
    if not os.path.exists(path):
        return set()

    dois: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row.get("doi_norm") or row.get("doi") or ""
            norm = normalize_doi(raw)
            if norm:
                dois.add(norm)
    return dois


def fetch_datacite_record(doi_norm: str):
    """
    Dotáže DataCite API pro daný DOI (normalizovaný) a vrátí JSON (nebo None).

    DŮLEŽITÉ: tahle funkce *vždy* po požadavku čeká:
      - SLEEP_SECONDS po 200/404/410/ostatních stavech
      - SLEEP_SECONDS * 5 po 429
    """
    url = DATACITE_API_TEMPLATE.format(quote(doi_norm))
    print(f"[DOI] {doi_norm}")
    print(f"  GET {url}")

    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/vnd.api+json"},
            timeout=30,
        )
    except Exception as e:
        print(f"  -> ERROR {e}, DOI {doi_norm} přeskočeno")
        # pauza i při chybě spojení
        time.sleep(SLEEP_SECONDS)
        return None

    status = resp.status_code
    print(f"  -> HTTP {status}")

    if status == 200:
        try:
            data = resp.json()
        except Exception as e:
            print(f"  -> JSON decode error: {e}, DOI {doi_norm} přeskočeno")
            time.sleep(SLEEP_SECONDS)
            return None

        time.sleep(SLEEP_SECONDS)
        return data

    if status in (404, 410):
        print(f"  -> DOI {doi_norm} v DataCite není (404/410), přeskočeno")
        time.sleep(SLEEP_SECONDS)
        return None

    if status == 429:
        print(f"  -> HTTP 429 (rate limit), DOI {doi_norm} přeskočeno – delší pauza")
        # delší pauza, ať se to trochu uklidní
        time.sleep(SLEEP_SECONDS * 5)
        return None

    # Ostatní statusy
    print(f"  -> Nečekaný status {status}, DOI {doi_norm} přeskočeno")
    time.sleep(SLEEP_SECONDS)
    return None


def extract_affiliations(doi_norm: str, payload) -> list[dict]:
    """Z payloadu DataCite vytáhne řádky (autor + afiliace)."""
    rows: list[dict] = []
    if not payload:
        return rows

    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}
    creators = attributes.get("creators") or []
    doi_from_api = data.get("id") or doi_norm

    for idx, creator in enumerate(creators, start=1):
        name = creator.get("name")
        given = creator.get("givenName")
        family = creator.get("familyName")
        name_type = creator.get("nameType")

        orcid = None
        for ni in creator.get("nameIdentifiers") or []:
            scheme = (ni.get("nameIdentifierScheme") or "").upper()
            if scheme == "ORCID":
                orcid = ni.get("nameIdentifier")
                break

        affiliations = creator.get("affiliation") or []
        if not isinstance(affiliations, list):
            affiliations = [affiliations]

        if not affiliations:
            rows.append({
                "doi": doi_from_api,
                "doi_norm": doi_norm,
                "creator_index": idx,
                "creator_name": name,
                "given_name": given,
                "family_name": family,
                "name_type": name_type,
                "orcid": orcid,
                "affiliation_name": None,
                "affiliation_identifier": None,
                "affiliation_identifier_scheme": None,
                "affiliation_scheme_uri": None,
            })
            continue

        for aff in affiliations:
            if isinstance(aff, str):
                aff_name = aff
                aff_id = None
                aff_scheme = None
                aff_scheme_uri = None
            else:
                aff_name = aff.get("name")
                aff_id = aff.get("affiliationIdentifier")
                aff_scheme = aff.get("affiliationIdentifierScheme")
                aff_scheme_uri = aff.get("schemeUri")

            rows.append({
                "doi": doi_from_api,
                "doi_norm": doi_norm,
                "creator_index": idx,
                "creator_name": name,
                "given_name": given,
                "family_name": family,
                "name_type": name_type,
                "orcid": orcid,
                "affiliation_name": aff_name,
                "affiliation_identifier": aff_id,
                "affiliation_identifier_scheme": aff_scheme,
                "affiliation_scheme_uri": aff_scheme_uri,
            })

    return rows


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    openaire_path = os.path.join(base_dir, OPENAIRE_DOIS_CSV)
    harvested_path = os.path.join(base_dir, HARVESTED_AFFILS_CSV)
    output_path = os.path.join(base_dir, OUTPUT_CSV)

    if not os.path.exists(openaire_path):
        print(f"Soubor s DOIs z OpenAIRE neexistuje: {openaire_path}")
        sys.exit(1)

    # 1) Načíst všechny DOIs z OpenAIRE-minus-DataCite
    all_dois = load_openaire_dois(openaire_path)
    # 2) Načíst už sklizené DOIs z první vlny
    harvested_dois = load_harvested_dois(harvested_path)
    # 3) Množinový rozdíl = co ještě chybí
    missing_dois = sorted(all_dois - harvested_dois)

    print(f"Vstupních DOIs (OpenAIRE minus DataCite): {len(all_dois)}")
    print(f"Již sklizených DOIs: {len(harvested_dois)}")
    print(f"Chybějících DOIs: {len(missing_dois)}")

    if not missing_dois:
        print("Všechna DOIs už byla sklizena, není co dělat. 🙂")
        return

    fieldnames = [
        "doi",
        "doi_norm",
        "creator_index",
        "creator_name",
        "given_name",
        "family_name",
        "name_type",
        "orcid",
        "affiliation_name",
        "affiliation_identifier",
        "affiliation_identifier_scheme",
        "affiliation_scheme_uri",
    ]

    total_rows = 0
    with open(output_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        n_missing = len(missing_dois)
        for i, doi_norm in enumerate(missing_dois, start=1):
            print(f"[{i}/{n_missing}] DOI: {doi_norm}")
            payload = fetch_datacite_record(doi_norm)
            rows = extract_affiliations(doi_norm, payload)
            for row in rows:
                writer.writerow(row)
            total_rows += len(rows)

    print(f"Hotovo. Zapsáno {total_rows} řádků do {output_path}.")


if __name__ == "__main__":
    main()

