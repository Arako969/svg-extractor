# ADR-002: Vektorregionen statt direktem Pixel-Flood-Fill

Status: Akzeptiert

## Kontext

Der ursprüngliche Ansatz sah vor, direkt auf einem PNG per Flood Fill zu färben. Anti-Aliasing, kleine Konturlücken, halbtransparente Randpixel und starke Zoomstufen führten jedoch zu sichtbaren und technischen Problemen.

## Entscheidung

Spielflächen werden als Vektorregionen beziehungsweise explizite Geometrie behandelt. Die Outline bleibt eine getrennte visuelle Ebene.

## Konsequenzen

- Farbflächen sind unabhängig von Raster-Flood-Fill.
- Die sichtbare Outline kann separat optimiert werden.
- Mehrere Polygone können einer Game Area zugeordnet werden.
- Gameplay-Geometrie kann strukturiert an Godot übergeben werden.
