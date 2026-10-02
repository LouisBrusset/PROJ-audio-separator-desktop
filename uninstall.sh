#!/usr/bin/env bash
# Retire le lanceur et l'icône. Le dossier du projet et les modèles téléchargés sont conservés.
set -euo pipefail

APP_ID="audio-separator-local"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

rm -f "$DATA_HOME/applications/$APP_ID.desktop"
rm -f "$DATA_HOME/icons/hicolor/scalable/apps/$APP_ID.svg"
update-desktop-database "$DATA_HOME/applications" >/dev/null 2>&1 || true
gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo "Lanceur supprimé."
echo "Pour tout effacer : supprime le dossier du projet et ~/.cache/audio-separator-models"
