# Development Handoff

## Projekt
Coloring Region Extractor für Cozy Desk / Little Color Studio.

## Repository
https://github.com/Arako969/svg-extractor

## Aktueller Release
v0.11.0

## Aktueller Branch
feature/game-export-v3

## Architektur
Outline PNG + optionale Farbvorlage → Regionen → Game Areas → SVG + JSON → Godot.

## Zentrale Entscheidung
Technische Region != Game Area.
Eine Game Area kann mehrere Polygone enthalten.

## Regionstypen
Normal
Micro
Color Overlay
Recovery
Manual

## Setup
macOS-Finder-Launcher: `Coloring Region Extractor.command`
Abhängigkeiten: `pip install -r requirements.txt` (opencv-python, pillow, numpy)

## Zuletzt abgeschlossen (v0.11.0)
SVG-Outline-Export überarbeitet: separate Vektor-Outline-Ebene über den Game Areas, Distanzfeld-basierte Glättung, krümmungsabhängige Vereinfachung, einstellbare Pixel-Toleranz, Fill-Überdeckung gegen weiße Spalten, Exportstatistiken. Details siehe PROJECT-STATUS.md §9.

## Aktuell in Arbeit
Game-Export v3 (Branch `feature/game-export-v3`, getestet, noch nicht gemerged/released). JSON-Format `coloring_game_export_v3`: `regions` enthält jetzt die reine Gameplay-Geometrie (`points`, `centroid`, `area`, `bbox`, Farbe, Priorität, Overlay-Flags) pro aktiver Region; `game_areas` enthält manuelle Gruppen (`is_implicit = false`) und automatisch erzeugte Ein-Region-Game-Areas für ungruppierte Regionen (`is_implicit = true`). Ziel: Godot parst für Gameplay-Geometrie kein SVG mehr. Details siehe PROJECT-STATUS.md §8.

## Nächster Branch
feature/game-export-v3 mergen, danach feature/godot-importer

## Ziel
Erst `feature/game-export-v3` nach `main` mergen (Versionsentscheidung noch offen). Danach Godot Importer entwickeln: Game SVG + Game JSON (v3) einlesen und daraus GameArea-Nodes mit Polygon2D-Children, Label sowie Farb-ID/Zielfarbe erzeugen.

## Danach
Klicklogik in Godot (ein Klick färbt alle Polygone einer Game Area) und Performance-Test mit komplexen Seiten.

## Wichtige Dokumente
PROJECT-STATUS.md
GIT-WORKFLOW.md
CHANGELOG.md
CLAUDE.md
