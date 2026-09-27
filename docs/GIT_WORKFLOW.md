# Git-Workflow und Versionierung

## Versionierung

Semantic Versioning: `vMAJOR.MINOR.PATCH`.

Die aktuelle Version steht zusätzlich in `VERSION`.

- PATCH: kleiner Bugfix ohne neue Funktion
- MINOR: neue Funktion oder neuer Themenbereich
- MAJOR: grundlegender Umbruch oder produktiver 1.0-Stand

`CHANGELOG.md` wird nur bei tatsächlichen Releases erweitert.

## Branches

- `main`: lauffähiger aktueller Stand
- `feature/<kurzname>`: neue Funktion
- `fix/<kurzname>`: Bugfix
- `chore/<kurzname>`: Aufräumen, Dokumentation oder Konfiguration

Änderungen werden per Pull Request nach `main` übernommen.

## Commit-Nachrichten

Kurzer deutscher Imperativ, zum Beispiel:

`Farbbasierte Unterregionen ergänzen`

## Dokumentationspflicht

Nach einer größeren Arbeitseinheit müssen die betroffenen Dokumente gemäß `AI_PROJECT_RULES.md` aktualisiert werden.

Mindestens prüfen:

- `PROJECT_STATE.md`
- relevante Systemdokumentation
- `ARCHITECTURE.md` bei Architekturänderungen
- neue oder geänderte ADR bei bedeutenden Entscheidungen
- `HANDOFF.md`

`CHANGELOG.md` nur bei einem tatsächlichen Release ändern.

## Feature beginnen

```bash
git checkout main
git pull
git checkout -b feature/<kurzname>
```

## Zwischenstand

```bash
git add -A
git commit -m "Kurze Beschreibung der Änderung"
git push -u origin feature/<kurzname>
```

## Feature fertigstellen

```bash
git diff main...HEAD
gh pr create --fill
```

Nach ausdrücklicher Bestätigung:

```bash
gh pr merge --squash --delete-branch
```

## Release

Nur bewusst und ausdrücklich. Danach `VERSION` und `CHANGELOG.md` aktualisieren, committen, taggen und pushen.
