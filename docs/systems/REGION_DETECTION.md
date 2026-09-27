# Regionserkennung

## Zweck

Die Regionserkennung wandelt die schwarz-weiße Outline in technische Flächen um, die anschließend gefärbt, gruppiert und exportiert werden können.

## Basisablauf

1. Graustufen-Outline schwellenwerten.
2. Optional morphologisches Closing zum Schließen kleiner Lücken anwenden.
3. Auf der invertierten Maske Connected Components bestimmen.
4. Geschlossene weiße Bereiche als Basisregionen übernehmen.
5. Kleine Regionen abhängig von den Parametern filtern.
6. Optional den Bildrand als Begrenzung behandeln.

## Regionstypen

### Normale Region

Durch die Standarderkennung der geschlossenen Outline gefunden. Priorität `0`.

### Mikroregion

Durch einen zusätzlichen feineren Erkennungsdurchlauf ohne beziehungsweise mit geringerer Lückenschließung ergänzt. Gedacht für sehr kleine geschlossene Zellen, die durch Morphology verloren gehen können.

### Farbbasierte Unterregion

Wird anhand der Farbvorlage aus einer größeren Outline-Region herausgetrennt. Priorität `1`.

### Recovery-Region

Wird aus der Farbvorlage rekonstruiert, wenn die Outline keine brauchbare geschlossene Region liefert. Priorität `2`.

### Manuell ergänzte Region

Wird durch Nutzerinteraktion ergänzt. Priorität `3`.

## Prioritätsprinzip

Bei relevanten Überlagerungen gewinnt die spezifischere Region mit der höheren Priorität.

## Bekannte Grenzen

- Sehr kleine Regionen können durch Morphology verloren gehen.
- Offene oder beschädigte Konturen können Basisregionen verhindern.
- Nicht deckungsgleiche Farbvorlagen können farbbasierte Ergänzungen verfälschen.
