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
- Konturglättung
- geschlossene Bezier-Geometrie (Catmull-Rom, Tension `0.44`)
- konservative Douglas-Peucker-Vereinfachung
- zusätzliche Ankerpunkte in Bereichen höherer Krümmung
- einstellbare Pixel-Toleranz von `0,20` bis `1,20 px`

Qualitätspriorität: sichtbare Outline und geschlossene Geometrie vor maximaler Dateireduktion.

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

Details zur Entscheidung: `decisions/ADR-005-outline-mesh-for-godot.md`.

### Verantwortlichkeiten

- **JSON:** Gameplay-Geometrie (`points`), visuelle Füllgeometrie (`render_points`), Game-Area-Struktur, Farben, Labels, Prioritäten, Overlay-Metadaten sowie das triangulierte Outline-Mesh (`outline_mesh`).
- **SVG:** visuelle Fills und geglättete Outline (unverändert, weiterhin die primäre visuelle Darstellung).

## Weitere Exporte

- Outline PNG (`export_outline_png()`) mit schwarzer Linie und transparentem Hintergrund
- Preview PNG (`export_preview()`)
- Projektdatei (`save_project()` / `load_project()`) für vollständigen Editor-Roundtrip

## Nächster Integrationsschritt

Godot Importer entwickeln, der Game JSON v3 (inklusive `render_points` und `*.meshbin`) sowie das Game SVG in Game-Area-Nodes, Polygon2D-Children, Labels und Farbinformationen überführt.
