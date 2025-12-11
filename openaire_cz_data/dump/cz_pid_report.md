# CZ datasets in OpenAIRE with non-DOI PIDs

This page documents persistent identifier (PID) schemes used for datasets that are affiliated with Czech institutions in the OpenAIRE Graph, and highlights those datasets that only have non-DOI PIDs.

---

## Summary by PID scheme

Source: `cz_pid_scheme_stats_full_vs_dedup.csv`.

| pid_scheme | n_pids | n_affs | n_datasets_dedup | n_datasets_scheme_and_doi_dedup | n_datasets_non-doi_scheme_only |
|-----------:|-------:|-------:|-----------------:|--------------------------------:|-------------------------------:|
| doi       |  15 892 | 14 707 |           10 271 |                          10 271 |                              0 |
| handle    |     223 |    556 |              197 |                             179 |                             18 |
| mag_id    |      46 |     61 |               46 |                              46 |                              0 |
| pmid      |      11 |     25 |               11 |                               0 |                             11 |
| pmc       |       6 |     13 |                6 |                               0 |                              6 |
| pdb       |       5 |      9 |                5 |                               5 |                              0 |

Totals:

- number of CZ affiliation rows in `cz_dataset_aff` (full, with duplicates): **14 799**
- number of unique CZ datasets (distinct `dataset_id`): **10 315**

---

## Column descriptions

All counts are computed over datasets that have at least one affiliation to a Czech organisation (`cz_dataset_aff`), i.e. datasets that are related to at least one organisation with `country.code = 'CZ'` in the OpenAIRE Graph.

- **`pid_scheme`**  
  PID scheme as it appears in `dataset_pids.pid_scheme`, e.g. `doi`, `handle`, `pmid`, `pmc`, `pdb`, `mag_id`.

- **`n_pids`**  
  Number of PID rows in `dataset_pids` for the given `pid_scheme`, restricted to datasets that have at least one Czech affiliation. One row ≙ one `(dataset_id, pid_scheme, pid_value)` triple.

- **`n_affs`**  
  Number of affiliation rows (full, not deduplicated) for datasets that have at least one PID of the given scheme. Concretely: count of rows in `cz_dataset_aff` for all datasets that appear in `dataset_pids` with this `pid_scheme`. One row ≙ one `(dataset_id, CZ organisation)` pair.

- **`n_datasets_dedup`**  
  Number of **distinct datasets** that have at least one PID of the given scheme and at least one Czech affiliation. Each dataset is counted at most once per scheme, even if it has multiple PIDs of that scheme (e.g. multiple DOIs).

- **`n_datasets_scheme_and_doi_dedup`**  
  Number of **distinct datasets** that have at least one PID of the given `pid_scheme` *and* at least one DOI (`pid_scheme = 'doi'`), and at least one Czech affiliation.

- **`n_datasets_non-doi_scheme_only`**  
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

### Datasets with handle only (no DOI)

_Total: 18 CZ datasets with `handle` PIDs and no DOI._

- **IntUne Elite Survey Wave 1, January - July 2007** (2014-03-26)  
  OpenAIRE Dataset ID: [r313f0700742::b8f97bbbcea00b2f69101bd3ac2c5831](https://explore.openaire.eu/search/dataset?datasetId=r313f0700742::b8f97bbbcea00b2f69101bd3ac2c5831)  
  Handle(s): <https://hdl.handle.net/21.12137/NUOOIH>  
  CZ organisations (short): `AVCR`  
  CZ organisations (full): `Czech Academy of Sciences`  
  Repositories: [Lithuanian Data Archive for Social Sciences and Humanities (LiDA)](https://lida.dataverse.lt) – Data Repository

- **IntUne Elite Survey Wave 2, 2009** (2014-06-10)  
  OpenAIRE Dataset ID: [r313f0700742::20016f62863ec35aa7a133b6cadb9382](https://explore.openaire.eu/search/dataset?datasetId=r313f0700742::20016f62863ec35aa7a133b6cadb9382)  
  Handle(s): <https://hdl.handle.net/21.12137/TLO758>  
  CZ organisations (short): `AVCR`  
  CZ organisations (full): `Czech Academy of Sciences`  
  Repositories: [Lithuanian Data Archive for Social Sciences and Humanities (LiDA)](https://lida.dataverse.lt) – Data Repository

- **Supplementary data for article: Nikolić, S.; Ćirić, I.; Roller, A.; Lukeš, V.; Arion, V. B.; Grgurić-Šipka, S. Conversion of Hydrazides into: N, N ′-Diacylhydrazines in the Presence of a Ruthenium(II)-Arene Complex. New Journal of Chemistry 2017, 41 (14), 6857–6865. https://doi.org/10.1039/c7nj00965h** (2017-01-01)  
  OpenAIRE Dataset ID: [od______4206::cc4421a3803e4cc42e8cb4d95f6e92e3](https://explore.openaire.eu/search/dataset?datasetId=od______4206::cc4421a3803e4cc42e8cb4d95f6e92e3)  
  Handle(s): <https://hdl.handle.net/21.15107/rcub_cherry_3125>  
  CZ organisations (short): `ÚACH AV ČR`  
  CZ organisations (full): `Institute of Inorganic Chemistry`  
  Repositories: [Cherry - Repository of the Faculty of Chemistry, University of Belgrade](http://cherry.chem.bg.ac.rs/) – Institutional Repository

- **Supplementary data for article: Milenković, M. R.; Papastavrou, A. T.; Radanović, D. D.; Pevec, A.; Jagličić, Z.; Zlatar, M.; Gruden, M.; Vougioukalakis, G. C.; Turel, I.; Anđelković, K. K.; et al. Highly-Efficient N-Arylation of Imidazole Catalyzed by Cu(II) Complexes with Quaternary Ammonium-Functionalized 2-Acetylpyridine Acylhydrazone. Polyhedron 2019, 165, 22–30. https://doi.org/10.1016/j.poly.2019.03.001** (2019-01-01)  
  OpenAIRE Dataset ID: [od______4206::c5b586c15f0da48722b36378500dcdc9](https://explore.openaire.eu/search/dataset?datasetId=od______4206::c5b586c15f0da48722b36378500dcdc9)  
  Handle(s): <https://hdl.handle.net/21.15107/rcub_cherry_3006>  
  CZ organisations (short): `AVCR; Institute of Mathematics`  
  CZ organisations (full): `Czech Academy of Sciences; Institute of Mathematics`  
  Repositories: [Cherry - Repository of the Faculty of Chemistry, University of Belgrade](http://cherry.chem.bg.ac.rs/) – Institutional Repository

- **Supplementary data for article: Novakovic, M.; Bukvicki, D.; Andjelkovic, B.; Ilic-Tomic, T.; Veljic, M.; Tesevic, V.; Asakawa, Y. Cytotoxic Activity of Riccardin and Perrottetin Derivatives from the Liverwort Lunularia Cruciata. Journal of Natural Products 2019, 82 (4), 694–701. https://doi.org/10.1021/acs.jnatprod.8b00390** (2019-01-01)  
  OpenAIRE Dataset ID: [od______4206::f605791d1913783c86a837fd073cb654](https://explore.openaire.eu/search/dataset?datasetId=od______4206::f605791d1913783c86a837fd073cb654)  
  Handle(s): <https://hdl.handle.net/21.15107/rcub_cherry_3097>  
  CZ organisations (short): `AVCR; IMG; Institute of Botany`  
  CZ organisations (full): `Czech Academy of Sciences; Institute of Botany; Institute of Molecular Genetics`  
  Repositories: [Cherry - Repository of the Faculty of Chemistry, University of Belgrade](http://cherry.chem.bg.ac.rs/) – Institutional Repository

- **Supplementary data for the article: Perendija, J.; Veličković, Z. S.; Cvijetić, I.; Rusmirović, J. D.; Ugrinović, V.; Marinković, A. D.; Onjia, A. Batch and Column Adsorption of Cations, Oxyanions and Dyes on a Magnetite Modified Cellulose-Based Membrane. Cellulose 2020, 27 (14), 8215–8235. https://doi.org/10.1007/s10570-020-03352-x** (2020-01-01)  
  OpenAIRE Dataset ID: [od______4206::f4f93148d691be834443b9ed65ee0dcd](https://explore.openaire.eu/search/dataset?datasetId=od______4206::f4f93148d691be834443b9ed65ee0dcd)  
  Handle(s): <https://hdl.handle.net/21.15107/rcub_cherry_4205>  
  CZ organisations (short): `UO`  
  CZ organisations (full): `University of Defence`  
  Repositories: [Cherry - Repository of the Faculty of Chemistry, University of Belgrade](http://cherry.chem.bg.ac.rs/) – Institutional Repository

- **Mapa a tabulky půdních subtypů v české části povodí Labe pro model SWIM** (2022-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::008e72a8a311081ff48dc513ed3273b4](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::008e72a8a311081ff48dc513ed3273b4)  
  Handle(s): <http://hdl.handle.net/11104/0330643>  
  CZ organisations (short): `AVCR; Institute of Hydrodynamics; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Hydrodynamics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Raw data for the paper Molecular dynamics simulation trajectories dataset of a kinesin on tubulin heterodimers in electric field A2103** (2023-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::30f168f2acb5ce0bbc29f7288d2e5ed6](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::30f168f2acb5ce0bbc29f7288d2e5ed6)  
  Handle(s): <https://hdl.handle.net/11104/0343217>  
  CZ organisations (short): `AVCR; IPE; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Photonics and Electronics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Crystallographic data with embedded Jana2020 files. Analysis of magnetic structures in JANA2020** (2024-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::09cae70b54965a74c0653fa089380c61](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::09cae70b54965a74c0653fa089380c61)  
  Handle(s): <https://hdl.handle.net/11104/0354334>  
  CZ organisations (short): `AVCR; FZU; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Dataset for Microstructure and physical properties of black aluminum antireflective films.** (2024-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::224fd1bc4d6aedbf67a92962fd473658](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::224fd1bc4d6aedbf67a92962fd473658)  
  Handle(s): <https://hdl.handle.net/11104/0353281>  
  CZ organisations (short): `AVCR; FZU; IPP; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics; Institute of Plasma Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Dataset for Growth and Spectroscopic Properties of Pr.sup.3+./sup.-Doped Lu.sub.2./sub.S.sub.3./sub. Single\nCrystals** (2024-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::95f8a18859f447801664bedba69b5d6b](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::95f8a18859f447801664bedba69b5d6b)  
  Handle(s): <https://hdl.handle.net/11104/0353698>  
  CZ organisations (short): `AVCR; FZU; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Dataset for Silver oxide phase tailoring for improved antimicrobial activity** (2024-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::9ba72f9af78ab1c21500388cfea52f15](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::9ba72f9af78ab1c21500388cfea52f15)  
  Handle(s): <https://hdl.handle.net/11104/0353279>  
  CZ organisations (short): `AVCR; FZU; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Data for plots in Experimental photon addition and subtraction in multi-mode and entangled optical fields (Optics Letters (2024))** (2024-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::d204f964d89fca4476ece52e9d4ff3af](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::d204f964d89fca4476ece52e9d4ff3af)  
  Handle(s): <https://hdl.handle.net/11104/0354687>  
  CZ organisations (short): `AVCR; FZU; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **DATASET for "Adapting the LIF detection setup of the standard CE equipment to achieve high-sensitivity detection of 2-aminoacridone-labeled oligosaccharides"** (2025-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::0c7329bcf90315cd93b40ef405866e31](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::0c7329bcf90315cd93b40ef405866e31)  
  Handle(s): <https://hdl.handle.net/11104/0364166>  
  CZ organisations (short): `AVCR; IAC; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Analytical Chemistry`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **DATASET for "Sensitive profiling of human milk oligosaccharides in human colostrum and breast milk by capillary electrophoresis-mass spectrometry".** (2025-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::632265ad65f46d10d53398860fbd556b](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::632265ad65f46d10d53398860fbd556b)  
  Handle(s): <https://hdl.handle.net/11104/0368676>  
  CZ organisations (short): `AVCR; IAC; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Analytical Chemistry`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Data for arxiv_Aerospace 2024** (2025-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::695e29cb4c51a2fb8a24ccc9d8355d1b](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::695e29cb4c51a2fb8a24ccc9d8355d1b)  
  Handle(s): <https://hdl.handle.net/11104/0369212>  
  CZ organisations (short): `AVCR; FZU; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Physics`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Measurement of carbonic anhydrase inhibition by steroidal O-sulfamates** (2025-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::8246c196a6b7dec4b3ae8a2d5129dbb8](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::8246c196a6b7dec4b3ae8a2d5129dbb8)  
  Handle(s): <https://hdl.handle.net/11104/0368275>  
  CZ organisations (short): `AVCR; IOCB; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Institute of Organic Chemistry and Biochemistry`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

- **Data - Evaluating the AgMIP calibration protocol for crop models; case study and new diagnostic tests** (2025-01-01)  
  OpenAIRE Dataset ID: [r38615271ce1::ceadff78589b51301c9fbd40ad3834f1](https://explore.openaire.eu/search/dataset?datasetId=r38615271ce1::ceadff78589b51301c9fbd40ad3834f1)  
  Handle(s): <https://hdl.handle.net/11104/0367784>  
  CZ organisations (short): `AVCR; GCC; KNAV`  
  CZ organisations (full): `Academy of Sciences Library; Czech Academy of Sciences; Global Change Research Centre`  
  Repositories: [ASEP Repository](https://asep-portal.lib.cas.cz/basic-information/dataset-repository/) – Data Repository

### Datasets with PMID only (no DOI)

_Total: 11 CZ datasets with `pmid` PIDs and no DOI._

PMID values are linked to PubMed using the pattern <https://pubmed.ncbi.nlm.nih.gov/PMID/>.

- **Repetitive transcranial stimulation for freezing of gait in Parkinson's disease.** (2007-10-03)  
  OpenAIRE Dataset ID: [pmid________::0e8323a89184553e4ee5a55ca87a45a7](https://explore.openaire.eu/search/dataset?datasetId=pmid________::0e8323a89184553e4ee5a55ca87a45a7)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/17516472/>  
  CZ organisations (short): `MU`  
  CZ organisations (full): `Masaryk University`  
  Repositories: Unknown Repository – Publication Repository

- **TOPICAL CORTICOSTEROIDS BUT NOT CALCINEURIN INHIBITORS INDUCED ATROPHY AFTER FOUR WEEKS.** (2015-11-16)  
  OpenAIRE Dataset ID: [pmid________::422552f150d0db4b16ce976465482282](https://explore.openaire.eu/search/dataset?datasetId=pmid________::422552f150d0db4b16ce976465482282)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/26403410/>  
  CZ organisations (short): `Charles University`  
  CZ organisations (full): `Charles University`  
  Repositories: Unknown Repository – Publication Repository

- **Fine tuning of surface CRLF2 expression and its associated signaling profile in childhood B-cell precursor acute lymphoblastic leukemia.** (2016-02-12)  
  OpenAIRE Dataset ID: [pmid________::3ae470aea0c87c521af6cc1e227cd970](https://explore.openaire.eu/search/dataset?datasetId=pmid________::3ae470aea0c87c521af6cc1e227cd970)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/25862705/>  
  CZ organisations (short): `Charles University`  
  CZ organisations (full): `Charles University`  
  Repositories: Unknown Repository – Publication Repository

- **Clinical outcome of transcatheter treatment of heart failure with preserved or mildly reduced ejection fraction using a novel implant.** (2016-02-25)  
  OpenAIRE Dataset ID: [pmid________::f817fe31e50b212377e1dd55de372f90](https://explore.openaire.eu/search/dataset?datasetId=pmid________::f817fe31e50b212377e1dd55de372f90)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/25841123/>  
  CZ organisations (short): `Ministry of Health; Na Homolce Hospital`  
  CZ organisations (full): `Ministry of Health; Na Homolce Hospital`  
  Repositories: Unknown Repository – Publication Repository

- **Efficacy of P2Y12 receptor antagonists in patients with atrial fibrillation according to the CHA2DS2VASc score.** (2016-12-13)  
  OpenAIRE Dataset ID: [pmid________::b69dedc5de89b58566b86b7a565f7f3f](https://explore.openaire.eu/search/dataset?datasetId=pmid________::b69dedc5de89b58566b86b7a565f7f3f)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/26797336/>  
  CZ organisations (short): `Charles University; FNKV; Ministry of Health; SZU`  
  CZ organisations (full): `Charles University; Fakultní nemocnice Královské Vinohrady; Ministry of Health; National Institute of Public Health`  
  Repositories: Unknown Repository – Publication Repository

- **Rituximab maintenance significantly prolongs progression-free survival of patients with newly diagnosed mantle cell lymphoma treated with the Nordic MCL2 protocol and autologous stem cell transplantation.** (2019-11-25)  
  OpenAIRE Dataset ID: [pmid________::434b6aaec69c57587bafca9b387d59d1](https://explore.openaire.eu/search/dataset?datasetId=pmid________::434b6aaec69c57587bafca9b387d59d1)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/30474171/>  
  CZ organisations (short): `Charles University; MU; Palacký University, Olomouc; University Hospital Olomouc`  
  CZ organisations (full): `Charles University; Masaryk University; Palacký University, Olomouc; University Hospital Olomouc`  
  Repositories: Unknown Repository – Publication Repository

- **Long-term treatment results of Polish pediatric and adolescent patients enrolled in the ALL IC-BFM 2002 trial.** (2020-03-26)  
  OpenAIRE Dataset ID: [pmid________::f0bb79901320c25b0267b6861930658a](https://explore.openaire.eu/search/dataset?datasetId=pmid________::f0bb79901320c25b0267b6861930658a)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/31432528/>  
  CZ organisations (short): `Charles University; University Hospital in Motol`  
  CZ organisations (full): `Charles University; University Hospital in Motol`  
  Repositories: Unknown Repository – Publication Repository

- **Long-term follow up of pediatric Philadelphia positive acute lymphoblastic leukemia treated with the EsPhALL2004 study: high white blood cell count at diagnosis is the strongest prognostic factor.** (2020-06-15)  
  OpenAIRE Dataset ID: [pmid________::114423b20d2641a0a80ca178f9675f87](https://explore.openaire.eu/search/dataset?datasetId=pmid________::114423b20d2641a0a80ca178f9675f87)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/30213832/>  
  CZ organisations (short): `University Hospital in Motol`  
  CZ organisations (full): `University Hospital in Motol`  
  Repositories: Unknown Repository – Publication Repository

- **Successful early treatment combining remdesivir with high-titer convalescent plasma among COVID-19-infected hematological patients.** (2021-12-14)  
  OpenAIRE Dataset ID: [pmid________::60771a5dd35052f127c28a112a589a28](https://explore.openaire.eu/search/dataset?datasetId=pmid________::60771a5dd35052f127c28a112a589a28)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/34396566/>  
  CZ organisations (short): `BC; JČU; MU; University Hospital Brno; VRI`  
  CZ organisations (full): `Biology Centre; Masaryk University; University Hospital Brno; University of South Bohemia in České Budějovice; Veterinary Research Institute`  
  Repositories: Unknown Repository – Publication Repository

- **Kinetics of anti-SARS-CoV-2 neutralizing antibodies development after BNT162b2 vaccination in patients with amyloidosis and the impact of therapy.** (2021-12-27)  
  OpenAIRE Dataset ID: [pmid________::2c97baf40c753ce5b0287105b6258036](https://explore.openaire.eu/search/dataset?datasetId=pmid________::2c97baf40c753ce5b0287105b6258036)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/34778995/>  
  CZ organisations (short): `SEVEN; Seven`  
  CZ organisations (full): `SEVEN, THE ENERGY EFFICIENCY CENTER Z.U.; Seven`  
  Repositories: Unknown Repository – Publication Repository

- **COVID-19 in vaccinated adult patients with hematological malignancies: preliminary results from EPICOVIDEHA.** (2022-03-21)  
  OpenAIRE Dataset ID: [pmid________::e359ef59404e0a39d48d4e9235a1f28a](https://explore.openaire.eu/search/dataset?datasetId=pmid________::e359ef59404e0a39d48d4e9235a1f28a)  
  PMID(s): <https://pubmed.ncbi.nlm.nih.gov/34748627/>  
  CZ organisations (short): `MU; University Hospital Brno`  
  CZ organisations (full): `Masaryk University; University Hospital Brno`  
  Repositories: Unknown Repository – Publication Repository

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
