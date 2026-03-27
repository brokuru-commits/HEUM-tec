#!/bin/bash
# CRITL OS - Einfaches Install-Script für Raspberry Pi
# Einfach ausführen mit: bash INSTALL_PI.sh

set -e  # Bei Fehler abbrechen

echo "================================================"
echo "  ROBOT OS - Installation auf Raspberry Pi"
echo "  ROBOT OS VERSION 2.1.0"
echo "================================================"
echo ""

# Finde das Script-Verzeichnis (USB-Stick)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "USB-Stick gefunden: $SCRIPT_DIR"
echo ""

# WICHTIG: Abhängigkeiten zuerst prüfen
if [ ! -f "/usr/bin/git" ] || [ ! -f "/usr/lib/python3/dist-packages/pygame/__init__.py" ]; then
    echo "WARNUNG: Es fehlen System-Abhängigkeiten!"
    echo "Bitte führe zuerst folgendes aus:"
    echo "  bash $SCRIPT_DIR/SETUP_DEPS.sh"
    echo ""
    read -p "Trotzdem fortfahren? (j/n): " DEP_CONFIRM
    if [ "$DEP_CONFIRM" != "j" ]; then exit 1; fi
fi

# Frage nach Zielverzeichnis
read -p "ROBOT OS Verzeichnis auf dem Pi [/home/bot/robot]: " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-/home/bot/robot}

echo ""
echo "Zielverzeichnis: $TARGET_DIR"
echo ""

# Bestätigung
read -p "Alle Dateien nach $TARGET_DIR kopieren? (j/n): " CONFIRM
if [ "$CONFIRM" != "j" ] && [ "$CONFIRM" != "J" ]; then
    echo "Abgebrochen."
    exit 0
fi

echo ""
echo "[1/3] Erstelle Zielverzeichnis..."
mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/assets"

echo "[2/3] Kopiere Dateien..."
# Kopiere alle Python-Dateien
cp -v "$SCRIPT_DIR"/*.py "$TARGET_DIR/" 2>/dev/null || true

# Kopiere version.json
cp -v "$SCRIPT_DIR"/version.json "$TARGET_DIR/" 2>/dev/null || true

# Kopiere Assets
if [ -d "$SCRIPT_DIR/assets" ]; then
    cp -rv "$SCRIPT_DIR/assets"/* "$TARGET_DIR/assets/" 2>/dev/null || true
fi

echo ""
echo "[3/3] Setze Berechtigungen..."
chmod +x "$TARGET_DIR"/*.py 2>/dev/null || true

echo ""
echo "[4/4] Aktualisiere Autostart-Konfiguration..."
# Suche nach alten Pfaden in Autostart-Dateien
OLD_PATHS=("/home/pi/critl-os" "/home/pi/HEUM-tec" "/home/martin/Dokumente/prog/HEUM-tec")
AUTOSTART_FILES=(
    "$HOME/.config/lxsession/LXDE-pi/autostart"
    "/etc/xdg/lxsession/LXDE-pi/autostart"
    "/etc/rc.local"
)

for FILE in "${AUTOSTART_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "Prüfe $FILE..."
        for OLD_PATH in "${OLD_PATHS[@]}"; do
            if grep -q "$OLD_PATH" "$FILE"; then
                echo "  -> Alten Pfad $OLD_PATH in $FILE gefunden. Aktualisiere auf $TARGET_DIR..."
                sudo sed -i "s|$OLD_PATH|$TARGET_DIR|g" "$FILE"
            fi
        done
        # Falls main.py direkt ohne Pfad oder mit anderem Pfad aufgerufen wird
        if grep -q "main.py" "$FILE" && ! grep -q "$TARGET_DIR/main.py" "$FILE"; then
            echo "  -> Unvollständigen Pfad für main.py in $FILE gefunden. Korrigiere..."
            # Ersetze die gesamte Zeile, die main.py enthält, durch den korrekten Aufruf
            sudo sed -i "s|.*main.py.*|python3 $TARGET_DIR/main.py \&|g" "$FILE"
        fi
    fi
done

echo ""
echo "================================================"
echo "  ✓ Installation und Pfad-Update abgeschlossen!"
echo "================================================"
echo ""
echo "ROBOT OS wurde installiert nach: $TARGET_DIR"
echo ""
echo "WICHTIG FÜR BOT-BENUTZER:"
echo "Da dein Benutzername 'bot' ist, wurde der Autostart"
echo "automatisch auf $TARGET_DIR angepasst."
echo ""
echo "Falls es beim Starten immer noch Probleme gibt:"
echo "Prüfe die Datei: ~/.config/lxsession/LXDE-pi/autostart"
echo ""
echo "Neustart empfohlen: sudo reboot"
echo ""
echo "Oder manuell testen:"
echo "  → cd $TARGET_DIR && python3 main.py"
echo ""
