# Development Handoff

## Projekt
Coloring Region Extractor für Cozy Desk / Little Color Studio.

## Repository
https://github.com/Arako969/svg-extractor

## Aktueller Release
v0.11.0

## Aktueller Branch
main

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
Nichts – main ist releaster Stand, kein offener Branch.

## Nächster Branch
feature/godot-importer

## Ziel
Godot Importer entwickeln: Game SVG + Game JSON einlesen und daraus GameArea-Nodes mit Polygon2D-Children, Label sowie Farb-ID/Zielfarbe erzeugen.

## Danach
Klicklogik in Godot (ein Klick färbt alle Polygone einer Game Area) und Performance-Test mit komplexen Seiten.

## Wichtige Dokumente
PROJECT-STATUS.md
GIT-WORKFLOW.md
CHANGELOG.md
CLAUDE.md
