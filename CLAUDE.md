# CLAUDE.md

Diese Datei liefert Claude Code (claude.ai/code) Kontext für die Arbeit mit dem Code in diesem Repository.

## Projekt

Coloring Region Extractor: ein Single-File-Tkinter-Desktop-Tool, das schwarz-weiße Coloring-Book-Outline-Bilder (optional mit koloriertem Referenzbild) in vektorbasierte "Game Areas" für ein späteres Malen-nach-Zahlen-System in Godot umwandelt. Die vollständige Begründung, verworfene Ansätze und offene Designfragen stehen in `PROJECT-STATUS.md` — dieses Dokument ist deutlich detaillierter als diese Datei und sollte für alles Architektonische konsultiert werden, was hier nicht abgedeckt ist.

## Befehle

```bash
# Abhängigkeiten installieren
python3 -m pip install -r requirements.txt

# App starten
python3 coloring_region_extractor_gui.py

# macOS-Finder-Launcher (prüft Python/Abhängigkeiten, startet dann die App)
./"Coloring Region Extractor.command"
```

Es gibt in diesem Repo keine Testsuite, keinen Linter und keinen Build-Schritt — die Verifikation erfolgt manuell über die GUI.

## Architektur

Alles befindet sich in einer einzigen Datei, `coloring_region_extractor_gui.py`, als eine einzelne Klasse `ColoringRegionExtractor(tk.Tk)` (~3700 Zeilen). `history/` enthält unveränderte Schnappschüsse vergangener Versionen (`_v1` … `_v10`) rein als Archiv — diese Dateien niemals bearbeiten; `v10` ist identisch mit dem aktuellen `coloring_region_extractor_gui.py`.

### Kern-Datenmodell

- **Region** (`self.regions: list[dict]`): eine technische, geometrisch geschlossene Fläche, die in der Outline gefunden wurde. Wichtige Felder: `id`, `source_label` (Index in `self.labels` aus `connectedComponentsWithStats`, oder `None` bei Regionen ohne zugrunde liegende rohe Outline-Komponente), `is_recovered`, `is_manual`, `active`, `priority`.
- **Priority** bestimmt, welche Region gewinnt, wenn sich Overlays an denselben Pixeln überlappen (höherer Wert gewinnt):
  - `0` — normale Region, durch Standard-Erkennung der geschlossenen Outline gefunden
  - `1` — farbbasierte Unterregion (aus einer größeren Outline-Region anhand der Farbvorlage herausgeschnitten, z. B. eine beige Pfote innerhalb eines orangefarbenen Hundekörpers)
  - `2` — Recovery-Region (ausschließlich aus der Farbvorlage rekonstruiert, wenn die Outline dort gar keine geschlossene Region lieferte)
  - `3` — manuell hinzugefügte Region (Nutzerklick über "Fehlende Fläche hinzufügen")
- **Gruppe / Game Area** (`self.groups: dict[int, dict]`): die *spielerische* Einheit — eine oder mehrere Region-IDs (`region_ids`), die sich bei einem einzigen Klick gemeinsam einfärben, mit einer `color_id`, einer `label_position` und einer `target_color`. Technische Region und Game Area sind bewusst getrennte Konzepte; eine Game Area wird nie zu einem einzigen Polygon zusammengeführt (siehe PROJECT-STATUS.md §16 für die Begründung).
- **Palette** (`self.palette: list[dict]`): im Lab-Farbraum geclusterte Farben, abgeleitet aus dem Farbreferenzbild; jede Region/Gruppe erhält eine `color_id`, die auf diese Palette verweist.

### Erkennungs-Pipeline (`analyze()` und verwandte Methoden)

1. Schwellenwert + morphologisches Closing auf der Graustufen-Outline → binäre Linienmaske.
2. `connectedComponentsWithStats` auf der invertierten Maske → Basisregionen (priority 0).
3. Optionaler zweiter Durchlauf ohne Lückenschließung für adaptive Mikroregionen (fängt winzige geschlossene Zellen ab, die Morphology sonst verschlucken würde).
4. Falls eine Farbvorlage geladen ist: `split_selected_regions_by_color()` schneidet farbbasierte Unterregionen (priority 1) aus großen Outline-Regionen heraus; `recover_missing_regions_from_color()` rekonstruiert Regionen, die die Outline-Erkennung komplett verpasst hat (priority 2).
5. `add_missing_region_at()` behandelt das manuelle Klick-zum-Hinzufügen-Werkzeug (priority 3), mit Fallback von bestehender Region → roher Outline-Komponente → Farbvorlagen-Insel.

### UI-Aufbau

Dreigeteiltes `ttk.Panedwindow`, aufgebaut in `_build_ui()`: scrollbare linke Sidebar (Analyse-/Farb-/Parameter-Steuerung), mittlere Canvas (zoom- und schwenkbare Vorschau über `_zoom_at`/`_do_pan`), rechte Sidebar (Auswahl, Gruppen-/Game-Area-Verwaltung, Export). Canvas-Klicks werden über `on_canvas_click()` je nach `self.mode_var` (`select` vs. Modus zum Hinzufügen fehlender Flächen) verarbeitet.

### Exportformate (siehe PROJECT-STATUS.md §8–9 für das Ziel-Schema)

- `export_svg()` — Game SVG mit Metadaten pro Region (`group-id`, `region-id`, `color-id`, Zielfarbe, Label-Position, `priority`, Recovered-/Manual-Flags). Eine geplante, aber noch nicht umgesetzte Änderung ist, die Outline selbst als eigene `<g id="outlines">`-Ebene über `<g id="game_areas">` zu legen.
- `export_game_json()` — vollständige Projektdaten: Quellbildpfade, Abmessungen, Palette, Game Areas, Farb-IDs/Zielfarben, Label-Positionen, ungruppierte aktive Regionen.
- `export_outline_png()` — transparentes PNG nur mit der schwarzen Outline.
- `export_preview()` — gerenderte Vorschau als PNG.
- `save_project()` / `load_project()` — vollständiges Roundtrip des Editor-Zustands (`_project_data()`), unabhängig von den obigen Exportformaten.

## Versionierung & Git-Workflow

Details in `GIT-WORKFLOW.md`; kurz zusammengefasst:

- Semantic Versioning (`vMAJOR.MINOR.PATCH`), festgehalten in `VERSION` und als Git-Tag markiert (`v0.1.0` … aktuell).
- `CHANGELOG.md` wird nur bei tatsächlichen Releases aktualisiert; `PROJECT-STATUS.md` wird zwischen Releases frei mit dem laufenden architektonischen/technischen Stand aktualisiert.
- Branches: `main` (immer lauffähig), `feature/<name>`, `fix/<name>`, `chore/<name>`, per PR gemergt.
- Commit-Nachrichten: kurzer deutscher Imperativ (z. B. `Farbbasierte Unterregionen ergänzen`).
- Releases werden nur auf ausdrückliche Entscheidung hin geschnitten — nicht jeder Merge erhöht `VERSION`/`CHANGELOG.md`.

## Hinweise

- `Grafik Library/` (Quell-Artwork, PNGs) ist bewusst per `.gitignore` ausgeschlossen — große Binärassets, kein Teil des Tool-Quellcodes.
- Deutsch ist durchgehend die Arbeitssprache: UI-Texte, Statusmeldungen, Commit-Nachrichten und Dokumentation. Neue nutzersichtbare Texte und Commit-Nachrichten entsprechend auf Deutsch halten, um zum bestehenden Stil zu passen.
