# Entwicklungsübergabe

Letzte Migration der Dokumentation: 27.09.2026
Letzte Verifikation gegen Quellcode und Git-Historie: 27.09.2026

## Projekt

Coloring Region Extractor für Cosy Desk - The Coloring Atelier.

## Aktueller Release (VERSION / CHANGELOG)

`v0.11.0`

## Aktueller Branch

`main` sowie der offene Branch `chore/outline-mesh-tests` (PR ausstehend).

## Zuletzt abgeschlossen

- **`v0.11.0` (released):** SVG-Outline-Export überarbeitet — separate Vektor-Outline-Ebene, Distanzfeld-basierte Glättung, krümmungsabhängige Vereinfachung, einstellbare Pixel-Toleranz, kontrollierte Fill-Überdeckung, Exportstatistiken.
- **Auf `main` gemergt, noch nicht versioniert:** Game Export v3 (`coloring_game_export_v3`, PR #3, `bcc13d9`) — explizite Gameplay-Geometrie (`points`) und einheitliche Game-Area-Struktur (`game_areas`, `is_implicit`) im JSON.
- **Auf `main` gemergt, noch nicht versioniert:** Vektor-Outline-Mesh & Render-Geometrie für Godot (PR #4, `9c2dd17`) — `render_points` pro Region sowie ein trianguliertes, binäres Outline-Mesh (`*_outline.meshbin`, Format `lcs_outline_mesh_v1`); benötigt die neue Abhängigkeit `shapely` (bereits in `requirements.txt`).

## Aktuell in Arbeit

`chore/outline-mesh-tests` (PR ausstehend): automatisierte `unittest`-Geometrietests für die Outline-Mesh-Pipeline (`tests/test_outline_mesh_geometry.py`) und ein GitHub-Actions-Workflow (`.github/workflows/tests.yml`), der sie bei Push/PR auf `main` ausführt. Keine Änderung an `coloring_region_extractor_gui.py`. Ziel: Regressionsschutz vor geplanten Änderungen an Kurvenglättung, Konturerzeugung und Mesh-Export.

## Nächster Arbeitsschritt

1. `chore/outline-mesh-tests` mergen.
2. Versionsentscheidung für den `main`-Stand treffen (Game Export v3 und Outline-Mesh sind bereits gemergt und laut bisheriger Dokumentation getestet; `VERSION`/`CHANGELOG.md` sind noch nicht aktualisiert).
3. Danach `feature/godot-importer` beginnen: Game SVG + Game JSON v3 (inklusive `render_points` und `*.meshbin`) einlesen und daraus GameArea-Nodes mit Polygon2D-Children, Label sowie Farb-ID/Zielfarbe erzeugen.

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
