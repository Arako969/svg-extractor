# Git-Workflow & Versionierung

## Versionierung

Semantic Versioning: `vMAJOR.MINOR.PATCH`.

Die aktuelle Version steht zusätzlich in `VERSION`.

- PATCH: kleiner Bugfix, keine neue Funktion
- MINOR: neue Funktion oder neuer Themenbereich
- MAJOR: grundlegender Umbruch oder erster produktiver 1.0-Stand

`CHANGELOG.md` wird nur bei Releases erweitert.

`PROJECT-STATUS.md` enthält den laufenden Arbeitsstand und darf zwischen Releases aktualisiert werden.

## Branches

- `main`: immer lauffähiger aktueller Stand
- `feature/<kurzname>`: neue Funktion
- `fix/<kurzname>`: Bugfix
- `chore/<kurzname>`: Aufräumen, Doku, Konfiguration

Änderungen werden per Pull Request nach `main` übernommen.

## Commit-Nachrichten

Kurzer deutscher Imperativ, zum Beispiel:

`Farbbasierte Unterregionen ergänzen`

## PR-Titel

Solange nach einem Phasenplan gearbeitet wird:

`Phase N: Beschreibung`

## Ablauf A: Themenbereich beginnen

```bash
git checkout main
git pull
git checkout -b feature/<kurzname>
```

Zwischenstände:

```bash
git add -A
git commit -m "Kurze Beschreibung der Änderung"
git push -u origin feature/<kurzname>
```

## Ablauf B: Feature fertig

```bash
git diff main...HEAD
gh pr create --fill
```

Nach ausdrücklicher Bestätigung:

```bash
gh pr merge --squash --delete-branch
```

## Ablauf C: Release

Nur bewusst und ausdrücklich:

```bash
git checkout main
git pull
```

Dann `VERSION` und `CHANGELOG.md` aktualisieren:

```bash
git add VERSION CHANGELOG.md
git commit -m "Version 0.11.0"
git tag v0.11.0
git push
git push --tags
```
