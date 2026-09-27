# Game Areas

## Grundprinzip

Technische Regionen und Game Areas sind getrennte Konzepte.

Eine technische Region beschreibt Geometrie. Eine Game Area beschreibt eine spielerische Einheit und kann mehrere technische Regionen enthalten.

## Daten

Eine Game Area enthält konzeptionell:

- ID
- Name
- Farb-ID
- referenzierte Region-IDs
- Label-Position
- Zielfarbe

## Spielverhalten

Wenn der Spieler später auf eine technische Region klickt, wird deren Game Area ermittelt. Bei korrekter Farbwahl werden alle zugehörigen Regionen gemeinsam eingefärbt und die Game Area als gelöst behandelt.

## Ungruppierte Regionen

Im Game Export v3 (`coloring_game_export_v3`, auf `main` gemergt) werden ungruppierte aktive Regionen als implizite Game Areas mit genau einer Region exportiert (`is_implicit = true`). Dadurch benötigt Godot keinen separaten Sonderfall. Details: `EXPORT_PIPELINE.md`.

## Gruppierung

Semantisches automatisches Gruppieren ist derzeit nicht Bestandteil des Systems. Zusammengehörige Regionen werden vom Nutzer zu Game Areas gruppiert.

## Labels

Game Areas besitzen eine Label-Position. Automatische Positionen können bei ungewöhnlichen Formen ungeeignet sein und deshalb manuell angepasst werden.
