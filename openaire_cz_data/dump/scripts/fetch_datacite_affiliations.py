#!/usr/bin/env python3
import csv
import json
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests


# --- Konfigurace / defaulty ---------------------------------------------------

# Defaultní vstupní/výstupní soubory, když nespecifikuješ argumenty
DEFAULT_INPUT_CSV = "openaire_minus_datacite_dois_norm.csv"
DEFAULT_OUTPUT_CSV = "datacite_affiliations_for_openaire_minus_datacite.csv"

DATACITE_BASE_URL = "https://api.datacite.org/dois/"
REQUEST_TIMEOUT = 20  # s
REQUEST_SLEEP = 0.2   # pauza mezi dotazy, aby se API úplně nezahltilo


# --- Pomocné funkce -----------------------------------------------------------

def log(msg: str) -> None:
    """Jednoduché logování na stderr (aby se nemíchalo s CSV výstupem)."""
    print(msg, file=sys.stderr, flush=True)


def normalize_doi(doi: str) -> str:
    """
    Normalizace DOI ve stejném duchu jako v DuckDB:

      LOWER(
        regexp_replace(
          regexp_replace(trim(doi),
            '^https?://(dx[.])?doi[.]org/', ''),
          '^doi:', ''
        )
      )
    """
    if doi is None:
        return ""
    doi = doi.strip()
    if not doi:
        return ""
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:", "", doi, flags=re.IGNORECASE)
    return doi.lower()


def load_dois_from_csv(path: str) -> List[Tuple[str, str]]:
    """
    Načte DOIs ze vstupního CSV souboru.

    - hledá sloupec 'doi_norm', jinak 'doi'/'DOI', jinak první sloupec
    - normalizuje DOI (normalize_doi)
    - odebírá duplicitní DOI podle doi_norm
    """
    dois: List[Tuple[str, str]] = []
    seen: set[str] = set()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError("Vstupní CSV nemá hlavičku.")

        # zkusíme odhadnout, který sloupec obsahuje DOI
        candidates = ["doi_norm", "doi", "DOI", "pid"]
        doi_col: Optional[str] = None
        for c in candidates:
            if c in reader.fieldnames:
                doi_col = c
                break
        if doi_col is None:
            # fallback: první sloupec
            doi_col = reader.fieldnames[0]
            log(
                f"Varování: nenašel jsem sloupec 'doi_norm' ani 'doi', "
                f"používám první sloupec: {doi_col}"
            )
        else:
            log(f"Používám sloupec s DOI: {doi_col}")

        for row in reader:
            raw = (row.get(doi_col) or "").strip()
            if not raw:
                continue
            doi_norm = normalize_doi(raw)
            if not doi_norm:
                continue
            if doi_norm in seen:
                continue
            seen.add(doi_norm)
            dois.append((raw, doi_norm))

    return dois


def fetch_datacite_record(doi_norm: str, session: Optional[requests.Session] = None) -> Optional[Dict[str, Any]]:
    """
    Zavolá DataCite API pro daný DOI (v normalizované podobě).
    Vrací dict (parsed JSON) nebo None při chybě.
    """
    if session is None:
        session = requests.Session()

    url = DATACITE_BASE_URL + quote(doi_norm)
    log(f"GET {url}")

    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        log(f"  -> ERROR při requestu: {e!r}")
        return None

    if resp.status_code == 200:
        log("  -> OK 200")
        try:
            return resp.json()
        except json.JSONDecodeError as e:
            log(f"  -> ERROR při parsování JSON: {e!r}")
            return None
    else:
        log(f"  -> HTTP {resp.status_code}, DOI {doi_norm} přeskočeno")
        return None


def extract_affiliations(doi_norm: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Z response DataCite API vytáhne seznam řádků (autor + afiliace).

    Výstupní struktura řádku:
      - doi
      - doi_norm
      - creator_index
      - creator_name
      - given_name
      - family_name
      - name_type
      - orcid
      - affiliation_name
      - affiliation_identifier
      - affiliation_identifier_scheme
      - affiliation_scheme_uri
    """
    rows: List[Dict[str, Any]] = []

    rec = data.get("data", {}) or {}
    attributes = rec.get("attributes", {}) or {}

    doi = attributes.get("doi") or rec.get("id") or doi_norm

    creators = attributes.get("creators") or []
    if not isinstance(creators, list):
        # pro jistotu – kdyby tam někdo dal nesmysl
        creators = []

    for idx, creator in enumerate(creators, start=1):
        if not isinstance(creator, dict):
            # nečekaný formát, přeskočíme
            continue

        creator_name = creator.get("name")
        given_name = creator.get("givenName")
        family_name = creator.get("familyName")
        name_type = creator.get("nameType")

        # ORCID z nameIdentifiers (nebo value obsahující orcid.org)
        orcid = None
        for ni in creator.get("nameIdentifiers") or []:
            if not isinstance(ni, dict):
                continue
            scheme = (ni.get("nameIdentifierScheme") or ni.get("scheme") or "").upper()
            value = (ni.get("nameIdentifier") or ni.get("value") or "").strip()
            if not value:
                continue
            if scheme == "ORCID" or "orcid.org" in value.lower():
                orcid = value
                break

        # affiliations: může to být
        # - list objektů
        # - list řetězců
        # - jeden objekt
        # - jeden string
        affiliations = creator.get("affiliation") or []
        if isinstance(affiliations, (str, bytes)):
            affiliations = [affiliations]
        elif isinstance(affiliations, dict):
            affiliations = [affiliations]
        elif not isinstance(affiliations, list):
            affiliations = []

        # pokud nejsou žádné affiliace, chceme aspoň jeden řádek "bez aff"
        if not affiliations:
            rows.append(
                {
                    "doi": doi,
                    "doi_norm": doi_norm,
                    "creator_index": idx,
                    "creator_name": creator_name,
                    "given_name": given_name,
                    "family_name": family_name,
                    "name_type": name_type,
                    "orcid": orcid,
                    "affiliation_name": None,
                    "affiliation_identifier": None,
                    "affiliation_identifier_scheme": None,
                    "affiliation_scheme_uri": None,
                }
            )
            continue

        for aff in affiliations:
            if isinstance(aff, dict):
                aff_name = (
                    aff.get("name")
                    or aff.get("affiliationName")
                    or ""
                )
                aff_id = aff.get("affiliationIdentifier") or aff.get("id")
                aff_scheme = (
                    aff.get("affiliationIdentifierScheme")
                    or aff.get("scheme")
                )
                aff_uri = (
                    aff.get("schemeUri")
                    or aff.get("affiliationIdentifierSchemeURI")
                )
            else:
                # aff je string – to byl ten případ, kde to dřív padalo
                aff_name = str(aff)
                aff_id = None
                aff_scheme = None
                aff_uri = None

            rows.append(
                {
                    "doi": doi,
                    "doi_norm": doi_norm,
                    "creator_index": idx,
                    "creator_name": creator_name,
                    "given_name": given_name,
                    "family_name": family_name,
                    "name_type": name_type,
                    "orcid": orcid,
                    "affiliation_name": aff_name,
                    "affiliation_identifier": aff_id,
                    "affiliation_identifier_scheme": aff_scheme,
                    "affiliation_scheme_uri": aff_uri,
                }
            )

    return rows


# --- Hlavní běh ---------------------------------------------------------------

def main() -> None:
    # Argumenty: input_csv [output_csv]
    if len(sys.argv) >= 2:
        input_csv = sys.argv[1]
    else:
        input_csv = DEFAULT_INPUT_CSV

    if len(sys.argv) >= 3:
        output_csv = sys.argv[2]
    else:
        output_csv = DEFAULT_OUTPUT_CSV

    log(f"Vstupní CSV s DOIs: {input_csv}")
    log(f"Výstupní CSV s afiliacemi: {output_csv}")

    try:
        dois = load_dois_from_csv(input_csv)
    except FileNotFoundError:
        log(f"ERROR: nenalezen vstupní soubor: {input_csv}")
        sys.exit(1)

    n = len(dois)
    log(f"Nalezeno {n} unikátních DOI k dotazu.")

    if n == 0:
        log("Nemám žádné DOI, končím.")
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

    session = requests.Session()
    total_rows = 0

    with open(output_csv, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for i, (raw_doi, doi_norm) in enumerate(dois, start=1):
            log(f"[{i}/{n}] DOI: {raw_doi} (norm: {doi_norm})")

            data = fetch_datacite_record(doi_norm, session=session)
            if data is None:
                continue

            try:
                rows = extract_affiliations(doi_norm, data)
            except Exception as e:
                log(f"  -> ERROR při zpracování DOI {doi_norm}: {e!r}")
                continue

            for row in rows:
                writer.writerow(row)
                total_rows += 1

            # jednoduchá pauza kvůli rate limiting
            time.sleep(REQUEST_SLEEP)

    log(f"Hotovo. Zapsáno {total_rows} řádků do {output_csv}.")


if __name__ == "__main__":
    main()

