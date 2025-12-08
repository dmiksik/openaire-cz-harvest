#!/bin/bash
# verify_search_criteria.sh

FILE="openaire_cz_dataset_20251207_142716.json"

echo "=================================================================="
echo "Ověření kritérií vyhledávání v datech"
echo "=================================================================="
echo

# 1. TYPE - měly by být všechny "dataset"
echo "📊 1. TYPY ZÁZNAMŮ (měly by být jen 'dataset'):"
echo "------------------------------------------------------------------"
jq -r '.records[].type' "$FILE" | sort | uniq -c | sort -rn
echo

# 2. COUNTRIES - kde se projevuje "CZ"?
echo "📊 2. ZEMĚ V POLI 'countries':"
echo "------------------------------------------------------------------"
echo "Záznamy s neprázdným polem countries:"
jq '[.records[] | select(.countries != null)] | length' "$FILE"
echo
echo "Unikátní kódy zemí v poli countries:"
jq -r '.records[].countries[]?.code' "$FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10
echo

# 3. ORGANIZATIONS - české instituce
echo "📊 3. ORGANIZACE (české instituce):"
echo "------------------------------------------------------------------"
echo "Záznamy s organizacemi:"
jq '[.records[] | select(.organizations != null and (.organizations | length > 0))] | length' "$FILE"
echo
echo "Top 10 organizací:"
jq -r '.records[].organizations[]?.legalName' "$FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10
echo

# 4. PUBLICATION DATE - časové rozmezí
echo "📊 4. DATUM PUBLIKACE:"
echo "------------------------------------------------------------------"
echo "Roky publikací (top 20):"
jq -r '.records[].publicationDate' "$FILE" | cut -d'-' -f1 | sort | uniq -c | sort -rn | head -20
echo
echo "Nejstarší a nejmladší:"
echo "  Nejstarší: $(jq -r '.records[].publicationDate' "$FILE" | sort | head -1)"
echo "  Nejmladší: $(jq -r '.records[].publicationDate' "$FILE" | sort | tail -1)"
echo

# 5. COLLECTED FROM - zdroje dat
echo "📊 5. ZDROJE DAT (collectedFrom):"
echo "------------------------------------------------------------------"
jq -r '.records[].collectedFrom[]?.value' "$FILE" | sort | uniq -c | sort -rn | head -10
echo

# 6. COMMUNITIES - komunity
echo "📊 6. KOMUNITY:"
echo "------------------------------------------------------------------"
jq -r '.records[].communities[]?.label' "$FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10
echo

# 7. Jak se pozná "CZ" spojení?
echo "📊 7. JAK OPENAIRE URČUJE 'CZ' SPOJENÍ:"
echo "------------------------------------------------------------------"
echo "Možné indikátory českého původu:"
echo
echo "a) Pole 'countries' obsahuje CZ:"
jq '[.records[] | select(.countries != null and (.countries | map(.code) | any(. == "CZ")))] | length' "$FILE"
echo
echo "b) Organizace s CZ v názvu/ID:"
jq '[.records[] | select(.organizations != null and (.organizations | map(.legalName // "" | test("Czech|Česk|Praha|Brno|Masaryk|Charles University")) | any))] | length' "$FILE"
echo
echo "c) Publisher obsahuje české instituce:"
jq -r '.records[].publisher' "$FILE" | grep -i "czech\|česk\|praha\|brno\|masaryk" | sort | uniq -c | sort -rn | head -10
echo

echo "=================================================================="
echo "VYSVĚTLENÍ:"
echo "------------------------------------------------------------------"
echo "OpenAIRE určuje 'countryCode=CZ' na základě:"
echo "  1. Afiliací autorů (organizations)"
echo "  2. Explicitního pole 'countries' (pokud je vyplněno)"
echo "  3. Metadata od poskytovatelů dat (collectedFrom)"
echo "  4. Projektů s českým financováním"
echo "=================================================================="
