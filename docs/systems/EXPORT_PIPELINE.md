# Export-Pipeline

## Ziel

Der Export trennt visuelle Darstellung und Gameplay-Daten möglichst klar.

## Game SVG

Der aktuelle SVG-Export (`export_svg()`) enthält zwei wesentliche Ebenen:

```xml
<svg>
    <g id="game_areas">
        ...
    </g>
    <g id="outlines" data-role="visual-outline" pointer-events="none">
        ...
    </g>
</svg>
```

Die Game-Area-Füllungen liegen unter der Outline. Eine kontrollierte Überdeckung unter die schwarze Linie (`_svg_fill_points_with_outline_bleed`, `bleed_px=3`) verhindert sichtbare weiße Spalten.

### SVG-Outline seit v0.11.0 (released)

Die Outline wird eigenständig aus der binären Linienmaske erzeugt und nicht aus den Rändern einzelner Game Areas zusammengesetzt.

Die dokumentierte Pipeline umfasst:

- Signed-Distance-Feld
- symmetrische Glättung
- Extraktion der geglätteten Kontur
- Resampling
- Konturglättung (mit Eckenschutz, siehe unten)
- geschlossene Bezier-Geometrie: zentripetale Catmull-Rom-Parametrisierung (`alpha=0.5`), volle Tangenten (`_closed_curve_segments()`, `tension=1.0`)
- konservative Douglas-Peucker-Vereinfachung
- zusätzliche Ankerpunkte in Bereichen höherer Krümmung
- einstellbare Pixel-Toleranz von `0,20` bis `1,20 px`

Qualitätspriorität: sichtbare Outline und geschlossene Geometrie vor maximaler Dateireduktion.

#### Zentripetale Kurvensegmente mit Eckenschutz (SVG und Mesh gemeinsam)

`_closed_curve_segments()` ist die gemeinsame Quelle kubischer Bezier-Segmente für den SVG-Pfad (`_closed_catmull_rom_svg_path()`) und den Mesh-Ring (`_sample_closed_catmull_rom()`), damit beide Kurven nicht auseinanderlaufen:

- Zentripetale Parametrisierung (`alpha=0.5`, Zeitparameter aus Sehnenlängen) statt uniformer Parametrisierung, volle Tangenten (`tension=1.0`) statt der früheren Dämpfung.
- `_hard_corner_indices()` erkennt echte Ecken (Winkel ≥ 35° mit gerader Nachbarstützung, Geradheitsfehler ≤ 0.65 px über die benachbarten Abtastpunkte) und schützt sie vor Überglättung (`_smooth_closed_contour()`) und Wegfall bei der Vereinfachung (`_simplify_smooth_closed_contour()`); diese Anker erhalten getrennte Ein-/Austrittstangenten statt einer durchgehend geglätteten Kurve. Eng gerundete, tatsächlich runde Spitzen bleiben weich.
- Grund: Nach der adaptiven Mesh-Tessellierung blieben Knicke sichtbar — auch direkt in der SVG. Die Ursache lag in der Kurve selbst, nicht in der Abtastdichte.
- Details zur Korrektur/Historie: `../decisions/ADR-005-outline-mesh-for-godot.md`.

## Game JSON v3

Status: **auf `main` gemergt** (`export_game_json()`, PR #3 „Game-Export v3: explizite Regionsgeometrie für Godot“, Commit `bcc13d9`, 2026-09-18). Nicht mehr auf einem separaten Feature-Branch. Noch nicht Teil eines versionierten Releases — `VERSION`/`CHANGELOG.md` stehen weiterhin auf `v0.11.0`.

Formatkennung: `coloring_game_export_v3`.

### `regions`

Pro aktiver technischer Region wird unter anderem exportiert:

- `id`
- `points` — exakte Gameplay-/Hit-Test-Geometrie
- `render_points` — visuelle Füllgeometrie mit derselben Outline-Überdeckung wie der SVG-Export (`bleed_px=3`); ergänzt seit PR #4 (siehe unten)
- `centroid`
- `area`
- `bbox`
- `color_id`
- `target_color`, `target_color_hex`
- `parent_id`
- Overlay-, Micro-, Recovered- und Manual-Flags (`is_overlay`, `is_micro`, `is_recovered`, `is_manual`)
- `force_label`
- `priority`

### `game_areas`

- Manuelle Gruppen referenzieren mehrere `region_ids` und erhalten `is_implicit = false`.
- Ungruppierte aktive Regionen werden automatisch als Ein-Region-Game-Area mit `is_implicit = true` exportiert, sodass Godot keinen Sonderfall für ungruppierte Regionen benötigt.

### `outline_mesh` (seit PR #4, auf `main` gemergt)

Zusätzlich zu `regions` und `game_areas` schreibt `export_game_json()` ein trianguliertes Vektor-Outline-Mesh als eigenständige Binärdatei neben dem JSON (`_write_outline_mesh_binary()`):

- Dateiname: `<json-stem>_outline.meshbin`
- Binärformat `lcs_outline_mesh_v1`: 4-Byte-Signatur `LCSM`, `uint32` Version, `uint32` Vertex-Anzahl, `uint32` Index-Anzahl, gefolgt von den Vertices (`float32 x, y`) und Dreiecksindizes (`uint32`).
- Die Triangulierung nutzt dieselbe geglättete Outline-Kontur wie der SVG-Export, baut daraus über die OpenCV-Konturhierarchie Polygone mit Löchern (`_outline_mesh_rings()`, `_outline_mesh_data()`) und trianguliert sie mit Shapely (`constrained_delaunay_triangles`, `make_valid`).
- Benötigt die zusätzliche Abhängigkeit **`shapely`** (bereits in `requirements.txt`).
- Das Game JSON referenziert das Ergebnis über das Feld `outline_mesh` (`format`, `file`, `vertex_count`, `index_count`, `triangle_count`, `size_bytes`).
- Fehlt `shapely` oder schlägt die Triangulierung fehl, wird das Game JSON trotzdem gespeichert (`outline_mesh: null`); die GUI zeigt dazu eine Warnung.

#### Adaptive Tessellierung der Mesh-Kontur

Die Catmull-Rom-Segmente innerhalb von `_outline_mesh_rings()` werden für das Outline-Mesh nicht mehr mit einer festen Schrittzahl abgetastet, sondern über `_sample_cubic_bezier_adaptive()` fehlerbasiert unterteilt (De-Casteljau-Verfahren, `_sample_closed_catmull_rom(..., max_error=0.02)`):

- Standard-Fehlerbudget `0.02 px`, maximale Unterteilungstiefe `16`.
- Gerade Kurvenabschnitte erzeugen kaum Punkte, gekrümmte Abschnitte werden bis zum Erreichen der Toleranz unterteilt.
- Betrifft nur die Abtastdichte des triangulierten Outline-Mesh; der SVG-Outline-Export stellt kubische Bezier-Kurven nativ ohne Abtastung dar. Die zugrunde liegende Kurvenform selbst (Parametrisierung, Eckenschutz) ist seit `fix/outline-curve-corners` zwischen SVG und Mesh geteilt (siehe oben).
- Reduziert unnötig dichte Vertex-Verteilung in ruhigen Konturbereichen bei gegebener Kurve; behebt für sich genommen keine Knicke, die in der Kurve selbst liegen (siehe Korrektur oben und in `../decisions/ADR-005-outline-mesh-for-godot.md`).

Details zur Entscheidung: `../decisions/ADR-005-outline-mesh-for-godot.md`.

### Automatisierte Geometrietests

`tests/test_outline_mesh_geometry.py` deckt die Outline-Mesh-Pipeline als Regressionsschutz ab, bevor an der Kurvenglättung oder Konturerzeugung weitergearbeitet wird:

- Deterministisches und endliches Catmull-Rom-Sampling (`_sample_closed_catmull_rom`).
- Die adaptive Abtastung hält das Fehlerbudget (`max_error`) gegenüber der kubischen Bezier-Kurve ein.
- Gekrümmte Segmente erhalten mehr Abtastpunkte als gerade Segmente (`_sample_cubic_bezier_adaptive`).
- Ein kleineres Fehlerbudget erhöht die Abtastdichte.
- SVG-Pfad und Mesh-Ring nutzen dieselben Segmente auch bei kurzen/doppelten Ankerpunkten (`_closed_curve_segments`).
- Echte Ecken mit gerader Nachbarstützung werden erkannt und erhalten getrennte Tangenten, runde Bögen dagegen nicht (`_hard_corner_indices`).
- SVG-Ring und Mesh-Ring starten am selben Konturpunkt.
- Verarbeitung einer leeren Linienmaske (`_outline_mesh_data()` liefert ein leeres Mesh).
- Ein gültiges, degenerationsfreies Ring-Mesh mit erhaltener zentraler Aussparung.
- Den binären `LCSM`-v1-Export (`_write_outline_mesh_binary()`) auf Byte-Ebene.

Umfang: 10 Tests (Stand `fix/outline-curve-corners`).

Ausführung: `python3 -m unittest discover -s tests -v`, automatisiert per GitHub Actions (`.github/workflows/tests.yml`) bei Push/PR auf `main`.

### Verantwortlichkeiten

- **JSON:** Gameplay-Geometrie (`points`), visuelle Füllgeometrie (`render_points`), Game-Area-Struktur, Farben, Labels, Prioritäten, Overlay-Metadaten sowie das triangulierte Outline-Mesh (`outline_mesh`).
- **SVG:** visuelle Fills und geglättete Outline (unverändert, weiterhin die primäre visuelle Darstellung).

## Weitere Exporte

- Outline PNG (`export_outline_png()`) mit schwarzer Linie und transparentem Hintergrund
- Preview PNG (`export_preview()`)
- Projektdatei (`save_project()` / `load_project()`) für vollständigen Editor-Roundtrip

## Bekannte Grenzen des Exports

- Das Game JSON speichert keine Exportparameter (Schwelle, Lückenschluss, SVG-Outline-Toleranz); nur die Projektdatei (`save_project()`) enthält sie. Ein exportiertes Ergebnis ist daher nicht allein aus SVG, JSON und Mesh reproduzierbar (Zehn-Punkte-Plan, Punkt 7).
- SVG, JSON und Mesh werden über getrennte Exportfunktionen erzeugt; ein gemeinsamer, konsistenter Game-Paket-Export existiert noch nicht (Zehn-Punkte-Plan, Punkt 6). Die Konturaufbereitung wird in `_outline_svg_path_data()` und `_outline_mesh_rings()` getrennt, aber mit denselben Parametern und derselben Segmentfunktion berechnet.
- Die Eckenerkennung nutzt feste Grenzen (`35°`, `0.65 px`), siehe ADR-005.

## Nächste Arbeit am Export

Reihenfolge laut Zehn-Punkte-Plan in `../PROJECT_STATE.md`: zuerst Qualitätsstufen, danach Mesh-Vorschau, Game-Paket-Export und Exportparameter im JSON. Der Godot Importer für Game JSON v3 (inklusive `render_points` und `*.meshbin`) und das Game SVG ist separat geplant; seine Reihenfolge relativ zum Plan ist noch offen.
