# Projektstatus

Letzte Migration der Dokumentation: 27.09.2026
Letzte Verifikation gegen Quellcode und Git-Historie: 27.09.2026 (PR #5–#8)

## Aktueller Release (VERSION / CHANGELOG)

`v0.11.0`

## Stand auf `main` (verifiziert)

`main` enthält gegenüber dem Tag `v0.11.0` bereits vier weitere gemergte Arbeitseinheiten, die noch nicht versioniert bzw. veröffentlicht wurden (eine davon, PR #6, ist reine Testinfrastruktur ohne Versionsrelevanz):

1. **Game Export v3** (PR #3, Commit `bcc13d9`, gemergt 2026-09-18).
2. **Vektor-Outline-Mesh & Render-Geometrie für Godot** (PR #4, Commit `9c2dd17`, gemergt 2026-09-19).
3. **Outline-Mesh mit automatisierten Geometrietests abgesichert** (PR #6, Commit `4073709`, gemergt 2026-09-27): `tests/test_outline_mesh_geometry.py` sowie ein GitHub-Actions-Workflow (`.github/workflows/tests.yml`), der diese Tests bei Push/PR auf `main` ausführt. Keine Änderung an `coloring_region_extractor_gui.py`; reine Testinfrastruktur, keine Versionsrelevanz.
4. **Outline-Mesh adaptiv tessellieren** (PR #8, Commit `9b970b4`, gemergt 2026-09-27): ersetzt die feste Schrittabtastung der Catmull-Rom-Segmente im Outline-Mesh durch adaptive, fehlerbasierte De-Casteljau-Tessellierung (`_sample_cubic_bezier_adaptive`, Fehlerbudget `0.02 px`, max. Tiefe `16`), damit die Outline auch bei starkem Zoom (bis 24-fach) glatt bleibt. Betrifft nur das triangulierte Godot-Outline-Mesh, nicht den SVG-Export. Testsuite auf 7 Tests erweitert. Der laut Branch-Dokumentation vor dem Merge vorgesehene manuelle visuelle Test (Hundemotiv, Godot-VectorColoringTest, 24-facher Zoom) lässt sich aus dem Repository allein nicht verifizieren.

Alle vier sind vollständig im Code auf `main` vorhanden; es existiert kein offener Feature-Branch mehr dafür. `VERSION` und `CHANGELOG.md` wurden für die produktrelevanten Änderungen (1, 2, 4) noch nicht aktualisiert; eine Versionsentscheidung steht noch aus (siehe `GIT_WORKFLOW.md`, Abschnitt Release: nur auf ausdrückliche Entscheidung).

## Aktueller Entwicklungszweig

`main`. Es existiert aktuell kein offener Feature-Branch in diesem Repository.

## Projektziel

Der Coloring Region Extractor ist ein Desktop-Werkzeug zur Vorbereitung schwarz-weißer Coloring-Book-Illustrationen für ein späteres Malen-nach-Zahlen-System in Godot. Optional kann eine kolorierte Referenzversion verwendet werden, um Ziel-Farben und Farb-IDs abzuleiten.

Die Pipeline soll aus einer Illustration technische Regionen erzeugen, Korrekturen und Gruppierungen ermöglichen und anschließend spielbare Game Areas für Godot exportieren.

## Aktuelle Kernarchitektur

- Technische Region und Game Area sind getrennte Konzepte.
- Eine Game Area kann aus mehreren technischen Regionen bestehen.
- Die Regionserkennung basiert auf Bildverarbeitung und Connected Components.
- Zusätzliche Regionstypen ergänzen die Standarderkennung: Mikroregionen, farbbasierte Unterregionen, Recovery-Regionen und manuell ergänzte Regionen.
- Farben werden optional aus einer Referenzvorlage abgeleitet und auf eine reduzierte Palette abgebildet.
- Der SVG-Export enthält getrennte Ebenen für Game Areas und die visuelle Outline.
- Game JSON v3 (`coloring_game_export_v3`, auf `main` gemergt) stellt Gameplay-Geometrie (`points`), visuelle Füllgeometrie mit Outline-Überdeckung (`render_points`) sowie die vollständige Game-Area-Struktur explizit bereit, damit Godot für die Spiellogik keine SVG-Pfade parsen muss.
- Zusätzlich erzeugt der Game-JSON-Export ein trianguliertes, binäres Vektor-Outline-Mesh (`*_outline.meshbin`, Format `lcs_outline_mesh_v1`) für Godot, sofern die optionale Abhängigkeit `shapely` installiert ist.

## Veröffentlicht und abgeschlossen (Stand CHANGELOG/VERSION `v0.11.0`)

- Regionserkennung und Grundeditor
- Bildrand als optionale Grenze
- Mehrfachauswahl und Game Areas
- Projektworkflow
- Farbvorlage, Palette und Farb-IDs
- Farbbasierte Unterregionen
- Adaptive Mikroregionen
- Farbbasierte Wiederherstellung
- Manuelles Ergänzen fehlender Flächen
- Zoom und dreigeteilte Oberfläche
- SVG-Outline-Export mit separater Vektor-Outline, Glättung, kontrollierter Fill-Überdeckung und einstellbarer Pixel-Toleranz (`v0.11.0`)

## Auf `main` gemergt, aber noch nicht versioniert/released

- **Game Export v3**: explizite Gameplay-Geometrie (`regions[].points`) und einheitliche Game-Area-Struktur (`game_areas`, inklusive impliziter Ein-Region-Game-Areas über `is_implicit`) im Game JSON.
- **Render-Geometrie**: `regions[].render_points` mit derselben Outline-Überdeckung (`bleed_px=3`), die der SVG-Export verwendet.
- **Vektor-Outline-Mesh**: trianguliertes Binärformat `*_outline.meshbin` (`lcs_outline_mesh_v1`) für Godot, benötigt `shapely`; bei fehlender Abhängigkeit wird das Game JSON dennoch gespeichert (`outline_mesh: null`, Warnhinweis in der GUI). Seit PR #8 mit fehlerbasierter adaptiver Tessellierung (`_sample_cubic_bezier_adaptive`, Fehlerbudget `0.02 px`) statt fester Schrittabtastung.
- **Automatisierte Geometrietests** (PR #6, nicht versionsrelevant): `tests/test_outline_mesh_geometry.py` (7 Tests) und GitHub-Actions-Workflow `.github/workflows/tests.yml` bei Push/PR auf `main`.

Details: `systems/EXPORT_PIPELINE.md`, `decisions/ADR-003-json-gameplay-geometry.md`, `decisions/ADR-005-outline-mesh-for-godot.md`.

## Nächste Schritte

1. Versionsentscheidung für den aktuellen `main`-Stand treffen (Game Export v3, Outline-Mesh und dessen adaptive Tessellierung sind bereits gemergt und laut bisheriger Dokumentation getestet).
2. `feature/godot-importer` beginnen: Godot Importer für Game SVG + Game JSON v3 (inklusive `render_points` und `*.meshbin`) entwickeln.
3. Klicklogik für Game Areas in Godot umsetzen.
4. Performance mit komplexen Seiten testen.
5. Die SVG-/Outline-Mesh-Pipeline an weiteren Motivtypen testen (offener Langzeittest, kein Blocker).

## Bekannte Grenzen

- Nicht deckungsgleiche Farbvorlagen können die Farbanalyse verfälschen.
- Sehr komplexe Farbverläufe werden bewusst auf repräsentative Ziel-Farben reduziert.
- Extrem kleine Regionen bleiben eine Herausforderung für Erkennung, Labels und Bedienbarkeit.
- Semantisches Zusammenfassen mehrerer Regionen erfolgt derzeit nicht automatisch.
- Label-Positionen können bei ungewöhnlichen Formen manuell angepasst werden müssen.
- Der Vektor-Outline-Mesh-Export benötigt `shapely`; ohne diese Abhängigkeit entfällt nur das Mesh, der übrige Game-JSON-Export bleibt unberührt.
- Die SVG-/Outline-Mesh-Pipeline sollte langfristig noch an weiteren Motivtypen getestet werden.

## Veraltete oder ersetzte Ansätze

- Direkter Pixel-Flood-Fill auf dem finalen PNG ist nicht mehr die Zielarchitektur.
- Ein Illustrator-zentrierter Produktionsworkflow ist nicht mehr der primäre Weg, bleibt aber optional für Spezialfälle.
- Vollautomatische semantische Objekterkennung ist derzeit bewusst nicht Bestandteil des Systems.
- Die historischen Python-Schnappschüsse unter `history/` (`_v1` … `_v10`) enden beim Stand von `v0.10.0`; `history/coloring_region_extractor_gui_v10.py` ist seit dem SVG-Outline-Export (`v0.11.0`) nicht mehr identisch mit dem aktuellen `coloring_region_extractor_gui.py`.

## Autoritative Detaildokumente

- Architektur: `ARCHITECTURE.md`
- Aktuelle Übergabe: `HANDOFF.md`
- Dokumentationsregeln: `AI_PROJECT_RULES.md`
- Systeme: `systems/`
- Architekturentscheidungen: `decisions/`
- Release-Historie: `../CHANGELOG.md`
- Historischer Altbestand: `archive/PROJECT_STATUS_LEGACY.md`
