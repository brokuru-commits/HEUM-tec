#!/bin/bash
# SETUP_DEPS.sh - Installs system dependencies for ROBOT OS on Raspberry Pi

set -e

echo "================================================"
echo "  ROBOT OS - System-Abhängigkeiten installieren"
echo "================================================"
echo ""

# Überprüfe auf Internetverbindung
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo "FEHLER: Keine Internetverbindung gefunden."
    echo "Bitte verbinde den Pi mit dem Internet und versuche es erneut."
    exit 1
fi

echo "[1/2] Aktualisiere Paketlisten..."
sudo apt-get update

echo "[2/2] Installiere Pakete (Python3, Pygame-Abhängigkeiten, Git)..."
# git: Für das Update-System
# python3-pygame: Installiert SDL und alle nötigen System-Abhängigkeiten für Pygame
# xscreensaver wurde entfernt, da er DPMS triggert und den Bildschirm schwarz schaltet
sudo apt-get install -y git python3-pygame

echo ""
echo "================================================"
echo "  ✓ Abhängigkeiten erfolgreich installiert!"
echo "================================================"
echo ""
echo "Du kannst jetzt INSTALL_PI.sh ausführen."
