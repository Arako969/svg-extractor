# Architektur

## Überblick

Der Coloring Region Extractor ist ein Single-File-Python/Tkinter-Desktop-Werkzeug. Die Hauptimplementierung liegt in `coloring_region_extractor_gui.py` als Klasse `ColoringRegionExtractor(tk.Tk)`.

Die Verarbeitung folgt grundsätzlich dieser Pipeline:

```text
Outline PNG
+ optionale Farbvorlage
        ↓
Regionserkennung
        ↓
Farbzuordnung und Korrekturen
        ↓
technische Regionen
        ↓
Gruppierung zu Game Areas
        ↓
SVG + JSON (+ Outline-Mesh) + optional Outline PNG / Preview
        ↓
Godot Importer (geplant)
```

## Kern-Datenmodell

### Technische Region (`self.regions: list[dict]`)

Eine geometrisch geschlossene oder rekonstruierte Teilfläche. Wichtige Felder: `id`, `source_label` (Index in `self.labels` aus `connectedComponentsWithStats`, oder `None` bei Regionen ohne zugrunde liegende rohe Outline-Komponente), `points`, `centroid`, `area`, `bbox`, `active`, `priority`, `parent_id`, `is_overlay`, `is_micro`, `is_recovered`, `is_manual`, `force_label`.

Prioritäten (höherer Wert gewinnt bei Überlagerungen):

- `0`: normale Region (Standarderkennung der geschlossenen Outline)
- `1`: farbbasierte Unterregion (aus einer größeren Outline-Region anhand der Farbvorlage herausgeschnitten)
- `2`: Recovery-Region (ausschließlich aus der Farbvorlage rekonstruiert)
- `3`: manuell hinzugefügte Region (Nutzerklick über „Fehlende Fläche hinzufügen“)

### Game Area (`self.groups: dict[int, dict]`)

Die spielerische Einheit — eine oder mehrere Region-IDs (`region_ids`), die sich bei einem einzigen Klick gemeinsam einfärben, mit `color_id`, `label_position` und `target_color`.

Die Trennung zwischen Region und Game Area ist eine verbindliche Architekturentscheidung: eine Game Area wird nie zu einem einzigen Polygon zusammengeführt. Siehe `decisions/ADR-001-region-game-area-separation.md`.

### Palette (`self.palette: list[dict]`)

Im Lab-Farbraum geclusterte Farben, abgeleitet aus dem Farbreferenzbild. Jede Region/Gruppe erhält eine `color_id`, die auf diese Palette verweist.

## Regionserkennung

Die Outline wird binär analysiert. Connected Components bilden die Basisregionen. Zusätzliche Mechanismen ergänzen kleine, farbbasierte, rekonstruierte oder manuell hinzugefügte Flächen.

Details: `systems/REGION_DETECTION.md`.

## Farbverarbeitung

Eine optionale kolorierte Referenz dient zur Ermittlung repräsentativer Ziel-Farben und zur Bildung einer reduzierten Palette. Sehr dunkle und sehr helle Pixel können gefiltert werden.

Details: `systems/COLOR_SYSTEM.md`.

## Game Areas

Mehrere technische Regionen können zu einer gemeinsamen spielerischen Fläche gruppiert werden. Ein späterer Klick auf eine Teilregion soll die gesamte Game Area behandeln.

Details: `systems/GAME_AREAS.md`.

## Export

Der aktuelle SVG-Export (`export_svg()`) trennt Game Areas und visuelle Outline. Game JSON v3 (`export_game_json()`, `coloring_game_export_v3`, auf `main` gemergt) stellt die vollständige Gameplay-Geometrie (`points`), visuelle Füllgeometrie (`render_points`) und Game-Area-Struktur explizit bereit, damit Godot keine SVG-Pfade für die Spiellogik parsen muss. Zusätzlich wird ein trianguliertes Vektor-Outline-Mesh (`*_outline.meshbin`) für Godot exportiert (benötigt `shapely`).

Details und aktueller Merge-/Versionsstand: `systems/EXPORT_PIPELINE.md`, `decisions/ADR-003-json-gameplay-geometry.md`, `decisions/ADR-005-outline-mesh-for-godot.md`.

## UI

Die Oberfläche verwendet ein dreigeteiltes `ttk.Panedwindow`, aufgebaut in `_build_ui()`:

- scrollbare linke Sidebar für Analyse, Farben und Parameter
- mittlere Canvas für Vorschau, Zoom (`_zoom_at`) und Pan (`_do_pan`)
- rechte Sidebar für Auswahl, Gruppen-/Game-Area-Verwaltung und Export

Canvas-Klicks werden über `on_canvas_click()` je nach `self.mode_var` (`select` vs. Modus zum Hinzufügen fehlender Flächen) verarbeitet.

## Historische Implementierungen

Der Ordner `history/` enthält unveränderte historische Python-Schnappschüsse (`_v1` … `_v10`) und ist nicht für aktive Änderungen vorgesehen. Die Schnappschüsse enden beim Stand von `v0.10.0`: `history/coloring_region_extractor_gui_v10.py` ist seit dem SVG-Outline-Export (`v0.11.0`) nicht mehr identisch mit dem aktuellen `coloring_region_extractor_gui.py` und wurde seither nicht fortgeführt.
