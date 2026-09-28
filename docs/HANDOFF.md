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
- **Auf `main` gemergt, noch nicht versioniert:** Outline-Kurven zentripetal parametrisiert und Ecken geschützt (PR #10, `09fbabd`) — `_closed_curve_segments()` als gemeinsame Quelle kubischer Bezier-Segmente für SVG-Pfad (`_closed_catmull_rom_svg_path()`) und Mesh-Ring (`_sample_closed_catmull_rom()`): zentripetale Catmull-Rom-Parametrisierung (`alpha=0.5`), volle Tangenten (`tension=1.0` statt bisher `0.44`). `_hard_corner_indices()` schützt echte Ecken (Winkel ≥ 35° mit gerader Nachbarstützung, Geradheitsfehler ≤ 0.65 px) vor Überglättung und Wegfall bei der Vereinfachung; runde, eng gebogene Spitzen bleiben weich. Behebt die nach PR #8 verbliebenen sichtbaren Knicke (Ursache lag in der Kurve selbst, nicht in der Mesh-Abtastdichte). Betrifft SVG- **und** Mesh-Export gemeinsam. Testsuite auf 10 Tests erweitert. Binärformat, Game JSON v3, `points`/`render_points` unverändert; keine neue Architekturentscheidung. Vor dem Merge visuell geprüft: einfache Formen, Blütenspitze und vollständiges Hundemotiv im Godot-VectorColoringTest — sieht gut aus laut Rückmeldung des Projektinhabers. Weitere Motivtypen bleiben ein späterer Langzeittest.

## Aktuell in Arbeit

Kein offener Feature-Branch. `main` ist der aktuelle, vollständig gemergte Arbeitsstand.

## Nächster Arbeitsschritt

1. Versionsentscheidung für den `main`-Stand treffen (Game Export v3, Outline-Mesh, dessen adaptive Tessellierung und die Kurvenkorrektur sind bereits gemergt und laut bisheriger Dokumentation getestet; `VERSION`/`CHANGELOG.md` sind noch nicht aktualisiert).
2. Danach `feature/godot-importer` beginnen: Game SVG + Game JSON v3 (inklusive `render_points` und `*.meshbin`) einlesen und daraus GameArea-Nodes mit Polygon2D-Children, Label sowie Farb-ID/Zielfarbe erzeugen.

## Ziel des folgenden Entwicklungsblocks

Godot Importer für Game SVG und Game JSON v3 entwickeln. Daraus sollen Game-Area-Nodes mit Polygon2D-Children, Label, Farb-ID und Zielfarbe entstehen. Das triangulierte Outline-Mesh (`*.meshbin`) soll für das Godot-seitige Rendern der Outline genutzt werden.

## Danach

- Klicklogik: Ein Klick auf ein Polygon färbt alle Polygone derselben Game Area.
- Performance-Test mit komplexen Seiten.

## Zentrale Entscheidung

Technische Region ist nicht gleich Game Area. Eine Game Area kann mehrere technische Regionen beziehungsweise Polygone enthalten.

## Vor Arbeitsbeginn lesen

1. `PROJECT_STATE.md`
2. `AI_PROJECT_RULES.md`
3. `ARCHITECTURE.md`
4. relevante Datei unter `systems/`
5. relevante ADRs unter `decisions/`
6. tatsächlichen Quellcode der betroffenen Funktion
