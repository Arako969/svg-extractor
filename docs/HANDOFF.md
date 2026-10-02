# Entwicklungsübergabe

Letzte Migration der Dokumentation: 27.09.2026
Letzte Verifikation gegen Quellcode und Git-Historie: 28.09.2026 (PR #5–#10)

## Projekt

Coloring Region Extractor für Cosy Desk - The Coloring Atelier.

## Aktueller Release (VERSION / CHANGELOG)

`v0.11.0`

## Aktueller Branch

`main`. Kein offener Feature-Branch.

## Zuletzt abgeschlossen

- **`v0.11.0` (released):** SVG-Outline-Export überarbeitet — separate Vektor-Outline-Ebene, Distanzfeld-basierte Glättung, krümmungsabhängige Vereinfachung, einstellbare Pixel-Toleranz, kontrollierte Fill-Überdeckung, Exportstatistiken.
- **Auf `main` gemergt, noch nicht versioniert:** Game Export v3 (`coloring_game_export_v3`, PR #3, `bcc13d9`) — explizite Gameplay-Geometrie (`points`) und einheitliche Game-Area-Struktur (`game_areas`, `is_implicit`) im JSON.
- **Auf `main` gemergt, noch nicht versioniert:** Vektor-Outline-Mesh & Render-Geometrie für Godot (PR #4, `9c2dd17`) — `render_points` pro Region sowie ein trianguliertes, binäres Outline-Mesh (`*_outline.meshbin`, Format `lcs_outline_mesh_v1`); benötigt die neue Abhängigkeit `shapely` (bereits in `requirements.txt`).
- **Auf `main` gemergt (PR #6, nicht versionsrelevant):** Outline-Mesh mit automatisierten Geometrietests abgesichert — `tests/test_outline_mesh_geometry.py` (Catmull-Rom-Sampling, Näherungsqualität, leere Linienmaske, Ring-Mesh mit Aussparung, `LCSM v1`-Export) und GitHub-Actions-Workflow (`.github/workflows/tests.yml`) bei Push/PR auf `main`. Keine Änderung an `coloring_region_extractor_gui.py`; reine Testinfrastruktur.
- **Auf `main` gemergt, noch nicht versioniert:** Outline-Mesh adaptiv tessellieren (PR #8, `9b970b4`) — feste Schrittabtastung der Catmull-Rom-Segmente im Outline-Mesh durch adaptive, fehlerbasierte De-Casteljau-Tessellierung ersetzt (`_sample_cubic_bezier_adaptive`, Fehlerbudget `0.02 px`, max. Tiefe `16`). Testsuite auf 7 Tests erweitert. Betrifft nur das Godot-Outline-Mesh, nicht den SVG-Export. **Korrektur:** Die Annahme, dies mache die Outline bei starkem Zoom allein glatt, war unvollständig — sichtbare Knicke blieben bestehen, siehe folgender Punkt.
- **Auf `main` gemergt, noch nicht versioniert:** Outline-Kurven zentripetal parametrisiert und Ecken geschützt (PR #10, `09fbabd`) — `_closed_curve_segments()` als gemeinsame Quelle kubischer Bezier-Segmente für SVG-Pfad (`_closed_catmull_rom_svg_path()`) und Mesh-Ring (`_sample_closed_catmull_rom()`): zentripetale Catmull-Rom-Parametrisierung (`alpha=0.5`), volle Tangenten (`tension=1.0` statt bisher `0.44`). `_hard_corner_indices()` schützt echte Ecken (Winkel ≥ 35° mit gerader Nachbarstützung, Geradheitsfehler ≤ 0.65 px) vor Überglättung und Wegfall bei der Vereinfachung; runde, eng gebogene Spitzen bleiben weich. Behebt die nach PR #8 verbliebenen sichtbaren Knicke (Ursache lag in der Kurve selbst, nicht in der Mesh-Abtastdichte). Betrifft SVG- **und** Mesh-Export gemeinsam. Testsuite auf 10 Tests erweitert. Binärformat, Game JSON v3, `points`/`render_points` unverändert; keine neue Architekturentscheidung. Visuell geprüft: einfache Formen (Kreis, Ellipse, Sechseck, Stern) und die rechte Blütenspitze des Hundemotivs (Illustrator 800 %, passendes Mesh in Godot); das Hundemotiv wurde vor dem Merge vom Projektinhaber geprüft („sieht gut aus“). Nicht belegt: eine systematische Abnahme aller Zoomstufen und Motivtypen sowie ein dokumentierter Test bei genau 24-fachem Zoom. Weitere Motivtypen bleiben ein späterer Langzeittest.

## Aktuell in Arbeit

Kein offener Feature-Branch. `main` ist der aktuelle, vollständig gemergte Arbeitsstand.

## Nächster Arbeitsschritt

1. **Zehn-Punkte-Plan, Punkt 4:** Qualitätsstufen Standard, Hoch und Ultra definieren (Branch z. B. `feature/quality-presets`). Der vollständige Plan mit Status steht in `PROJECT_STATE.md`, Abschnitt „Nächste Schritte“.
2. Die Version wird erst nach Abschluss aller zehn Punkte angehoben; bis dahin bleiben `VERSION` und `CHANGELOG.md` auf `v0.11.0`.

## Ziel des folgenden Entwicklungsblocks

Qualitätsstufen Standard, Hoch und Ultra:

1. Vorhandene Qualitätsparameter und ihre Wirkung auf SVG, Mesh, Laufzeit und Dateigröße erfassen.
2. Für jede Stufe messbare Ziele und nachvollziehbare Parameterwerte festlegen. Die gemeinsame Kurvengeometrie und der Eckenschutz aus PR #10 bleiben die Basis.
3. Presets am Hundemotiv und an einfachen Formen vergleichen, danach ein detailreicheres Motiv ergänzen.
4. Echte Ecken, runde Spitzen, Löcher, Füllüberdeckung und Hit-Test-Geometrie prüfen; die Testsuite bei tatsächlichem Regressionsrisiko erweitern.
5. Erst nach technischer Validierung die Presets in der UI anbieten.

## Danach

Zehn-Punkte-Plan in Reihenfolge: Mesh-Vorschau (5), Game-Paket-Export (6), Exportparameter im JSON (7), Motivprofile (8), Grundmodus/erweiterte Einstellungen (9), Dokumentation und Versionsanhebung (10).

Außerhalb des Plans, Reihenfolge noch offen: Godot Importer (`feature/godot-importer`: Game SVG + Game JSON v3 inklusive `render_points` und `*.meshbin` in GameArea-Nodes mit Polygon2D-Children, Label, Farb-ID/Zielfarbe), Klicklogik (ein Klick färbt alle Polygone derselben Game Area) und Performance-Test mit komplexen Seiten.

## Zentrale Entscheidung

Technische Region ist nicht gleich Game Area. Eine Game Area kann mehrere technische Regionen beziehungsweise Polygone enthalten.

## Vor Arbeitsbeginn lesen

1. `PROJECT_STATE.md`
2. `AI_PROJECT_RULES.md`
3. `ARCHITECTURE.md`
4. relevante Datei unter `systems/`
5. relevante ADRs unter `decisions/`
6. tatsächlichen Quellcode der betroffenen Funktion
