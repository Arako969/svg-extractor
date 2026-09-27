# CLAUDE.md

Diese Datei definiert den Einstieg für Claude Code in dieses Repository. Die Projektdokumentation befindet sich unter `docs/`.

## Verbindlicher Start einer Arbeitssitzung

Vor Änderungen am Projekt:

1. `docs/PROJECT_STATE.md` lesen.
2. `docs/AI_PROJECT_RULES.md` lesen.
3. `docs/HANDOFF.md` lesen, wenn an laufender Arbeit angeknüpft wird.
4. Nur die für die Aufgabe relevanten Dateien unter `docs/systems/` und `docs/decisions/` lesen.
5. Den tatsächlich betroffenen Quellcode prüfen.

Nicht pauschal alle historischen Dokumente lesen. `docs/archive/` dient ausschließlich der Historie.

## Quellenpriorität

Bei Widersprüchen gilt:

1. verifizierter aktueller Quellcode und Projektkonfiguration
2. `docs/PROJECT_STATE.md`
3. `docs/ARCHITECTURE.md`
4. relevante Systemdokumentation
5. akzeptierte ADRs
6. `docs/HANDOFF.md`
7. `CHANGELOG.md`
8. Archiv und historische Informationen

## Projekt

Coloring Region Extractor: Python/Tkinter-Werkzeug zur Aufbereitung von Coloring-Book-Artwork für ein späteres Malen-nach-Zahlen-System in Godot.

Zentrale Architekturentscheidung: Technische Region und Game Area sind getrennte Konzepte. Eine Game Area kann mehrere technische Regionen enthalten.

## Befehle

```bash
python3 -m pip install -r requirements.txt
python3 coloring_region_extractor_gui.py
./"Coloring Region Extractor.command"
```

Laut bisheriger Dokumentation gibt es keine automatisierte Testsuite, keinen Linter und keinen Build-Schritt. Änderungen wurden bislang primär manuell über die GUI verifiziert. Vor jeder Annahme dazu den aktuellen Repository-Stand prüfen.

## Dokumentationspflege ist Teil der Aufgabe

Nach einer Änderung:

1. `docs/PROJECT_STATE.md` prüfen und bei geändertem Projektzustand aktualisieren.
2. Betroffene Datei unter `docs/systems/` aktualisieren.
3. `docs/ARCHITECTURE.md` nur bei Architekturänderungen aktualisieren.
4. Bei bedeutenden technischen Entscheidungen eine ADR unter `docs/decisions/` anlegen oder aktualisieren.
5. `docs/HANDOFF.md` auf den nächsten konkreten Arbeitsschritt setzen.
6. `CHANGELOG.md` nur bei einem tatsächlichen Release aktualisieren.
7. Abschließend auf Widersprüche zwischen Code und Dokumentation prüfen.

Eine Aufgabe mit dokumentationsrelevanter Änderung ist erst fertig, wenn diese Pflege erfolgt ist.

## Git

Details: `docs/GIT_WORKFLOW.md`.

Commit-Nachrichten und Projektdokumentation bleiben deutsch. Datei- und Ordnernamen der Dokumentation bleiben englisch.
