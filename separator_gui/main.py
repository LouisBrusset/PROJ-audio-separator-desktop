"""Point d'entrée de l'application."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from separator_gui.config import APP_ID, APP_NAME
from separator_gui.main_window import MainWindow


def main() -> None:
    # Lancée sans terminal (icône, raccourci Windows), la sortie standard peut être absente,
    # ce qui ferait planter les barres de progression tqdm d'audio-separator
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ID)
    app.setDesktopFileName(APP_ID)  # associe la fenêtre à son icône sous GNOME/Wayland

    # Fichiers passés en argument (glissés sur l'icône ou « Ouvrir avec »)
    initial_paths = [Path(arg) for arg in sys.argv[1:] if Path(arg).exists()]

    window = MainWindow(initial_paths)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
