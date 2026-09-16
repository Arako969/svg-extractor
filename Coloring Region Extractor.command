#!/bin/bash

# Coloring Region Extractor macOS Finder launcher
# Starts the Python GUI from the same directory and checks dependencies first.

cd "$(dirname "$0")"

clear
echo "Coloring Region Extractor"
echo "========================="
echo

# Find Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 wurde nicht gefunden."
    echo
    echo "Bitte installiere Python 3 und starte diese Datei danach erneut."
    echo "Download: https://www.python.org/downloads/macos/"
    echo
    read -n 1 -s -r -p "Beliebige Taste zum Schliessen ..."
    exit 1
fi

echo "Python:"
python3 --version
echo

# Check required modules.
python3 - <<'PY'
import importlib.util
import sys

required = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "numpy": "numpy",
}

missing = [
    package
    for module, package in required.items()
    if importlib.util.find_spec(module) is None
]

if missing:
    print("MISSING:" + ",".join(missing))
    sys.exit(2)

print("Alle benoetigten Python-Pakete sind vorhanden.")
PY

CHECK_STATUS=$?

if [ "$CHECK_STATUS" -eq 2 ]; then
    echo
    echo "Es fehlen Python-Pakete."
    echo
    read -r -p "Jetzt automatisch installieren? [j/N] " answer

    case "$answer" in
        j|J|y|Y)
            echo
            echo "Installiere Abhaengigkeiten ..."
            python3 -m pip install -r requirements.txt

            if [ $? -ne 0 ]; then
                echo
                echo "Die Installation ist fehlgeschlagen."
                echo "Bitte kopiere die Fehlermeldung und sende sie im Chat."
                echo
                read -n 1 -s -r -p "Beliebige Taste zum Schliessen ..."
                exit 1
            fi
            ;;
        *)
            echo
            echo "Start abgebrochen."
            read -n 1 -s -r -p "Beliebige Taste zum Schliessen ..."
            exit 1
            ;;
    esac
elif [ "$CHECK_STATUS" -ne 0 ]; then
    echo
    echo "Die Abhaengigkeitspruefung ist fehlgeschlagen."
    read -n 1 -s -r -p "Beliebige Taste zum Schliessen ..."
    exit 1
fi

echo
echo "Starte Coloring Region Extractor ..."
echo

python3 coloring_region_extractor_gui.py
APP_STATUS=$?

if [ "$APP_STATUS" -ne 0 ]; then
    echo
    echo "Das Programm wurde mit einem Fehler beendet."
    echo "Fehlercode: $APP_STATUS"
    echo
    read -n 1 -s -r -p "Beliebige Taste zum Schliessen ..."
fi
