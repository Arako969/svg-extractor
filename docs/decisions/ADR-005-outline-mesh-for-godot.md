# ADR-005: Trianguliertes Vektor-Outline-Mesh für Godot

Status: Akzeptiert und umgesetzt (auf `main` gemergt, PR #4 „Vektor-Outline-Mesh und Render-Geometrie für Godot“, Commit `9c2dd17`, 2026-09-19). Noch nicht Teil eines versionierten Releases (`VERSION`/`CHANGELOG.md` stehen weiterhin auf `v0.11.0`).

## Kontext

Godot soll die geglättete Vektor-Outline nicht aus SVG-Pfaden parsen müssen (siehe ADR-003). Für ein performantes, direkt renderbares Outline-Mesh wird eine echte 2D-Dreiecksgeometrie benötigt, die auch Löcher — etwa durch verschachtelte Konturen — korrekt abbildet.

Gleichzeitig soll die exakte Gameplay-/Hit-Test-Geometrie einer Region (`points`) von der visuellen Füllgeometrie mit Outline-Überdeckung getrennt bleiben, die der SVG-Export bereits für sichtbare Fills verwendet.

## Entscheidung

Beim Export von Game JSON v3 (`export_game_json()`) wird zusätzlich ein trianguliertes Outline-Mesh als kompaktes Binärformat geschrieben:

- Format `lcs_outline_mesh_v1`, Dateiendung `.meshbin`, abgelegt als `<json-stem>_outline.meshbin` neben dem Game JSON.
- Die Triangulierung nutzt dieselbe geglättete Konturquelle wie der SVG-Outline-Export (Signed-Distance-Feld, Resampling, Glättung, Catmull-Rom-Sampling), baut daraus über die OpenCV-Konturhierarchie Polygone mit Löchern (`_outline_mesh_rings()`, `_outline_mesh_data()`) und trianguliert sie mit Shapely (`constrained_delaunay_triangles`, `make_valid`).
- Die neue Abhängigkeit **`shapely`** ist dafür erforderlich (in `requirements.txt` ergänzt).

Zusätzlich exportiert Game JSON v3 pro Region `render_points`: dieselbe visuelle Füllgeometrie mit Outline-Überdeckung (`_svg_fill_points_with_outline_bleed`, `bleed_px=3`), die bereits der SVG-Export verwendet — getrennt von der exakten Gameplay-/Hit-Test-Geometrie (`points`).

## Konsequenzen

- Godot kann die Outline als echtes Dreiecksmesh rendern, ohne SVG-Pfade zu parsen.
- Fehlt `shapely` oder schlägt die Triangulierung fehl, wird das Game JSON trotzdem gespeichert; `outline_mesh` ist dann `null` und die GUI zeigt eine Warnung.
- `render_points` und `points` sind bewusst getrennt: Die Gameplay-Hit-Test-Geometrie bleibt unverändert exakt, während die visuelle Füllung weiterhin kontrolliert unter die Outline reicht.
- Die Extractor-UI/-Logik selbst ändert sich nicht; es wird nur zusätzliche, bereits im Speicher vorhandene Geometrie strukturiert exportiert.

## Ergänzung: Adaptive Tessellierung der Mesh-Kontur (`fix/adaptive-outline-mesh`)

Die für die Triangulierung verwendete Catmull-Rom-Kontur (`_outline_mesh_rings()`) wurde nicht mehr mit einer festen Schrittzahl pro Kurvensegment abgetastet, sondern über `_sample_cubic_bezier_adaptive()` fehlerbasiert (De-Casteljau-Verfahren, Fehlerbudget `0.02 px`, maximale Tiefe `16`). Grund: Die feste Abtastung erzeugte bei starkem Zoom (bis 24-fach) sichtbare Polygonkanten, während ruhige Kurvenabschnitte unnötig dicht abgetastet wurden. Dies ist keine neue Architekturentscheidung, sondern eine Verfeinerung des in dieser ADR beschriebenen Mesh-Erzeugungsschritts; die grundsätzliche Entscheidung (trianguliertes Binärformat, Trennung von `points`/`render_points`) bleibt unverändert. Der SVG-Outline-Export ist davon nicht betroffen.

## Statushinweis

Verifiziert am 27.09.2026 gegen `coloring_region_extractor_gui.py` (`_outline_mesh_data()`, `_write_outline_mesh_binary()`, `export_game_json()`) und die Git-Historie: die Implementierung ist auf `main` gemergt (Commit `9c2dd17`), aber noch nicht Teil eines versionierten Releases.
