╔════════════════════════════════════════════════════════════╗
║  ROBOT OS - USB Installation für Raspberry Pi             ║
║  ROBOT OS VERSION 2.1.0                          ║
╚════════════════════════════════════════════════════════════╝

INSTALLATION - NUR 2 SCHRITTE:
═══════════════════════════════════════════════════════════

1. USB-Stick in den Raspberry Pi stecken

2. Terminal öffnen und ausführen:
   
   cd /media/pi/USB-NAME/robot-usb-deploy
   bash SETUP_DEPS.sh   <-- NEU: Installiert nötige Pakete
   bash INSTALL_PI.sh

   (Ersetze USB-NAME mit dem Namen deines USB-Sticks)

3. Fertig! Pi neu starten:
   
   sudo reboot


ALTERNATIVE (falls USB anders gemountet):
═══════════════════════════════════════════════════════════

1. USB-Stick finden:
   ls /media/pi/
   
2. Zum USB-Ordner wechseln:
   cd /media/pi/DEIN-USB/robot-usb-deploy
   
3. Script ausführen:
   bash INSTALL_PI.sh


WAS PASSIERT BEIM INSTALL:
═══════════════════════════════════════════════════════════

✓ Alle Python-Dateien werden kopiert
✓ Alle Assets (Grafiken, Sounds, Fonts) werden kopiert
✓ version.json wird kopiert
✓ Berechtigungen werden gesetzt

Das Script fragt dich nach dem Zielverzeichnis
(Standard: /home/bot/robot)


NEUE FEATURES:
═══════════════════════════════════════════════════════════

✓ ROBOT Boot-Screen beim Start
✓ Automatisches Update-System
✓ Optimierter Schlafmodus (17:00-7:00 & Wochenende)


PROBLEME?
═══════════════════════════════════════════════════════════

Falls das Script nicht läuft:
1. Berechtigungen prüfen: chmod +x INSTALL_PI.sh
2. Manuell kopieren: cp -r * /home/bot/robot/

Bei Fragen: Einfach melden!
