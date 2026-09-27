# ADR-004: Separate SVG-Outline über den Game Areas

Status: Akzeptiert und mit `v0.11.0` veröffentlicht

## Kontext

Aus einzelnen Game-Area-Rändern zusammengesetzte Outlines und exakt anliegende Fills führten zu Qualitätsproblemen, insbesondere Rastertreppen und sichtbaren weißen Spalten.

## Entscheidung

Die visuelle Outline wird als eigene SVG-Ebene über den Game Areas exportiert. Sie wird aus der binären Linienmaske erzeugt und separat geglättet und vereinfacht. Game-Area-Fills dürfen kontrolliert unter die Outline reichen.

## Konsequenzen

- Die sichtbare Kante wird durch die darüberliegende Outline bestimmt.
- Weiße Spalten zwischen Fill und Outline werden reduziert.
- Outline-Qualität kann unabhängig von Gameplay-Geometrie optimiert werden.
- Pixel-Toleranz bleibt pro Motiv einstellbar.
