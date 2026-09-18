#!/usr/bin/env bash
# WMAX — Helper script to pair Wear OS emulator with Phone emulator via ADB port forwarding
set -euo pipefail

echo "========================================================"
echo "  WMAX — Wear OS & Phone Emulator Pairing Tool"
echo "========================================================"

# Check if adb is installed
if ! command -v adb &> /dev/null; then
    echo "❌ Error: 'adb' command not found. Make sure Android SDK platform-tools is in your PATH."
    exit 1
fi

echo "🔍 Detecting running Android emulators and devices..."
DEVICES=$(adb devices | grep -v "List" | grep "device$" | awk '{print $1}')

if [ -z "$DEVICES" ]; then
    echo "⚠️  No running Android emulators found."
    echo "👉 Please start both a Wear OS emulator and a Phone emulator in Android Studio first."
    exit 1
fi

echo "Found connected device(s):"
echo "$DEVICES"
echo ""

echo "🔗 Setting up ADB TCP port forward for Wearable Data Layer (tcp:5601 -> tcp:5601)..."
adb -d forward tcp:5601 tcp:5601 2>/dev/null || adb forward tcp:5601 tcp:5601

echo "✅ Port forwarding established: tcp:5601 <-> tcp:5601"
echo ""

echo "🛡️ Granting runtime sensor permissions to WMAX Soat..."
for dev in $DEVICES; do
    echo "  Applying to device $dev..."
    adb -s "$dev" shell pm grant uz.nazorat.watch android.permission.BODY_SENSORS 2>/dev/null || true
    adb -s "$dev" shell pm grant uz.nazorat.watch android.permission.ACTIVITY_RECOGNITION 2>/dev/null || true
done

echo ""
echo "🎉 Pairing setup complete!"
echo "You can now open WMAX Soat and WMAX Hamroh — they will communicate via Google Play Services Data Layer."
