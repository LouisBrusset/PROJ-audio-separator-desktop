#!/usr/bin/env bash
# Installe Audio Separator Local pour l'utilisateur courant (Fedora / GNOME).
# À relancer si tu déplaces le dossier du projet.
set -euo pipefail

APP_ID="audio-separator-local"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DESKTOP_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv est introuvable. Installe-le avec : sudo dnf install uv" >&2
    exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Attention : ffmpeg est introuvable. Installe-le avec : sudo dnf install ffmpeg-free" >&2
fi

echo "==> Installation des dépendances (plusieurs minutes la première fois)…"
cd "$APP_DIR"
uv sync

echo "==> Installation de l'icône et du lanceur…"
mkdir -p "$DESKTOP_DIR" "$ICON_DIR"
cp "$APP_DIR/separator_gui/assets/$APP_ID.svg" "$ICON_DIR/$APP_ID.svg"

cat > "$DESKTOP_DIR/$APP_ID.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Audio Separator Local
GenericName=Séparateur voix et instrumentale
Comment=Extraire l'instrumentale ou la voix de fichiers audio
Exec="$APP_DIR/.venv/bin/$APP_ID" %F
Icon=$APP_ID
Terminal=false
Categories=AudioVideo;Audio;
MimeType=audio/mpeg;audio/flac;audio/x-wav;audio/ogg;
StartupWMClass=$APP_ID
StartupNotify=true
DESKTOP

update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo
echo "Installation terminée."
echo "Cherche « Audio Separator Local » dans les Activités (touche Super)."
