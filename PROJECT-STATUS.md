# PROJECT-STATUS

Aktueller Stand: **v0.10.0**

Dieses Dokument beschreibt den laufenden Entwicklungsstand des **Coloring Region Extractor** möglichst vollständig. Es ist bewusst detaillierter als `CHANGELOG.md`.

`CHANGELOG.md` dokumentiert nur tatsächliche Releases.  
`PROJECT-STATUS.md` dokumentiert zusätzlich technische Entscheidungen, verworfene Ansätze, bekannte Grenzen, Bedienabläufe, aktuelle Architektur und die nächsten Arbeitsschritte.

---

# 1. Projektziel

Der Coloring Region Extractor ist ein Desktop-Werkzeug zur Vorbereitung von schwarz-weißen Coloring-Book-Illustrationen für ein späteres Malen-nach-Zahlen-System in Godot.

Ausgangssituation:

- Die Illustrationen liegen typischerweise als schwarz-weiße Outline-Bilder vor.
- Häufig existiert zusätzlich eine kolorierte Referenzversion desselben Motivs.
- Die Bilder stammen unter anderem aus KI-generierten Coloring-Book-Artworks.
- Das Ziel ist, aus diesen Bildern automatisch oder halbautomatisch spielbare Farbregionen zu erzeugen.
- Die erzeugten Regionen sollen später in Godot als anklickbare Game Areas verwendet werden.
- Mehrere technische Teilregionen können zu einer logischen Game Area zusammengefasst werden.
- Eine Game Area soll im Spiel mit einem einzigen Klick vollständig eingefärbt werden.

Langfristig soll damit ein schneller Content-Workflow entstehen:

```text
Outline-Bild
+ Farbvorlage
        ↓
Coloring Region Extractor
        ↓
Regionen erkennen
        ↓
Regionen korrigieren / gruppieren
        ↓
Farb-IDs und Ziel-Farben ableiten
        ↓
SVG / JSON / Outline exportieren
        ↓
Godot Importer
        ↓
fertige Malen-nach-Zahlen-Seite
```

---

# 2. Warum der ursprüngliche Pixel-Flood-Fill-Ansatz verworfen wurde

Ursprünglich war vorgesehen, direkt auf einem PNG per Flood Fill zu färben.

Dabei traten mehrere Probleme auf:

- Anti-Aliasing an schwarzen Konturen erzeugt halbtransparente oder graue Randpixel.
- Flood Fill stoppt an diesen Pixeln nicht immer sauber.
- Dadurch entstehen unschöne weiße oder halbgefärbte Säume.
- Kleine Unterbrechungen in Konturen lassen Farbe in Nachbarbereiche auslaufen.
- Beim starken Zoomen werden Rasterbilder sichtbar unscharf.
- Komplexe Motive lassen sich nur schwer robust pixelbasiert auswerten.

Daraus entstand der neue Ansatz:

- **Spielflächen als Vektorregionen**
- **separate Outline-Ebene**
- **ein Klick verändert die Farbe einer Game Area**
- **mehrere Polygone können zu einer logischen Game Area gehören**

---

# 3. Grundarchitektur des aktuellen Systems

Das System arbeitet mit drei logischen Ebenen:

## 3.1 Regionserkennung

Die schwarz-weiße Outline wird analysiert.

Prinzip:

- dunkle Pixel werden als Linien behandelt
- weiße Bereiche werden als potenzielle Regionen behandelt
- geschlossene weiße Bereiche werden als Regionen erkannt
- kleine Regionen können gefiltert werden
- der Bildrand kann optional als Begrenzung gelten

## 3.2 Farbzuordnung

Wenn eine kolorierte Referenz vorhanden ist:

- Pixel innerhalb einer Region werden ausgelesen
- sehr dunkle Pixel können ignoriert werden
- sehr helle Pixel können ignoriert werden
- pro Region wird eine repräsentative Farbe bestimmt
- ähnliche Farben werden zu einer reduzierten Palette geclustert
- jede Region erhält eine vorgeschlagene Farb-ID

## 3.3 Game Areas

Technische Regionen und spielerische Flächen sind getrennte Konzepte.

Beispiel:

```text
Game Area: Blatt rechts
├── Region 20
├── Region 39
├── Region 45
├── Region 57
└── Region 59
```

Im Spiel soll ein Klick auf **eine beliebige Teilregion** genügen.

Die komplette Game Area wird dann gleichzeitig eingefärbt.

---

# 4. Versionshistorie im Detail

---

## v0.1.0

Erster funktionsfähiger Prototyp.

### Funktionen

- Laden eines Outline-Bildes
- Umwandlung in Graustufen
- Schwarz-Weiß-Schwellenwert
- Erkennung dunkler Linien
- Schließen kleiner Lücken per Morphology
- Connected Components zur Erkennung geschlossener Regionen
- Mindestflächengröße als Filter
- Vorschau mit zufälligen Farben
- Export erkannter Regionen als SVG
- Export von Metadaten als JSON
- Ausgabe einer bereinigten Lineart
- erste GUI mit Tkinter

### Technischer Kern

Die Regionserkennung arbeitet auf einer binären Maske:

```text
schwarz = Grenze
weiß    = potenzielle Füllfläche
```

Die weißen Flächen werden mit `connectedComponentsWithStats()` erkannt.

### Erkenntnis

Das Grundprinzip funktioniert auch bei komplexen Coloring-Book-Artworks.

---

## v0.2.0

Unterstützung großer Randbereiche ergänzt.

### Problem

Große Flächen, die den Bildrand berühren, wurden ursprünglich verworfen.

Das war problematisch für:

- Hintergründe
- Himmel
- große Randflächen
- Motive, die absichtlich bis zum Bildrand reichen

### Lösung

Option:

```text
Bildrand als Grenze verwenden
```

Wenn aktiv, darf eine Region den Bildrand berühren und trotzdem als gültige Spielfläche gelten.

---

## v0.3.0

Mehrfachauswahl und logische Gruppen eingeführt.

### Problem

Detailreiche Motive enthalten oft viele technische Regionen, die spielerisch zusammengehören.

Beispiel:

Ein Blatt kann durch Blattadern in fünf geschlossene Regionen zerlegt sein.

### Lösung

Mehrere Regionen können zu einer Gruppe zusammengefasst werden.

Funktionen:

- normale Auswahl per Klick
- Mehrfachauswahl mit Shift + Klick
- Gruppe aus Auswahl erstellen
- Regionen zu bestehender Gruppe hinzufügen
- Regionen aus Gruppen entfernen
- Gruppen löschen
- Gruppenliste
- Gruppenname
- Farb-ID pro Gruppe

### Designentscheidung

Eine Gruppe muss **nicht** zu einem einzigen Polygon vereinigt werden.

Stattdessen bleibt sie eine logische Game Area mit mehreren Polygonen.

Das ist robuster und für Godot günstiger.

---

## v0.4.0

Gruppen- und Projektworkflow erweitert.

### Ergänzungen

- Projekt speichern
- Projekt laden
- Gruppenstatus sichern
- Label-Position pro Gruppe
- Label automatisch zentrieren
- Label manuell im Bild setzen
- aktive und deaktivierte Regionen
- ungegruppierte Regionen sichtbar markieren
- getrennte Exporte:
  - Game SVG
  - Game JSON
  - Outline PNG
  - Vorschau PNG

### Label-Konzept

Eine Game Area zeigt nur **eine** Nummer.

Beispiel:

```text
Game Area "leaf-right"
Farb-ID: 4
Regionen: 5
Label-Position: [x, y]
```

Im Spiel soll nur einmal die `4` angezeigt werden.

---

## v0.5.0

Kolorierte Referenzbilder integriert.

### Motivation

Viele Motive liegen nicht nur als Outline vor, sondern zusätzlich als kolorierte Version.

Diese kann verwendet werden, um Ziel-Farben automatisch abzuleiten.

### Neue Funktionen

- Farbvorlage laden
- automatische Skalierung auf Outline-Größe, falls nötig
- repräsentative Farbe pro Region bestimmen
- dunkle Pixel ignorieren
- helle Pixel ignorieren
- Farbpalette automatisch clustern
- Anzahl der Palettenfarben frei einstellbar
- Farb-ID automatisch zuweisen
- Farbvorschau direkt im Editor anzeigen

### Farbmodell

Für das Clustering wird Lab verwendet.

Grund:

Lab ist für wahrgenommene Farbunterschiede geeigneter als einfaches RGB.

### Repräsentative Farbe

Statt einfacher Durchschnittsfarbe wird eine robuste Medianfarbe verwendet.

Dadurch beeinflussen:

- schwarze Konturen
- Highlights
- kleine Ausreißer
- Anti-Aliasing

das Ergebnis weniger stark.

---

## v0.6.0

Farbbasierte Unterregionen ergänzt.

### Problem

Nicht jede Farbfläche ist in der Outline mit einer schwarzen Linie getrennt.

Beispiel Hund:

- beige Schnauze innerhalb eines orangefarbenen Kopfes
- beige Pfoten innerhalb eines orangefarbenen Körpers

Die Outline sieht dort nur eine große Region.

### Lösung

Große Outline-Regionen können anhand der Farbvorlage intern aufgeteilt werden.

Prinzip:

```text
große Outline-Region
        ↓
Farbvorlage analysieren
        ↓
dominante Farbe = Grundfläche
        ↓
abweichende Farbflächen = Unterregionen
```

### Technische Umsetzung

- Grundregion bleibt erhalten
- neue Unterregionen werden als Overlay-Regionen angelegt
- Overlay-Regionen besitzen eine höhere Priorität
- beim Anklicken gewinnt die kleinere Overlay-Region

Das verhindert komplizierte Polygone mit Löchern.

---

## v0.7.0

Adaptive Mikroregionen eingeführt.

### Problem

Sehr kleine geschlossene Regionen, zum Beispiel einzelne Himbeerzellen, können bei Morphology-Schritten verschwinden.

### Lösung

Zweiter Erkennungsdurchlauf:

- Hauptdurchlauf mit Lückenschließung
- Mikroregion-Durchlauf ohne Lückenschließung

### Neue Parameter

- adaptive Mikroregionen aktivieren
- minimale Mikroregion
- relative Mindestgröße für farbbasierte Unterregionen

### Motivation

Ein einziger globaler Flächenfilter ist für alle Motivtypen ungeeignet.

Hund:

- eher große Farbflächen

Himbeeren:

- sehr kleine geschlossene Zellen

---

## v0.8.0

Farbbasierte Wiederherstellung fehlender Regionen ergänzt.

### Problem

Einige kleine Flächen sind optisch geschlossen, aber pixeltechnisch nicht vollständig von schwarzen Linien umgeben.

Dann kann selbst die Mikroregion-Erkennung keine Region finden.

### Lösung

Color Recovery Pass.

Prinzip:

```text
Farbvorlage
    ↓
Palettenfarbe bestimmen
    ↓
zusammenhängende Farbinseln erkennen
    ↓
prüfen, ob bereits Region vorhanden
    ↓
fehlende Region ergänzen
```

### Neue Funktionen

- farbbasierte Wiederherstellung aktivieren
- Mindestgröße für Recovery-Regionen
- Randabstand
- fehlende Regionen aus Farbvorlage suchen
- Recovery-Regionen löschen

### Visualisierung

Recovery-Regionen werden auffällig markiert, damit sie kontrolliert werden können.

---

## v0.9.0

Manuelles Ergänzen fehlender Flächen per Mausklick.

### Beobachtung

Bei manchen Himbeersegmenten war die Geometrie intern schon vorhanden, aber:

- keine Nummer wurde angezeigt
- die Region war nicht sinnvoll als Spielfläche übernommen

### Lösung

Werkzeug:

```text
Fehlende Fläche hinzufügen
```

### Ablauf

Ein Klick auf eine kleine Problemfläche:

1. prüft, ob bereits eine Region existiert
2. falls ja:
   - Region übernehmen
   - Nummer erzwingen
   - Farbe automatisch bestimmen
3. falls nein:
   - rohe Outline-Komponente suchen
4. falls das ebenfalls scheitert:
   - Farbvorlage als Fallback verwenden
5. neue Region erzeugen
6. passende Farb-ID automatisch zuweisen

### Vorteil

Für seltene Ausnahmefälle muss nicht mehr an globalen Schwellenwerten gedreht werden.

---

## v0.10.0

Oberfläche und Vorschau grundlegend verbessert.

### Ziel

Die GUI wurde zu unübersichtlich.

Insbesondere die lange linke Sidebar war problematisch.

### Neues Layout

Drei Bereiche:

```text
┌────────────────┬──────────────────────────┬────────────────┐
│ Analyse        │                          │ Auswahl        │
│ Farben         │       Vorschau           │ Game Areas     │
│ Parameter      │                          │ Gruppen        │
│                │                          │ Export         │
└────────────────┴──────────────────────────┴────────────────┘
```

### Neue Funktionen

- linke und rechte Sidebar
- mittlere Vorschau
- Fenster frei skalierbar
- Seitenleisten verschiebbar
- Vorschau standardmäßig komplett sichtbar
- Fit-to-View
- hineinzoomen
- herauszoomen
- Zoom-Anzeige
- Magic Mouse / Trackpad-Unterstützung
- Verschieben der Ansicht bei starkem Zoom

### Bedienziel

Bei kleinen Problemregionen:

```text
hineinzoomen
↓
Fehlende Fläche hinzufügen
↓
Farbe automatisch bestimmen
↓
zur Gesamtansicht zurückkehren
```

---

# 5. Aktuelle Regionstypen

Das System kennt inzwischen verschiedene technische Regionstypen.

## Normale Region

Durch geschlossene Outline erkannt.

```text
priority = 0
```

## Mikroregion

Durch den zweiten feinen Erkennungsdurchlauf erkannt.

Typischer Einsatz:

- Himbeerzellen
- kleine Blüten
- feine Blattbereiche

## Farbbasierte Unterregion

Aus einer größeren Outline-Fläche anhand der Farbvorlage erzeugt.

Beispiel:

- beige Pfote innerhalb des Hundekörpers
- beige Schnauze im Hundekopf

```text
priority = 1
```

## Recovery-Region

Aus der Farbvorlage rekonstruiert, wenn die Outline keine geschlossene Region liefern konnte.

```text
priority = 2
```

## Manuell ergänzte Region

Durch direkten Klick des Nutzers erzeugt bzw. übernommen.

```text
priority = 3
```

Dadurch gewinnt bei Überlappungen die spezifischste Region.

---

# 6. Aktuelle Farbarchitektur

## Farbvorlage

Optionales koloriertes Referenzbild.

Idealfall:

- gleiche Geometrie
- gleicher Ausschnitt
- gleiche Auflösung
- gleiche Position

Falls die Auflösung abweicht, wird sie automatisch skaliert.

## Farbfilter

Optional:

- sehr dunkle Pixel ignorieren
- sehr helle Pixel ignorieren

## Palette

Die Anzahl der Farben ist einstellbar.

Beispiele:

- 8 Farben
- 12 Farben
- 16 Farben
- 24 Farben

Die Farbe jeder Region wird auf die nächste Palettenfarbe abgebildet.

## Farb-ID

Die Farb-ID ist die spätere Malen-nach-Zahlen-Nummer.

Beispiel:

```text
Farb-ID 4
RGB: [112, 176, 90]
Hex: #70B05A
```

---

# 7. Aktuelle Gruppenlogik

Eine Game Area besteht aus:

```text
id
name
color_id
region_ids
label_position
target_color
```

Beispiel:

```json
{
  "id": 3,
  "name": "leaf-right",
  "color_id": 4,
  "region_ids": [20, 39, 45, 57, 59],
  "label_position": [1120, 140]
}
```

### Verhalten im späteren Spiel

Klick auf Region 39:

```text
Region 39
↓
gehört zu Game Area 3
↓
richtige Farb-ID gewählt?
↓
alle Regionen [20, 39, 45, 57, 59] einfärben
↓
Label der Game Area ausblenden
↓
Game Area gilt als gelöst
```

---

# 8. Aktuelle Exportformate

## Game SVG

Enthält aktuell primär die Game Areas und ihre Pfade.

Metadaten:

- group-id
- region-id
- color-id
- target color
- label position
- priority
- recovered/manual flags

## Game JSON

Enthält:

- Quellbild
- Farbvorlage
- Breite / Höhe
- Palette
- Game Areas
- Farb-IDs
- Zielfarben
- Label-Positionen
- ungegruppierte aktive Regionen

## Outline PNG

Transparente PNG-Datei:

- schwarze Linien
- transparenter Hintergrund

Sie dient derzeit als visuelle Deckschicht.

---

# 9. Noch offene SVG-Entscheidung

Aktuell werden hauptsächlich die Game Areas in das SVG geschrieben.

Als nächster Schritt ist vorgesehen:

```xml
<svg>
    <g id="game_areas">
        ...
    </g>

    <g id="outlines">
        ...
    </g>
</svg>
```

Die Outline soll dabei als letzte Ebene gespeichert werden und damit visuell über den Farbflächen liegen.

Ziel:

- Game Areas als Vektoren
- Outline ebenfalls als Vektorebene
- optional Outline PNG weiterhin als Fallback

Diese Änderung ist noch **nicht** als Release umgesetzt.

---

# 10. Bekannte Grenzen

## 10.1 Nicht deckungsgleiche Farbvorlagen

Wenn Outline und Farbversion gegeneinander verschoben sind, kann die Farbanalyse ungenau werden.

Geplant:

- optionale automatische Bildausrichtung
- eventuell Feature Matching / Registrierung

## 10.2 Sehr komplexe Farbverläufe

Die aktuelle Logik reduziert eine Region auf eine repräsentative Ziel-Farbe.

Bei stark schattierten Bildern kann dadurch Detailinformation verloren gehen.

Für Malen nach Zahlen ist das aktuell beabsichtigt.

## 10.3 Winzige Regionen

Extrem kleine Flächen können:

- von Morphology verschluckt werden
- keine sichtbare Nummer aufnehmen
- spielerisch zu klein für einen komfortablen Klick sein

Dafür existieren aktuell:

- Mikroregion-Erkennung
- Color Recovery
- manuelles Ergänzen

## 10.4 Automatisches Zusammenfassen

Das System gruppiert Regionen aktuell nicht semantisch automatisch.

Beispiel:

Fünf Blattsegmente werden nicht automatisch als „ein Blatt“ erkannt.

Der Nutzer erstellt die Game Area derzeit manuell.

## 10.5 Label-Platzierung

Automatische Schwerpunktberechnung kann bei ungewöhnlichen Formen unpraktisch sein.

Deshalb kann die Label-Position manuell gesetzt werden.

---

# 11. Verworfen bzw. bewusst nicht weiterverfolgt

## Direkter Illustrator-Zwang

Ursprünglich war ein Workflow vorgesehen:

```text
KI-Bild
↓
Illustrator Image Trace
↓
manuelle SVG-Bereinigung
↓
Godot
```

Dieser Ansatz wurde nicht vollständig verworfen, ist aber nicht mehr der primäre Workflow.

Grund:

- zu viel manuelle Arbeit
- schlecht skalierbar bei vielen Bildern
- unser Python-Tool kann inzwischen große Teile automatisch erledigen

Illustrator bleibt optional für Spezialfälle.

## Vollautomatische semantische Objekterkennung

Eine automatische Erkennung wie:

```text
das ist ein Blatt
das ist der Hund
das ist eine Pfote
```

wurde bisher bewusst nicht eingebaut.

Grund:

- höherer technischer Aufwand
- schwerer deterministisch zu halten
- aktuelle halbautomatische Lösung ist kontrollierbarer

---

# 12. Aktueller empfohlener Produktionsworkflow

## Schritt 1

Outline öffnen.

## Schritt 2

Regionen analysieren.

Typische Startwerte:

```text
Schwarz/Weiß-Schwelle: 190
Lücken schließen: 3
Min. Flächengröße: motivabhängig
Pfad-Vereinfachung: 1.5
```

## Schritt 3

Farbvorlage laden.

## Schritt 4

Palette analysieren.

Je nach Motiv typischerweise:

```text
8 bis 24 Farben
```

## Schritt 5

Problemregionen korrigieren.

Werkzeuge:

- adaptive Mikroregionen
- farbbasierte Unterregionen
- Color Recovery
- fehlende Fläche hinzufügen

## Schritt 6

Logische Game Areas bilden.

Beispiel:

```text
mehrere Blattsegmente
↓
eine Game Area
```

## Schritt 7

Farb-ID prüfen.

## Schritt 8

Label-Position setzen.

## Schritt 9

Projekt speichern.

## Schritt 10

Export:

- Game SVG
- Game JSON
- Outline PNG
- optional Preview

---

# 13. Aktueller Git-Workflow

Semantic Versioning:

```text
vMAJOR.MINOR.PATCH
```

Aktuell:

```text
v0.10.0
```

## Branches

```text
main
feature/<kurzname>
fix/<kurzname>
chore/<kurzname>
```

## Releases

Nur auf ausdrückliche Entscheidung.

Nicht jede Änderung erzeugt automatisch eine neue Version.

---

# 14. Aktueller Entwicklungsstand

Der Extractor ist inzwischen ein brauchbarer halbautomatischer Editor.

Er kann:

- komplexe Coloring-Book-Illustrationen analysieren
- sehr viele geschlossene Regionen erkennen
- kleine Regionen ergänzen
- fehlende Farbflächen anhand einer Referenz rekonstruieren
- technische Regionen zu logischen Game Areas gruppieren
- Farbpaletten ableiten
- Farb-IDs automatisch vorschlagen
- Label-Positionen speichern
- Projekte speichern und laden
- SVG und JSON für den nächsten Pipeline-Schritt exportieren

Die Regionserkennung wurde an verschiedenen Motivtypen getestet:

- detaillierte Landschaft
- stark ornamentierter Pfau
- Porträt mit Haaren und Blumen
- Beeren- und Blattmotive
- Hund mit farbigen Teilflächen ohne schwarze Trennung
- tropische Motive mit vielen schmalen Blättern

Diese Tests haben direkt zu den verschiedenen Erkennungsmodi geführt.

---

# 15. Nächste geplante Themen

## 15.1 SVG-Outline

Nächster sinnvoller Schritt:

- Outline als eigene Gruppe im Game SVG speichern
- Game Areas zuerst
- Outline zuletzt
- optional weiterhin Outline PNG exportieren

Geplante Struktur:

```xml
<svg>
    <g id="game_areas">
        ...
    </g>

    <g id="outlines">
        ...
    </g>
</svg>
```

## 15.2 Exportformat finalisieren

Vor dem Godot Importer soll das Austauschformat fest definiert werden.

Zu klären:

- welche Informationen ausschließlich im JSON liegen
- welche Metadaten zusätzlich im SVG stehen
- ob die Outline als echte Vektorpfade oder rasterbasierter Fallback exportiert wird
- Umgang mit Overlay-Regionen
- Umgang mit ungegruppierten Regionen

## 15.3 Godot Importer

Danach:

```text
Game SVG
+ Game JSON
↓
Godot Importer
↓
GameArea Nodes
↓
Polygon2D Children
↓
Label
↓
Farb-ID / Zielfarbe
```

## 15.4 Klicklogik

Eine Game Area gilt als ein einziges interaktives Objekt.

Ein Klick auf eines ihrer Polygone färbt alle Polygone der Gruppe.

## 15.5 Performance-Test

Test mit komplexen Seiten:

- mehrere hundert technische Regionen
- 50 bis 150 Game Areas
- starke Zoomstufen
- Desktop
- später Tablet / Mobile

---

# 16. Aktuell wichtigste Architekturentscheidung

Technische Region und Game Area bleiben getrennt.

Das ist der zentrale Punkt des gesamten Systems.

```text
Technische Region
= geometrische Teilfläche

Game Area
= spielerische Einheit
```

Dadurch können:

- mehrere Polygone gleichzeitig gefärbt werden
- dekorative Linien erhalten bleiben
- komplexe Motive ohne komplizierte Polygon-Booleans verarbeitet werden
- kleine Farb-Overlays unabhängig von Grundflächen existieren
- Godot später eine sehr klare Spiellogik verwenden

---

# 17. Aktueller Stand für den nächsten Arbeitsblock

**Release-Stand:** `v0.10.0`

**Noch nicht released:**

- geplante SVG-Outline-Erweiterung
- endgültiger Godot-Importer
- finales Austauschformat

Empfohlener nächster Branch:

```bash
feature/svg-outline-export
```

Danach voraussichtlich:

```bash
feature/godot-importer
```

---

# 18. Repository- und Tooling-Setup (Stand 2026-09-16)

## GitHub

Repository: `https://github.com/Arako969/svg-extractor.git`

Die komplette Versionshistorie `v0.1.0` bis `v0.10.0` wurde nachträglich als einzelne Commits mit passenden Git-Tags abgebildet, sodass jeder Entwicklungsschritt aus `CHANGELOG.md` einem eigenen Commit entspricht.

`Grafik Library/` (Quell-Artwork, PNGs) sowie `.DS_Store` sind über `.gitignore` bewusst vom Repository ausgeschlossen.

## Start ohne Terminal

`Coloring Region Extractor.command` ist ein macOS-Finder-Launcher: prüft Python 3 und die benötigten Pakete, bietet bei fehlenden Paketen die automatische Installation über `requirements.txt` an und startet danach `coloring_region_extractor_gui.py`.

## Kontext für KI-Unterstützung

- `CLAUDE.md`: Architektur- und Befehlsüberblick für Claude Code, damit ein neuer Chat/Agent sich schnell zurechtfindet, ohne den Quellcode komplett neu zu erschließen.
- `DEVELOPMENT-HANDOFF.md`: sehr kompakte Momentaufnahme (aktueller Release, aktueller Branch, aktuell offener Arbeitsschritt) für den Wechsel in einen neuen Chat, ohne die volle Historie zu wiederholen. Wird am Ende größerer Arbeitseinheiten zusammen mit diesem Dokument aktualisiert.

---

# 19. Kurzfazit

Der Coloring Region Extractor hat sich von einem einfachen Connected-Components-Prototypen zu einem spezialisierten Produktionswerkzeug entwickelt.

Der aktuelle Ansatz kombiniert:

- klassische Bildverarbeitung
- Farbsegmentierung
- Vektorregionen
- manuelle Korrektur
- logische Game Areas
- automatische Farbzuordnung

Damit ist die Content-Vorbereitung inzwischen weitgehend unabhängig von Illustrator möglich und eignet sich wesentlich besser für einen größeren Bestand an Coloring-Book-Artworks.
