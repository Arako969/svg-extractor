# ADR-003: Gameplay-Geometrie explizit im JSON

Status: Akzeptiert und umgesetzt (auf `main` gemergt, PR #3, Commit `bcc13d9`, 2026-09-18). Noch nicht Teil eines versionierten Releases (`VERSION`/`CHANGELOG.md` stehen weiterhin auf `v0.11.0`).

## Kontext

Der Godot Importer soll für die Spiellogik möglichst keine SVG-Pfade analysieren müssen. Die für Gameplay benötigte Geometrie ist im Extractor bereits vorhanden.

## Entscheidung

Game Export v3 soll die ursprüngliche Gameplay-Geometrie aktiver technischer Regionen explizit im JSON exportieren. Game Areas referenzieren diese Regionen. Ungruppierte aktive Regionen werden als implizite Game Areas behandelt.

## Konsequenzen

- JSON wird zur maßgeblichen Quelle für Gameplay-Geometrie und Game-Area-Struktur.
- SVG bleibt primär visuell.
- Godot benötigt keinen Sonderfall für ungruppierte Regionen.

## Statushinweis

Verifiziert am 27.09.2026 gegen `coloring_region_extractor_gui.py` (`export_game_json()`) und die Git-Historie: die Implementierung ist bereits auf `main` gemergt (Commit `bcc13d9`), nicht mehr auf einem separaten Feature-Branch. Sie ist jedoch noch nicht Teil eines versionierten Releases — eine Versionsentscheidung steht aus.
