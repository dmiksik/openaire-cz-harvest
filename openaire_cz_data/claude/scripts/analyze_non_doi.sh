#!/bin/bash
# analyze_non_doi.sh

FILE="../openaire_cz_dataset_20251207_142716.json"

echo "==================================================================="
echo "Analýza PID schémat v souboru: $FILE"
echo "==================================================================="
echo

# Celkový počet záznamů
TOTAL=$(jq '.records | length' "$FILE")
echo "📊 Celkem záznamů: $TOTAL"
echo

# Statistika všech schémat
echo "📈 Statistika PID schémat (scheme):"
echo "-------------------------------------------------------------------"
jq -r '.records[].pids[]?.scheme' "$FILE" | sort | uniq -c | sort -rn
echo

# Počet záznamů s non-DOI PID
NON_DOI=$(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | any(. != "doi")))] | length' "$FILE")
echo "🔍 Záznamy s non-DOI PID: $NON_DOI"
echo

# Export non-DOI záznamů
OUTPUT="..//non_doi_pids.json"
jq '{
  metadata: .metadata,
  records: [
    .records[] | 
    select(.pids != null and (.pids | map(.scheme) | any(. != "doi")))
  ]
}' "$FILE" > "$OUTPUT"

echo "💾 Záznamy s non-DOI PID uloženy do: $OUTPUT"
echo

# Ukázat příklady non-DOI záznamů
echo "📋 Příklady non-DOI záznamů (prvních 5):"
echo "-------------------------------------------------------------------"
jq -r '.records[] | 
  select(.pids != null and (.pids | map(.scheme) | any(. != "doi"))) | 
  "\(.id)\n  Title: \(.mainTitle)\n  PIDs: \(.pids | map("\(.scheme): \(.value)") | join(", "))\n"
' "$FILE" | head -n 20

echo "==================================================================="
