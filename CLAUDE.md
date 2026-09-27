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
python3 -m py_compile coloring_region_extractor_gui.py
python3 -m unittest discover -s tests -v
```

Seit der `tests/`-Einführung existiert eine automatisierte Testsuite (Python `unittest`) für die Outline-Mesh-Geometrie, die per GitHub Actions (`.github/workflows/tests.yml`) bei Push/PR auf `main` ausgeführt wird. Es gibt weiterhin keinen Linter und keinen darüber hinausgehenden Build-Schritt. Änderungen, die nicht von der Testsuite abgedeckt sind, werden weiterhin primär manuell über die GUI verifiziert. Vor jeder Annahme dazu den aktuellen Repository-Stand prüfen.

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

## Externe Änderungsübergabe

Ein Teil der Entwicklung dieses Projekts kann außerhalb von Claude Code stattfinden, insbesondere gemeinsam mit ChatGPT.
Wenn eine Änderungsübergabe zusammen mit lokal übernommenen Codeänderungen bereitgestellt wird, gilt folgender Ablauf:

1. Lies die Änderungsübergabe als Kontext für Ziel, Motivation und technische Entscheidungen der Änderung.
2. Prüfe anschließend den tatsächlichen Source Code und den Git Diff.
3. Bei Abweichungen zwischen Übergabe und tatsächlicher Implementierung haben der verifizierte Source Code, die Projektkonfiguration und der aktuelle Git Stand Vorrang.
4. Bestimme anhand der tatsächlich implementierten Änderung, welche Projektdokumentation betroffen ist.
5. Aktualisiere nur die Dokumentationsdateien, deren Inhalt sich tatsächlich geändert hat.
6. Beachte dabei vollständig die Dokumentationsregeln aus `docs/AI_PROJECT_RULES.md`.
7. Prüfe bei technischen oder architektonischen Entscheidungen, ob eine neue ADR notwendig ist oder eine bestehende Entscheidung betroffen ist.
8. Führe nach der Aktualisierung einen Konsistenzcheck zwischen Code, Git Stand und betroffener Dokumentation durch.
9. Führe anschließend den Git-Workflow ausschließlich gemäß `docs/GIT_WORKFLOW.md` durch.

Die Änderungsübergabe ist keine autoritative Beschreibung des implementierten Zustands. Sie ergänzt den Source Code um Kontext, Zielsetzung und Begründungen.

Nach Abschluss einer solchen Änderung kurz zusammenfassen:

- welche Änderung tatsächlich erkannt wurde,
- welche Dokumentationsdateien aktualisiert wurden,
- ob eine ADR erstellt oder eine bestehende ADR betroffen war,
- ob die Änderungsübergabe von der tatsächlichen Implementierung abwich,
- welche Punkte gegebenenfalls nicht verifiziert werden konnten.

## Git

Details: `docs/GIT_WORKFLOW.md`.

Commit-Nachrichten und Projektdokumentation bleiben deutsch. Datei- und Ordnernamen der Dokumentation bleiben englisch.
