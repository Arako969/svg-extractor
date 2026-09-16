# Development Handoff

## Projekt
Coloring Region Extractor für Cozy Desk / Little Color Studio.

## Repository
https://github.com/Arako969/svg-extractor

## Aktueller Release
v0.10.0

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

## Aktuell in Arbeit
SVG Outline Export.

## Nächster Branch
feature/svg-outline-export

## Ziel
SVG soll game_areas und outlines enthalten.
Outline muss visuell über Game Areas liegen.

## Danach
Godot Importer entwickeln.

## Wichtige Dokumente
PROJECT-STATUS.md
GIT-WORKFLOW.md
CHANGELOG.md
CLAUDE.md
