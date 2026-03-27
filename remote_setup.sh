#!/bin/bash
# remote_setup.sh - Setup HEUM-tec on Raspberry Pi

TARGET_DIR="/home/bot/robot"
AUTOSTART_FILE="/home/bot/.config/lxsession/LXDE-pi/autostart"

echo "Starting remote setup in $TARGET_DIR..."

# Make scripts executable
chmod +x "$TARGET_DIR"/*.sh
chmod +x "$TARGET_DIR"/*.py

# Configure Autostart
echo "Configuring autostart..."
mkdir -p "$(dirname "$AUTOSTART_FILE")"

# Create a clean autostart file with only the necessary components
# Standard LXDE-pi components + the bot program
cat <<EOF > "$AUTOSTART_FILE"
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xset s off
@xset -dpms
@xset s noblank
python3 $TARGET_DIR/main.py &
EOF

echo "Autostart configured in $AUTOSTART_FILE"
echo "Setup complete. A reboot is recommended."
