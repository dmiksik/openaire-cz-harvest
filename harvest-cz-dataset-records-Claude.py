#!/usr/bin/env python3
"""
OpenAIRE Czech Republic Data Scraper - Enhanced Version
Stáhne všechny české záznamy obejitím limitu 10 000 pomocí časových filtrů
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class OpenAIREScraper:
    """Třída pro stahování dat z OpenAIRE API."""
    
    BASE_URL_GRAPH = "https://api.openaire.eu/graph/v2/researchProducts"
    
    def __init__(self, output_dir: str = "openaire_cz_data"):
        """
        Inicializace scraperu.
        
        Args:
            output_dir: Adresář pro ukládání výstupních souborů
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenAIRE-CZ-Scraper/2.0',
            'Accept': 'application/json'
        })
        
    def get_research_products(
        self, 
        product_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict:
        """
        Získá výzkumné produkty z OpenAIRE API.
        
        Args:
            product_type: Typ produktu ('publication', 'dataset', 'software', 'other')
            from_date: Od data (YYYY-MM-DD)
            to_date: Do data (YYYY-MM-DD)
            page: Číslo stránky
            page_size: Počet záznamů na stránku (max 100)
        
        Returns:
            Dict s odpovědí API
        """
        params = {
            'countryCode': 'CZ',
            'page': page,
            'pageSize': min(page_size, 100),
            'sortBy': 'dateOfCollection DESC'
        }
        
        if product_type:
            params['type'] = product_type
        
        if from_date:
            params['fromPublicationDate'] = from_date
            
        if to_date:
            params['toPublicationDate'] = to_date
        
        try:
            response = self.session.get(self.BASE_URL_GRAPH, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Chyba při stahování dat: {e}", file=sys.stderr)
            return {}
    
    def scrape_all(
        self, 
        product_types: Optional[List[str]] = None,
        start_year: int = 2000,
        end_year: Optional[int] = None,
        delay: float = 0.1
    ) -> None:
        """
        Stáhne všechny české záznamy rozdělením podle let.
        
        Args:
            product_types: Seznam typů k stažení (None = všechny)
            start_year: Od roku (včetně)
            end_year: Do roku (včetně, None = aktuální rok)
            delay: Prodleva mezi požadavky v sekundách
        """
        if end_year is None:
            end_year = datetime.now().year
        
        if product_types is None:
            product_types = [None]  # Stáhnout všechny typy najednou
        
        for product_type in product_types:
            type_name = product_type or "all"
            print(f"\n{'='*70}")
            print(f"Stahování typu: {type_name}")
            print(f"Období: {start_year} - {end_year}")
            print(f"{'='*70}\n")
            
            all_records = []
            
            # Rozdělení podle let pro obejití limitu 10 000
            for year in range(start_year, end_year + 1):
                from_date = f"{year}-01-01"
                to_date = f"{year}-12-31"
                
                print(f"\n--- Rok {year} ---")
                year_records = self._scrape_date_range(
                    product_type, from_date, to_date, delay
                )
                
                if year_records:
                    all_records.extend(year_records)
                    print(f"  ✓ Rok {year}: {len(year_records)} záznamů")
                else:
                    print(f"  - Rok {year}: žádné záznamy")
            
            # Záznamy bez data publikace
            print(f"\n--- Záznamy bez data publikace ---")
            no_date_records = self._scrape_no_date(product_type, delay)
            if no_date_records:
                all_records.extend(no_date_records)
                print(f"  ✓ Bez data: {len(no_date_records)} záznamů")
            
            # Uložení dat
            if all_records:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._save_data(all_records, type_name, timestamp)
                print(f"\n{'='*70}")
                print(f"✓ CELKEM staženo: {len(all_records)} záznamů typu '{type_name}'")
                print(f"{'='*70}\n")
            else:
                print(f"\n✗ Žádné záznamy typu '{type_name}' nebyly nalezeny")
    
    def _scrape_date_range(
        self,
        product_type: Optional[str],
        from_date: str,
        to_date: str,
        delay: float
    ) -> List[Dict]:
        """Stáhne záznamy pro konkrétní časové období."""
        page = 1
        records = []
        consecutive_empty = 0
        max_consecutive_empty = 3
        
        while True:
            data = self.get_research_products(
                product_type, from_date, to_date, page, 100
            )
            
            if not data or 'results' not in data:
                break
            
            results = data['results']
            
            if not results or len(results) == 0:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    break
                page += 1
                time.sleep(delay)
                continue
            
            consecutive_empty = 0
            records.extend(results)
            
            print(f"  Stránka {page}: +{len(results)} záznamů (celkem: {len(records)})", end="\r")
            
            # Kontrola limitu 10 000
            if len(records) >= 9900:
                print(f"\n  ⚠ Varování: Blízko limitu 10 000! Zvažte rozdělení na menší období.")
            
            if len(results) < 100:
                break
            
            page += 1
            time.sleep(delay)
        
        print()  # Nový řádek po progress
        return records
    
    def _scrape_no_date(self, product_type: Optional[str], delay: float) -> List[Dict]:
        """Pokus o stažení záznamů bez data - experimentální."""
        # API nemusí podporovat explicitní filtr "bez data"
        # Zkusíme velmi starý rok
        return self._scrape_date_range(product_type, "1900-01-01", "1999-12-31", delay)
    
    def _save_data(self, records: List[Dict], type_name: str, timestamp: str) -> None:
        """Uloží data do JSON souboru."""
        filename = self.output_dir / f"openaire_cz_{type_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'downloaded_at': datetime.now().isoformat(),
                    'type': type_name,
                    'count': len(records),
                    'country': 'CZ'
                },
                'records': records
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n  📄 JSON uloženo: {filename}")
        
        # Uložit CSV s rozšířenými metadaty
        self._save_csv_enhanced(records, type_name, timestamp)
    
    def _save_csv_enhanced(self, records: List[Dict], type_name: str, timestamp: str) -> None:
        """Uloží rozšířená metadata do CSV podle skutečné struktury OpenAIRE."""
        import csv
        
        filename = self.output_dir / f"openaire_cz_{type_name}_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Rozšířená hlavička podle skutečné struktury API
            writer.writerow([
                'ID',
                'DOI',
                'MainTitle',
                'SubTitle',
                'Type',
                'PublicationDate',
                'Publisher',
                'Authors',
                'AuthorCount',
                'AuthorORCIDs',
                'BestAccessRight',
                'License',
                'Language',
                'Subjects',
                'Descriptions',
                'URL',
                'Organizations',
                'OrganizationIDs',
                'Projects',
                'ProjectCodes',
                'ProjectFunders',
                'Communities',
                'HostedBy',
                'CollectedFrom',
                'Citations',
                'Downloads',
                'Views',
                'Influence',
                'Popularity',
                'Version',
                'Size',
                'CodeRepository',
                'ProgrammingLanguage',
                'IsGreen',
                'IsInDiamondJournal',
                'PubliclyFunded',
                'OpenAccessColor'
            ])
            
            for record in records:
                # DOI - první z PIDs
                pids = record.get('pids') or []
                dois = [pid.get('value', '') for pid in pids if pid.get('scheme') == 'doi']
                doi = dois[0] if dois else ''
                
                # Autoři
                authors_list = record.get('authors') or []
                authors_str = '; '.join([a.get('fullName', '') for a in authors_list])
                author_count = len(authors_list)
                
                # ORCID autorů
                orcids = []
                for author in authors_list:
                    pid = author.get('pid')
                    if pid and isinstance(pid, dict):
                        if pid.get('scheme') == 'orcid':
                            orcids.append(pid.get('value', ''))
                orcids_str = '; '.join(orcids)
                
                # Access right
                best_access = record.get('bestAccessRight') or {}
                access_label = best_access.get('label', '')
                
                # License - z první instance
                instances = record.get('instances') or []
                license_info = instances[0].get('license', '') if instances else ''
                
                # Jazyk
                language = record.get('language') or {}
                language_str = f"{language.get('label', '')} ({language.get('code', '')})" if language else ''
                
                # Subjects
                subjects_list = record.get('subjects') or []
                subjects_str = '; '.join([
                    s.get('subject', {}).get('value', '') 
                    for s in subjects_list
                ])
                
                # Descriptions
                descriptions_list = record.get('descriptions') or []
                descriptions_str = ' | '.join(descriptions_list) if descriptions_list else ''
                
                # URL - z první instance
                url = ''
                if instances:
                    urls = instances[0].get('urls') or []
                    url = urls[0] if urls else ''
                
                # Organizace
                organizations = record.get('organizations') or []
                org_names = '; '.join([org.get('legalName') or '' for org in organizations])
                org_ids = '; '.join([org.get('id') or '' for org in organizations])
                
                # Projekty
                projects = record.get('projects') or []
                project_titles = '; '.join([p.get('title') or '' for p in projects])
                project_codes = '; '.join([p.get('code') or '' for p in projects])
                project_funders = '; '.join([p.get('funder') or '' for p in projects])
                
                # Communities
                communities = record.get('communities') or []
                communities_str = '; '.join([c.get('label', '') for c in communities])
                
                # Hosted by - z instancí
                hosted_by_list = []
                for inst in instances:
                    hosted = inst.get('hostedBy')
                    if hosted:
                        hosted_by_list.append(hosted.get('value', ''))
                hosted_by_str = '; '.join(set(hosted_by_list))  # unique
                
                # Collected from
                collected_from = record.get('collectedFrom') or []
                collected_str = '; '.join([c.get('value', '') for c in collected_from])
                
                # Indicators (metrics)
                indicators = record.get('indicators') or {}
                citation_impact = indicators.get('citationImpact') or {}
                usage_counts = indicators.get('usageCounts') or {}
                
                citations = citation_impact.get('citationCount', 0)
                influence = citation_impact.get('influence', 0)
                popularity = citation_impact.get('popularity', 0)
                downloads = usage_counts.get('downloads', 0)
                views = usage_counts.get('views', 0)
                
                row = [
                    record.get('id', ''),
                    doi,
                    record.get('mainTitle', ''),
                    record.get('subTitle', ''),
                    record.get('type', ''),
                    record.get('publicationDate', ''),
                    record.get('publisher', ''),
                    authors_str,
                    author_count,
                    orcids_str,
                    access_label,
                    license_info,
                    language_str,
                    subjects_str,
                    descriptions_str,
                    url,
                    org_names,
                    org_ids,
                    project_titles,
                    project_codes,
                    project_funders,
                    communities_str,
                    hosted_by_str,
                    collected_str,
                    citations,
                    downloads,
                    views,
                    influence,
                    popularity,
                    record.get('version', ''),
                    record.get('size', ''),
                    record.get('codeRepositoryUrl', ''),
                    record.get('programmingLanguage', ''),
                    record.get('isGreen', ''),
                    record.get('isInDiamondJournal', ''),
                    record.get('publiclyFunded', ''),
                    record.get('openAccessColor', '')
                ]
                writer.writerow(row)
        
        print(f"  📊 CSV uloženo: {filename}")


def main():
    """Hlavní funkce programu."""
    parser = argparse.ArgumentParser(
        description='Stáhne VŠECHNY české záznamy z OpenAIRE API (obejde limit 10k)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
  %(prog)s                                    # Všechny typy, roky 2000-2024
  %(prog)s --types dataset                    # Pouze datasety
  %(prog)s --start-year 2010 --end-year 2020  # Roky 2010-2020
  %(prog)s --types publication --start-year 2020  # Publikace od 2020
        """
    )
    
    parser.add_argument(
        '--types',
        nargs='+',
        choices=['publication', 'dataset', 'software', 'other'],
        help='Typy produktů k stažení (výchozí: všechny)'
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=2000,
        help='Od roku (výchozí: 2000)'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        help='Do roku (výchozí: aktuální rok)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='openaire_cz_data',
        help='Výstupní adresář (výchozí: openaire_cz_data)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0.1,
        help='Prodleva mezi požadavky v sekundách (výchozí: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Vytvoření scraperu
    scraper = OpenAIREScraper(output_dir=args.output_dir)
    
    # Informace o spuštění
    end_year = args.end_year or datetime.now().year
    print(f"\n{'='*70}")
    print(f"OpenAIRE Czech Republic Enhanced Scraper")
    print(f"{'='*70}")
    print(f"Země: Česká republika (CZ)")
    print(f"Období: {args.start_year} - {end_year}")
    print(f"Metoda: Rozdělení podle roků (obchází limit 10 000)")
    print(f"Výstupní adresář: {args.output_dir}")
    print(f"{'='*70}\n")
    
    # Spuštění stahování
    start_time = time.time()
    
    try:
        scraper.scrape_all(
            product_types=args.types,
            start_year=args.start_year,
            end_year=args.end_year,
            delay=args.delay
        )
    except KeyboardInterrupt:
        print("\n\n⚠ Stahování přerušeno uživatelem")
        sys.exit(1)
    
    # Statistiky
    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"✓ Dokončeno za {elapsed:.1f} sekund ({elapsed/60:.1f} minut)")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
