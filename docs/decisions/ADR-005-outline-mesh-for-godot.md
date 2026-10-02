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

## Ergänzung: Zentripetale Kurvensegmente mit Eckenschutz für SVG und Mesh (`fix/outline-curve-corners`)

Nach der adaptiven Mesh-Tessellierung (siehe oben) blieben sichtbare Knicke bestehen — auch direkt in der Game-SVG (in Illustrator geprüft). Die Ursache lag also nicht in der Abtastdichte des Mesh, sondern in der zugrunde liegenden Kurve selbst. Die vorherige Ergänzung dieser ADR, die adaptive Tessellierung erziele allein eine "sichtbar glatte Outline auch bei starkem Zoom", ist entsprechend zu relativieren: Sie reduzierte nur unnötig dichte Abtastung in ruhigen Kurvenabschnitten, behob aber nicht die Knicke selbst.

Korrektur/Ergänzung:

- `_closed_curve_segments()` ist jetzt die gemeinsame Quelle kubischer Bezier-Segmente für SVG-Pfad (`_closed_catmull_rom_svg_path()`) und Mesh-Ring (`_sample_closed_catmull_rom()`), damit beide Kurven nicht auseinanderlaufen.
- Zentripetale Catmull-Rom-Parametrisierung (`alpha=0.5`, chord-length-basierte Zeitparameter) statt uniformer Parametrisierung, mit vollen Tangenten (`tension=1.0`) statt der bisherigen Dämpfung (`0.44`).
- `_hard_corner_indices()` erkennt echte Ecken (Winkel ≥ 35° mit gerader Nachbarstützung, Geradheitsfehler ≤ 0.65 px über die benachbarten Abtastpunkte) und schützt sie vor dem Überglätten in `_smooth_closed_contour()` sowie vor dem Wegfallen in `_simplify_smooth_closed_contour()`; an diesen Ankern erhalten SVG- und Mesh-Segmente getrennte Ein-/Austrittstangenten. Eng gerundete, aber tatsächlich runde Spitzen werden weiterhin geglättet.
- Betrifft `coloring_game_export_v3` nicht strukturell: Binärformat `lcs_outline_mesh_v1`, Game JSON v3 und die Trennung `points`/`render_points` bleiben unverändert. Keine neue Architekturentscheidung.
- Visuell geprüft: einfache Formen (Kreis, Ellipse, Sechseck, Stern) sowie die rechte Blütenspitze des Hundemotivs (Illustrator 800 %, passendes Mesh in Godot); das Hundemotiv wurde vor dem Merge vom Projektinhaber geprüft. Nicht belegt: systematische Abnahme aller Zoomstufen und Motivtypen sowie ein Test bei genau 24-fachem Zoom. Weitere Motivtypen bleiben offene Qualitätssicherung.

### Diagnosebefund

Die sichtbare Formstörung steckte bereits in der exportierten SVG; Godot, MSAA und die Mesh-Abtastdichte waren nicht der Hebel. An der untersuchten Blütenspitze blieben nach der Vereinfachung wiederholt etwa 6 px zwischen Ankern, während die Richtung weiter wechselte. Der frühere Tangentenfaktor `0.44` bremste die Bezier-Kurve an diesen Ankern; vollere Tangenten glätteten den Verlauf sichtbar.

### Verworfene Alternativen (nicht erneut versuchen)

1. **Mesh-Fehlerbudget `0.005 px`** (statt `0.02 px`): keine erkennbare Verbesserung, da die Knicke in der Kurve selbst lagen. Nicht gemergt.
2. **Zentripetale Parametrisierung mit unverändertem Tangentenfaktor `0.44`:** an der Problemstelle (Blütenspitze, Illustrator 800 %) keine erkennbare Verbesserung.
3. **Pauschaler Eckenschutz** (jeder große Winkel wird zur harten Ecke): erzeugte am Hundemotiv einen künstlichen Dorn an der Blüte. Ersetzt durch den geradheitsabhängigen Eckenschutz (`_hard_corner_indices()`).

### Bekannte Grenzen

- Die Eckenerkennung nutzt feste geometrische Grenzen (Winkel `35°`, maximaler Geradheitsfehler `0.65 px` über die benachbarten Abtastpunkte). Bei anderen Motivgrößen und sehr kleinen Formen kann eine zusätzliche Prüfung nötig sein.

## Statushinweis

Verifiziert am 28.09.2026 gegen `coloring_region_extractor_gui.py` (`_outline_mesh_data()`, `_write_outline_mesh_binary()`, `export_game_json()`, `_closed_curve_segments()`, `_hard_corner_indices()`) und die Git-Historie: Die Implementierung ist auf `main` gemergt (PR #4, Commit `9c2dd17`; Ergänzungen PR #8, Commit `9b970b4`, und PR #10, Commit `09fbabd`), aber noch nicht Teil eines versionierten Releases.
