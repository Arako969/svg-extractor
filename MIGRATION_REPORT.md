# Migrationsbericht

## Zweck

Die bisherige Projektdokumentation wurde in klar getrennte Wissensbereiche überführt. Ziel ist, Widersprüche zwischen aktuellem Status, Historie, Planung und Architektur zu vermeiden.

## Ausgangsdateien

- `CLAUDE.md`
- `PROJECT-STATUS.md`
- `DEVELOPMENT-HANDOFF.md`
- `CHANGELOG.md`
- `GIT-WORKFLOW.md`
- `README.md`

## Wesentliche Änderungen

### `PROJECT-STATUS.md`

Die Datei vereinte aktuellen Status, Architektur, Systemdetails, Release-Historie, Entscheidungen, Git-Workflow und Planung. Diese Inhalte wurden auf spezialisierte Dateien verteilt.

Die Originaldatei bleibt unverändert unter `docs/archive/PROJECT_STATUS_LEGACY.md` erhalten.

### Behobener Dokumentationskonflikt

Die alte Planung führte den SVG-Outline-Export noch als nächsten Schritt, obwohl derselbe Stand bereits als mit `v0.11.0` veröffentlicht dokumentiert war. In der neuen Struktur ist SVG Outline als abgeschlossen dokumentiert und nicht mehr Teil der aktuellen Planung.

### README

Die alte README nannte `v0.10.0` als letzten historischen Stand. Die vorhandenen übrigen Dokumente bestätigen `v0.11.0`. Die README verweist nun auf `VERSION` als autoritative Release-Datei und nennt `v0.11.0` als zuletzt dokumentierten Release.

### Release-Historie

`CHANGELOG.md` bleibt die einzige zuständige Datei für veröffentlichte Releases.

### Git-Workflow

Der Git-Workflow wurde an die neue Dokumentationsstruktur angepasst. Die frühere Pflicht, die monolithische `PROJECT-STATUS.md` zu pflegen, wurde durch eine gezielte Prüfung der betroffenen Dokumente ersetzt.

## Neue Struktur

```text
CLAUDE.md
README.md
CHANGELOG.md
MIGRATION_REPORT.md

docs/
├── PROJECT_STATE.md
├── HANDOFF.md
├── ARCHITECTURE.md
├── AI_PROJECT_RULES.md
├── GIT_WORKFLOW.md
├── systems/
│   ├── REGION_DETECTION.md
│   ├── COLOR_SYSTEM.md
│   ├── GAME_AREAS.md
│   ├── EXPORT_PIPELINE.md
│   └── PROJECT_WORKFLOW.md
├── decisions/
│   ├── ADR-001-region-game-area-separation.md
│   ├── ADR-002-vector-regions-over-pixel-flood-fill.md
│   ├── ADR-003-json-gameplay-geometry.md
│   └── ADR-004-separate-svg-outline.md
└── archive/
    └── PROJECT_STATUS_LEGACY.md
```

## Bewusst nicht als sicher verifiziert (Stand vor Verifikation)

Da für die Migration nur die Markdown-Dateien vorlagen, wurden Aussagen über den tatsächlichen Code zunächst nicht unabhängig geprüft. Besonders der Status von `feature/game-export-v3` sollte beim Einspielen in das Repository gegen den realen Branch geprüft werden.

## Empfohlene Übernahme

Die neue Struktur sollte zunächst in einem separaten Branch oder Commit in das bestehende Repository übernommen werden. Danach sollten Pfade und Aussagen gegen den aktuellen Code geprüft werden. Erst anschließend sollte die alte `PROJECT-STATUS.md` im Repository durch die archivierte Fassung ersetzt werden.

## Verifizierung gegen Quellcode und Git-Historie (27.09.2026)

Die oben offen gelassene Prüfung wurde durchgeführt (Branch `docs/documentation-migration`), gegen `coloring_region_extractor_gui.py`, `requirements.txt`, `VERSION`, Git-Log, -Tags und -Branches.

### Gefundene und korrigierte Widersprüche

1. **Game Export v3 ist bereits gemergt.** Die migrierte Doku übernahm unverändert die Aussage „getestet, aber noch nicht gemerged“ aus der alten `PROJECT-STATUS.md`. Tatsächlich ist `feature/game-export-v3` bereits per PR #3 (Commit `bcc13d9`, 2026-09-18) nach `main` gemergt. Es existiert aktuell kein offener Feature-Branch. Korrigiert in `PROJECT_STATE.md`, `HANDOFF.md`, `systems/EXPORT_PIPELINE.md`, `systems/GAME_AREAS.md`, `decisions/ADR-003-json-gameplay-geometry.md`.
2. **Eine vollständig undokumentierte, bereits gemergte Funktion fehlte.** PR #4 „Vektor-Outline-Mesh und Render-Geometrie für Godot“ (Commit `9c2dd17`, 2026-09-19) ergänzt `render_points` pro Region sowie ein trianguliertes Outline-Mesh-Binärformat (`*_outline.meshbin`, `lcs_outline_mesh_v1`, neue Abhängigkeit `shapely`). Diese Änderung betraf ausschließlich `coloring_region_extractor_gui.py`/`requirements.txt`, nie eine der alten Markdown-Dateien, und tauchte deshalb in keiner migrierten Doku auf. Ergänzt in `PROJECT_STATE.md`, `HANDOFF.md`, `ARCHITECTURE.md`, `systems/EXPORT_PIPELINE.md` sowie als neue `decisions/ADR-005-outline-mesh-for-godot.md`.
3. **`main` liegt vor dem letzten Tag/Release.** `VERSION` und `CHANGELOG.md` stehen weiterhin auf `v0.11.0`; die beiden oben genannten Arbeitseinheiten sind gemergt, aber nicht versioniert. Dies war in keiner Version der Doku als offene Versionsentscheidung sichtbar gemacht. Ergänzt in `PROJECT_STATE.md` und `HANDOFF.md`.
4. **`history/`-Schnappschüsse sind veraltet.** Die alte Behauptung „`v10` ist identisch mit dem aktuellen `coloring_region_extractor_gui.py`“ stimmte nur bis zum SVG-Outline-Export (`v0.11.0`, PR #2); seither ist `history/coloring_region_extractor_gui_v10.py` byteidentisch mit dem Stand vor PR #2, aber nicht mehr mit dem aktuellen Stand. Korrigiert in `ARCHITECTURE.md` und `PROJECT_STATE.md`.
5. **Projektname/Branding veraltet.** Die (aus der alten `DEVELOPMENT-HANDOFF.md` übernommene) Formulierung „Coloring Region Extractor für Cozy Desk / Little Color Studio“ widerspricht dem aktuellen Studio-Vault, in dem das Projekt durchgängig als „Cosy Desk - The Coloring Atelier“ geführt wird. Korrigiert in `HANDOFF.md`.

### Nicht eindeutig aus Quellcode oder Git-Verlauf verifizierbar

- Ob und wann eine Versionsentscheidung für den `main`-Stand (Game Export v3 + Outline-Mesh) getroffen wird, ist eine offene Produktentscheidung und nicht aus Code/Historie ableitbar.
- Ob PR #3/#4 bereits am realen Godot-Projekt (außerhalb dieses Repositories) getestet wurden, lässt sich aus diesem Repository allein nicht feststellen; die Doku übernimmt dazu weiterhin nur die Formulierung „laut bisheriger Dokumentation getestet“.
- Die konkreten Verifikations-Messwerte aus der alten `PROJECT-STATUS.md` §9 (z. B. Ankerpunkt-Reduktion am Motiv „dog-in-garden“) wurden nicht erneut nachgemessen; sie stehen unverändert nur in `archive/PROJECT_STATUS_LEGACY.md`.

### Nicht (mehr) als offene Prüfung geführte Dateien

Alle übrigen migrierten Dateien (`AI_PROJECT_RULES.md`, `GIT_WORKFLOW.md`, `systems/REGION_DETECTION.md`, `systems/COLOR_SYSTEM.md`, `systems/PROJECT_WORKFLOW.md`, `decisions/ADR-001`, `ADR-002`, `ADR-004`, `README.md`, `CHANGELOG.md`) wurden gegen Quellcode-Defaults (u. a. `threshold_var=190`, `close_size_var=3`, `simplify_var=1.5`) und Release-Tags geprüft und ohne inhaltliche Korrektur übernommen.
