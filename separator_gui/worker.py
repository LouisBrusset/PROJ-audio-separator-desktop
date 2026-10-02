"""Travail de séparation exécuté dans un thread séparé pour ne pas figer l'interface."""

from __future__ import annotations

import logging
import time
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from separator_gui.config import MODEL_DIR, expected_outputs, output_names


class SeparationWorker(QObject):
    log = Signal(str)
    file_started = Signal(int, int, str)  # index (à partir de 1), total, nom du fichier
    progress = Signal(int, int)  # fichiers terminés, total
    finished = Signal(int, int, int)  # réussis, ignorés, erreurs
    failed = Signal(str)  # traceback complet

    def __init__(
        self,
        files: list[Path],
        output_dir: Path,
        model_filename: str,
        output_format: str,
        single_stem: str | None,
        skip_existing: bool,
    ) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.model_filename = model_filename
        self.output_format = output_format
        self.single_stem = single_stem
        self.skip_existing = skip_existing
        self._cancel_requested = False

    def cancel(self) -> None:
        """Demande l'arrêt. Le morceau en cours est terminé avant de s'arrêter."""
        self._cancel_requested = True

    @Slot()
    def run(self) -> None:
        try:
            self._run()
        except Exception:
            self.failed.emit(traceback.format_exc())

    def _run(self) -> None:
        self.log.emit("Chargement de PyTorch et d'audio-separator…")
        # Imports tardifs : l'interface s'ouvre instantanément, torch n'est chargé qu'au lancement
        import torch
        from audio_separator.separator import Separator

        if torch.cuda.is_available():
            self.log.emit(f"GPU détecté : {torch.cuda.get_device_name(0)}")
        else:
            self.log.emit("Aucun GPU CUDA détecté, la séparation se fera sur le CPU (beaucoup plus lent).")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        separator = Separator(
            log_level=logging.WARNING,
            model_file_dir=str(MODEL_DIR),
            output_dir=str(self.output_dir),
            output_format=self.output_format,
            output_single_stem=self.single_stem,
        )
        self.log.emit(f"Chargement du modèle {self.model_filename} (téléchargé au premier usage)…")
        separator.load_model(model_filename=self.model_filename)

        total = len(self.files)
        ok = skipped = errors = 0
        for index, track in enumerate(self.files, start=1):
            if self._cancel_requested:
                self.log.emit("Séparation annulée.")
                break

            self.file_started.emit(index, total, track.name)
            targets = expected_outputs(track, self.output_dir, self.output_format, self.single_stem)

            if self.skip_existing and all(t.exists() for t in targets):
                skipped += 1
                self.log.emit(f"Ignoré, déjà séparé : {track.name}")
            else:
                start = time.monotonic()
                try:
                    separator.separate(str(track), output_names(track))
                    ok += 1
                    self.log.emit(f"Terminé en {time.monotonic() - start:.0f} s : {track.name}")
                except Exception as exc:
                    errors += 1
                    self.log.emit(f"Erreur sur {track.name} : {exc}")

            self.progress.emit(index, total)

        self.finished.emit(ok, skipped, errors)
