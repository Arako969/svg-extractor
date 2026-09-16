# CHANGELOG

Dieses Dokument enthält nur veröffentlichte Versionen.

## v0.11.0

SVG-Outline-Export qualitativ überarbeitet.

- Outline als eigene Vektor-Ebene über den Game Areas exportiert, nicht mehr aus den Region-Rändern zusammengesetzt
- Geglättete Vektor-Outlines ergänzt (Distanzfeld-basierte Glättung statt roher Pixelkontur)
- Weiße Spalten zwischen Game Areas und Outline durch kontrollierte Fill-Überdeckung verhindert
- Adaptive, krümmungsabhängige Outline-Vereinfachung ergänzt
- Einstellbare Pixel-Toleranz im Export ergänzt (0,20–1,20 px, Schritt 0,05 px)
- Exportstatistiken für Ankerpunktreduktion ergänzt (Punkte vorher/nachher, Reduktion %, Toleranz)

## v0.10.0

Drei-Spalten-Oberfläche, Fit-to-View, Zoom und bessere Vorschau-Navigation ergänzt.

## v0.9.0

Fehlende Flächen können per Klick ergänzt und automatisch eingefärbt werden.

## v0.8.0

Farbbasierte Wiederherstellung fehlender Regionen ergänzt.

## v0.7.0

Adaptive Mikroregionen und relative Mindestgrößen ergänzt.

## v0.6.0

Farbbasierte Unterregionen für nicht durch Outline getrennte Farbflächen ergänzt.

## v0.5.0

Farbvorlagen, automatische Farbanalyse, Palette und Farb-IDs ergänzt.

## v0.4.0

Gruppen-Workflow ausgebaut; Projekt- und Exportstruktur erweitert.

## v0.3.0

Mehrfachauswahl, Gruppen und erste logische Game Areas ergänzt.

## v0.2.0

Bildrand kann als Grenze behandelt werden; Regionserkennung und Bedienung verbessert.

## v0.1.0

Erste GUI mit Regionserkennung, Vorschau sowie SVG- und JSON-Export.
