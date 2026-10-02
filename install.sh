#!/usr/bin/env bash
# Installe Audio Separator Local pour l'utilisateur courant (Fedora / GNOME).
# À relancer si tu déplaces le dossier du projet.
set -euo pipefail

APP_ID="PROJ-audio-separator-desktop"
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

cd "$APP_DIR"

# Si .venv-path contient un chemin existant, on complète ce venv-là (utile pour
# réutiliser un venv déjà équipé de torch/CUDA) au lieu de créer un ".venv" local.
VENV_PATH_FILE="$APP_DIR/.venv-path"
EXTERNAL_VENV=""
if [ -s "$VENV_PATH_FILE" ]; then
    EXTERNAL_VENV="$(tr -d '[:space:]' < "$VENV_PATH_FILE")"
fi

if [ -n "$EXTERNAL_VENV" ] && [ -d "$EXTERNAL_VENV" ]; then
    echo "==> Réutilisation du venv existant : $EXTERNAL_VENV"
    export UV_PROJECT_ENVIRONMENT="$EXTERNAL_VENV"
    VENV_BIN="$EXTERNAL_VENV/bin"
else
    if [ -n "$EXTERNAL_VENV" ]; then
        echo "Attention : $VENV_PATH_FILE pointe vers un dossier introuvable ($EXTERNAL_VENV)." >&2
        echo "            Création d'un venv local à la place." >&2
    fi
    VENV_BIN="$APP_DIR/.venv/bin"
fi

echo "==> Installation des dépendances (plusieurs minutes la première fois)…"
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
Exec="$VENV_BIN/$APP_ID" %F
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
