#!/bin/bash
# detailed_pid_analysis.sh

FILE="openaire_cz_dataset_20251207_142716.json"

echo "==================================================================="
echo "Detailní analýza PID kombinací"
echo "==================================================================="
echo

# Celkový počet záznamů
TOTAL=$(jq '.records | length' "$FILE")
echo "📊 Celkem záznamů: $TOTAL"
echo

# 1. Statistika jednotlivých PID (co jsi už viděl)
echo "📈 Statistika všech PID (každý PID počítán zvlášť):"
echo "-------------------------------------------------------------------"
jq -r '.records[].pids[]?.scheme' "$FILE" | sort | uniq -c | sort -rn
echo

# 2. Záznamy POUZE s non-DOI (bez DOI)
echo "🔍 Záznamy POUZE s non-DOI (nemají žádný DOI):"
echo "-------------------------------------------------------------------"
jq -r '.records[] | 
  select(.pids != null and (.pids | map(.scheme) | all(. != "doi"))) | 
  .pids[].scheme' "$FILE" | sort | uniq -c | sort -rn

ONLY_NON_DOI=$(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | all(. != "doi")))] | length' "$FILE")
echo "Celkem záznamů POUZE s non-DOI: $ONLY_NON_DOI"
echo

# 3. Záznamy s DOI + něco dalšího
echo "📊 Záznamy s DOI + další PID:"
echo "-------------------------------------------------------------------"
WITH_DOI_AND_OTHER=$(jq '[.records[] | 
  select(.pids != null and 
         (.pids | map(.scheme) | any(. == "doi")) and 
         (.pids | length > 1))] | length' "$FILE")
echo "Záznamy s DOI + další PID: $WITH_DOI_AND_OTHER"
echo

# 4. Kombinace PID
echo "📋 Nejčastější kombinace PID:"
echo "-------------------------------------------------------------------"
jq -r '.records[] | 
  select(.pids != null) | 
  [.pids[].scheme] | sort | join(", ")' "$FILE" | 
  sort | uniq -c | sort -rn | head -20

echo
echo "==================================================================="
echo "SHRNUTÍ:"
echo "-------------------------------------------------------------------"
echo "Celkem záznamů: $TOTAL"
echo "Záznamy POUZE s DOI: $(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | all(. == "doi")) and (.pids | length == 1))] | length' "$FILE")"
echo "Záznamy s více DOI: $(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | all(. == "doi")) and (.pids | length > 1))] | length' "$FILE")"
echo "Záznamy s DOI + non-DOI: $WITH_DOI_AND_OTHER"
echo "Záznamy POUZE s non-DOI: $ONLY_NON_DOI"
echo "Záznamy bez žádného PID: $(jq '[.records[] | select(.pids == null or (.pids | length == 0))] | length' "$FILE")"
echo "==================================================================="
