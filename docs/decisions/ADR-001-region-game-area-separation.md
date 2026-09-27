# ADR-001: Trennung von technischer Region und Game Area

Status: Akzeptiert

## Kontext

Eine visuell zusammengehörige spielerische Fläche kann aus mehreren geometrisch getrennten Teilflächen bestehen. Gleichzeitig sollen dekorative Linien und komplexe Motive erhalten bleiben.

## Entscheidung

Technische Region und Game Area bleiben getrennte Konzepte.

- Technische Region = geometrische Teilfläche.
- Game Area = spielerische Einheit.
- Eine Game Area kann mehrere technische Regionen enthalten.

## Konsequenzen

- Ein Klick kann mehrere Polygone gleichzeitig färben.
- Komplexe Polygon-Booleans zum physischen Verschmelzen sind nicht erforderlich.
- Dekorative Linien können erhalten bleiben.
- Kleine Overlays können unabhängig von Grundflächen existieren.
- Godot kann eine Game Area als logisches Objekt mit mehreren Polygon-Children behandeln.
