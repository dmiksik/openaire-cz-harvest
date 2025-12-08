#!/bin/bash
# generate_markdown_table.sh

FILE="openaire_cz_dataset_20251207_142716.json"
OUTPUT="non_doi_records_table.md"

echo "# Záznamy s non-DOI PID" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "Celkem záznamů: **$(jq '[.records[] | select(.pids != null and (.pids | map(.scheme) | any(. != "doi")))] | length' "$FILE")**" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Širší tabulka s CSS styling
cat >> "$OUTPUT" << 'EOL'
<style>
table {
  width: 100%;
  table-layout: fixed;
}
th:nth-child(1) { width: 30%; }  /* Title */
th:nth-child(2) { width: 10%; }  /* Date */
th:nth-child(3) { width: 15%; }  /* Publisher */
th:nth-child(4) { width: 12%; }  /* Schemes */
th:nth-child(5) { width: 33%; }  /* URLs */
td {
  word-wrap: break-word;
  vertical-align: top;
}
</style>

EOL

echo "| Title | Publication Date | Publisher | PID Schemes | URLs |" >> "$OUTPUT"
echo "|-------|------------------|-----------|-------------|------|" >> "$OUTPUT"

jq -r '.records[] | 
  select(.pids != null and (.pids | map(.scheme) | any(. != "doi"))) | 
  {
    title: (.mainTitle // "N/A" | gsub("\\|"; "\\\\|") | .[0:200]),
    date: (.publicationDate // "N/A"),
    publisher: (.publisher // "N/A" | gsub("\\|"; "\\\\|") | .[0:100]),
    schemes: ([.pids[].scheme] | unique | sort | join(", ")),
    urls: (
      [.instances[]?.urls[]?] | 
      unique | 
      if length > 0 then
        [.[0:5] | .[] | "<\(.)>"] | join("<br>") +
        (if length > 5 then "<br>*...a další \(length - 5)*" else "" end)
      else
        "N/A"
      end
    )
  } | 
  "| \(.title) | \(.date) | \(.publisher) | \(.schemes) | \(.urls) |"
' "$FILE" >> "$OUTPUT"

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "*Vygenerováno ze souboru: $FILE*" >> "$OUTPUT"

echo "✓ Markdown tabulka uložena do: $OUTPUT"
echo "  Pro zobrazení v prohlížeči: pandoc $OUTPUT -o ${OUTPUT%.md}.html && firefox ${OUTPUT%.md}.html"
