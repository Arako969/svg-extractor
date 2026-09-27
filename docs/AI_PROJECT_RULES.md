# Regeln für KI-gestützte Projektarbeit

Diese Regeln gelten für Claude Code und andere KI-Assistenten, die am Repository arbeiten.

## Sprache und Benennung

- Datei- und Ordnernamen der Projektdokumentation werden auf Englisch geführt.
- Inhalte der Projektdokumentation werden auf Deutsch geschrieben.
- Nutzersichtbare UI-Texte und Commit-Nachrichten bleiben entsprechend dem bestehenden Projektstil deutsch.

## Quellenpriorität bei Widersprüchen

Wenn zwei Quellen unterschiedliche Aussagen zum aktuellen Projektzustand enthalten, gilt folgende Priorität:

1. Verifizierter aktueller Quellcode und aktuelle Projektkonfiguration
2. `PROJECT_STATE.md`
3. `ARCHITECTURE.md`
4. relevante Dateien unter `docs/systems/`
5. akzeptierte ADRs unter `docs/decisions/`
6. `HANDOFF.md` für den unmittelbaren Arbeitsstand
7. `CHANGELOG.md` für veröffentlichte Historie
8. archivierte oder historische Dokumentation

Historische Dokumente dürfen niemals einen verifizierten aktuellen Zustand überschreiben.

## Vor Beginn einer Aufgabe

1. `PROJECT_STATE.md` lesen.
2. `HANDOFF.md` lesen, wenn die Aufgabe an laufende Arbeit anknüpft.
3. `ARCHITECTURE.md` lesen, wenn Architektur betroffen ist.
4. Nur die für die Aufgabe relevanten Dateien unter `docs/systems/` und `docs/decisions/` lesen.
5. Betroffenen Quellcode prüfen, bevor Annahmen aus Dokumentation übernommen werden.
6. Bei einem Widerspruch zwischen Dokumentation und Code den Widerspruch ausdrücklich behandeln und nicht stillschweigend raten.

## Während der Arbeit

- Keine historischen Dateien als aktuelle Spezifikation verwenden.
- Keine Informationen unnötig in mehreren Dokumenten duplizieren.
- Jede Wissensart in ihrer zuständigen Datei pflegen.
- Bedeutende Architekturentscheidungen als ADR dokumentieren.

## Definition von fertig

Eine Aufgabe, die dokumentiertes Verhalten, Architektur, Exportformate, Datenmodelle, Workflows oder den aktuellen Projektstatus verändert, ist erst abgeschlossen, wenn die betroffene Dokumentation aktualisiert wurde.

## Nach Abschluss einer Aufgabe

1. Prüfen, ob `PROJECT_STATE.md` geändert werden muss.
2. Betroffene Systemdokumentation aktualisieren.
3. `ARCHITECTURE.md` nur bei tatsächlichen Architekturänderungen aktualisieren.
4. Bei einer neuen bedeutenden technischen Entscheidung eine ADR anlegen.
5. `HANDOFF.md` auf den unmittelbar nächsten Arbeitsschritt aktualisieren.
6. `CHANGELOG.md` nur bei einem tatsächlichen Release aktualisieren.
7. Dokumentation auf neu entstandene Widersprüche prüfen.
8. Ersetzte Ansätze als veraltet markieren oder ins Archiv verschieben, statt sie als parallel aktuellen Zustand stehen zu lassen.

## Zuständigkeiten der zentralen Dateien

- `PROJECT_STATE.md`: Was ist jetzt aktuell?
- `HANDOFF.md`: Wo wurde unmittelbar aufgehört und was kommt als Nächstes?
- `ARCHITECTURE.md`: Wie ist das System grundsätzlich aufgebaut?
- `systems/`: Wie funktionieren einzelne Systeme aktuell?
- `decisions/`: Warum wurden wichtige Architekturentscheidungen getroffen?
- `CHANGELOG.md`: Was wurde tatsächlich veröffentlicht?
- `archive/`: Historische Information ohne Autorität über den aktuellen Zustand.
