#!/usr/bin/env bash
# Retire le lanceur et l'icône. Le dossier du projet et les modèles téléchargés sont conservés.
set -euo pipefail

APP_ID="PROJ-audio-separator-desktop"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

rm -f "$DATA_HOME/applications/$APP_ID.desktop"
rm -f "$DATA_HOME/icons/hicolor/scalable/apps/$APP_ID.svg"
update-desktop-database "$DATA_HOME/applications" >/dev/null 2>&1 || true
gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true

echo "Lanceur supprimé."

# Si install.sh a réutilisé un venv externe (.venv-path), il vit hors du dossier
# du projet : on propose de le supprimer à part, sans jamais le faire sans confirmation
# (ce venv peut être utilisé par autre chose que cette appli).
VENV_PATH_FILE="$APP_DIR/.venv-path"
if [ -s "$VENV_PATH_FILE" ]; then
    EXTERNAL_VENV="$(tr -d '[:space:]' < "$VENV_PATH_FILE")"
    if [ -n "$EXTERNAL_VENV" ] && [ -d "$EXTERNAL_VENV" ]; then
        if [ -t 0 ]; then
            read -r -p "Supprimer aussi le venv externe réutilisé ($EXTERNAL_VENV) ? [y/N] " answer
        else
            answer="n"
            echo "Pas de terminal interactif : le venv externe est conservé par défaut."
        fi
        case "$answer" in
            [yY]|[yY][eE][sS])
                rm -rf "$EXTERNAL_VENV"
                echo "Venv externe supprimé : $EXTERNAL_VENV"
                ;;
            *)
                echo "Venv externe conservé : $EXTERNAL_VENV"
                ;;
        esac
    fi
fi

echo "Pour tout effacer : supprime le dossier du projet et ~/.cache/audio-separator-models"
