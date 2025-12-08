#!/bin/bash
# generate_markdown_table_enhanced.sh

FILE="../openaire_cz_dataset_20251207_142716.json"
OUTPUT="../non_doi_records_table.md"

echo "Generuji tabulku..."

# Úvodní hlavička
cat > "$OUTPUT" << 'EOL'
# Záznamy s non-DOI PID

## 📊 Souhrnná statistika

EOL

# Spočítat statistiky
TOTAL=$(jq '.records | length' "$FILE")
ONLY_DOI=$(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | all(. == "doi")))] | length' "$FILE")
WITH_NON_DOI=$(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | any(. != "doi")))] | length' "$FILE")
NO_PID=$(jq '[.records[] | select(.pids == null or (.pids | length == 0))] | length' "$FILE")

# Souhrnná tabulka
cat >> "$OUTPUT" << EOL
| Kategorie | Počet | % |
|-----------|-------|---|
| **Celkem záznamů** | $TOTAL | 100.0% |
| Pouze DOI | $ONLY_DOI | $(awk "BEGIN {printf \"%.1f\", ($ONLY_DOI/$TOTAL)*100}")% |
| **S non-DOI PID** | **$WITH_NON_DOI** | **$(awk "BEGIN {printf \"%.1f\", ($WITH_NON_DOI/$TOTAL)*100}")**% |
| Bez PID | $NO_PID | $(awk "BEGIN {printf \"%.1f\", ($NO_PID/$TOTAL)*100}")% |

## 📋 Kombinace PID schémat

EOL

# Tabulka kombinací
echo "| Kombinace | Počet |" >> "$OUTPUT"
echo "|-----------|-------|" >> "$OUTPUT"

jq -r '.records[] | 
  select(.pids != null) | 
  [.pids[].scheme] | sort | unique | join(", ")' "$FILE" | 
  sort | uniq -c | sort -rn | 
  awk '{count=$1; $1=""; combo=$0; gsub(/^ /, "", combo); printf "| %s | %d |\n", combo, count}' >> "$OUTPUT"

# Statistika jednotlivých schémat
cat >> "$OUTPUT" << 'EOL'

## 🔍 Jednotlivá PID schémata

| Schéma | Počet výskytů |
|--------|---------------|
EOL

jq -r '.records[].pids[]?.scheme' "$FILE" | 
  sort | uniq -c | sort -rn | 
  awk '{printf "| %s | %d |\n", $2, $1}' >> "$OUTPUT"

# Hlavní tabulka
cat >> "$OUTPUT" << 'EOL'

---

## 📄 Detailní seznam záznamů s non-DOI PID

<style>
table {
  width: 100%;
  table-layout: fixed;
}
td {
  word-wrap: break-word;
  vertical-align: top;
  padding: 8px;
}
.url-row {
  background-color: #f5f5f5;
  font-size: 0.9em;
}
.url-row td {
  padding: 12px;
}
</style>

| Title | Date | Publisher | PID Schemes |
|-------|------|-----------|-------------|
EOL

# Generovat záznamy s dvěma řádky
jq -r '.records[] | 
  select(.pids != null and (.pids | map(.scheme) | any(. != "doi"))) | 
  {
    title: (.mainTitle // "N/A" | gsub("\\|"; "\\\\|") | gsub("\n"; " ")),
    date: (.publicationDate // "N/A"),
    publisher: (.publisher // "N/A" | gsub("\\|"; "\\\\|") | gsub("\n"; " ")),
    schemes: ([.pids[].scheme] | unique | sort | join(", ")),
    urls: ([.instances[]?.urls[]?] | unique)
  } | 
  # První řádek s daty
  "| \(.title) | \(.date) | \(.publisher) | \(.schemes) |",
  # Druhý řádek s URL
  "| <div class=\"url-row\">**URLs:**<br>" + 
  (if (.urls | length) > 0 then 
    (.urls | map("• <\(.)>") | join("<br>"))
  else 
    "*Žádné URL*" 
  end) + 
  "</div> ||||"
' "$FILE" >> "$OUTPUT"

# Závěr
cat >> "$OUTPUT" << EOL

---

*Vygenerováno ze souboru: \`$FILE\`*

*Datum: $(date '+%Y-%m-%d %H:%M:%S')*
EOL

echo "✓ Tabulka uložena do: $OUTPUT"
echo ""
echo "Pro zobrazení v prohlížeči:"
echo "  pandoc $OUTPUT -s -o ${OUTPUT%.md}.html -c https://cdn.jsdelivr.net/npm/water.css@2/out/water.css"
echo "  firefox ${OUTPUT%.md}.html"
