"""Fenêtre principale de l'application."""

from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from separator_gui.config import (
    APP_ID,
    APP_NAME,
    AUDIO_EXTENSIONS,
    ICON_PATH,
    MODELS,
    OUTPUT_FORMATS,
    STEMS,
    collect_audio_files,
    default_output_dir,
    music_dir,
)
from separator_gui.worker import SeparationWorker


class DropList(QListWidget):
    """Liste qui accepte le glisser-déposer de fichiers et de dossiers."""

    paths_dropped = Signal(list)

    PLACEHOLDER = "Glisse ici des fichiers audio ou des dossiers\nou utilise les boutons ci-dessous"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumHeight(150)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.paths_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self.PLACEHOLDER)
            painter.end()


class MainWindow(QMainWindow):
    def __init__(self, initial_paths: list[Path] | None = None) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon.fromTheme(APP_ID, QIcon(str(ICON_PATH))))
        self.resize(780, 760)

        self.settings = QSettings(APP_ID, APP_ID)
        self.sources: list[Path] = []
        self.thread: QThread | None = None
        self.worker: SeparationWorker | None = None

        self._build_ui()
        self._load_settings()
        if initial_paths:
            self.add_sources(initial_paths)
        self._refresh_count()
        self._update_buttons()

    # ------------------------------------------------------------------ interface

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        # Sources
        sources_box = QGroupBox("Fichiers à séparer")
        sources_layout = QVBoxLayout(sources_box)
        self.source_list = DropList()
        self.source_list.paths_dropped.connect(self.add_sources)
        self.source_list.itemSelectionChanged.connect(self._update_buttons)
        sources_layout.addWidget(self.source_list)

        sources_row = QHBoxLayout()
        self.btn_add_files = QPushButton("Ajouter des fichiers…")
        self.btn_add_folder = QPushButton("Ajouter un dossier…")
        self.btn_remove = QPushButton("Retirer la sélection")
        self.btn_clear = QPushButton("Tout retirer")
        self.btn_add_files.clicked.connect(self._choose_files)
        self.btn_add_folder.clicked.connect(self._choose_folder)
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_clear.clicked.connect(self._clear_sources)
        for button in (self.btn_add_files, self.btn_add_folder, self.btn_remove, self.btn_clear):
            sources_row.addWidget(button)
        sources_row.addStretch()
        self.count_label = QLabel()
        sources_row.addWidget(self.count_label)
        sources_layout.addLayout(sources_row)
        root.addWidget(sources_box, stretch=2)

        # Paramètres
        self.params_box = QGroupBox("Paramètres")
        form = QFormLayout(self.params_box)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for label, filename in MODELS:
            self.model_combo.addItem(label, filename)
        self.model_combo.setToolTip(
            "Tu peux aussi taper le nom de fichier d'un autre modèle\n"
            "(liste complète : audio-separator --list_models)"
        )
        form.addRow("Modèle :", self.model_combo)

        self.stem_combo = QComboBox()
        for label, value in STEMS:
            self.stem_combo.addItem(label, value)
        form.addRow("Pistes à garder :", self.stem_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItems(OUTPUT_FORMATS)
        form.addRow("Format de sortie :", self.format_combo)

        self.recursive_check = QCheckBox("Inclure les sous-dossiers")
        self.recursive_check.toggled.connect(self._refresh_count)
        form.addRow("", self.recursive_check)

        self.skip_check = QCheckBox("Ignorer les morceaux déjà séparés dans le dossier de sortie")
        form.addRow("", self.skip_check)
        root.addWidget(self.params_box)

        # Dossier de sortie
        self.output_box = QGroupBox("Dossier de sortie")
        output_row = QHBoxLayout(self.output_box)
        self.output_edit = QLineEdit()
        btn_browse = QPushButton("Choisir…")
        btn_default = QPushButton("Par défaut")
        btn_open = QPushButton("Ouvrir")
        btn_browse.clicked.connect(self._choose_output)
        btn_default.clicked.connect(lambda: self.output_edit.setText(str(default_output_dir())))
        btn_open.clicked.connect(self._open_output)
        output_row.addWidget(self.output_edit, stretch=1)
        output_row.addWidget(btn_browse)
        output_row.addWidget(btn_default)
        output_row.addWidget(btn_open)
        root.addWidget(self.output_box)

        # Lancement
        run_row = QHBoxLayout()
        self.btn_run = QPushButton("Lancer la séparation")
        self.btn_run.setMinimumHeight(40)
        bold = QFont(self.btn_run.font())
        bold.setBold(True)
        self.btn_run.setFont(bold)
        self.btn_run.clicked.connect(self.start)
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.clicked.connect(self.cancel)
        run_row.addWidget(self.btn_run, stretch=1)
        run_row.addWidget(self.btn_cancel)
        root.addLayout(run_row)

        self.status_label = QLabel("Prêt.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        root.addWidget(self.status_label)
        root.addWidget(self.progress_bar)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setPlaceholderText("Le journal de la séparation s'affichera ici.")
        root.addWidget(self.log_view, stretch=1)

        self.setCentralWidget(central)

    # ------------------------------------------------------------------ réglages

    def _load_settings(self) -> None:
        s = self.settings
        self.output_edit.setText(str(s.value("output_dir", str(default_output_dir()))))

        model = str(s.value("model", MODELS[0][1]))
        index = self.model_combo.findData(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        else:
            self.model_combo.setEditText(model)

        stem_index = int(s.value("stem_index", 0))
        self.stem_combo.setCurrentIndex(min(max(stem_index, 0), self.stem_combo.count() - 1))

        fmt_index = self.format_combo.findText(str(s.value("format", "mp3")))
        self.format_combo.setCurrentIndex(max(fmt_index, 0))

        self.recursive_check.setChecked(s.value("recursive", True, type=bool))
        self.skip_check.setChecked(s.value("skip_existing", True, type=bool))

    def _save_settings(self) -> None:
        s = self.settings
        s.setValue("output_dir", self.output_edit.text().strip())
        s.setValue("model", self._model_filename())
        s.setValue("stem_index", self.stem_combo.currentIndex())
        s.setValue("format", self.format_combo.currentText())
        s.setValue("recursive", self.recursive_check.isChecked())
        s.setValue("skip_existing", self.skip_check.isChecked())

    def _model_filename(self) -> str:
        text = self.model_combo.currentText().strip()
        index = self.model_combo.findText(text)
        return self.model_combo.itemData(index) if index >= 0 else text

    def _output_dir(self) -> Path:
        text = self.output_edit.text().strip()
        return Path(text).expanduser() if text else default_output_dir()

    def _last_source_dir(self) -> str:
        return str(self.settings.value("last_source_dir", str(music_dir())))

    # ------------------------------------------------------------------ sources

    def add_sources(self, paths: list) -> None:
        known = set(self.sources)
        for raw in paths:
            path = Path(raw).expanduser()
            if not path.exists():
                continue
            if path.is_file() and path.suffix.lower() not in AUDIO_EXTENSIONS:
                self._log(f"Ignoré, ce n'est pas un fichier audio : {path.name}")
                continue
            path = path.resolve()
            if path in known:
                continue
            known.add(path)
            self.sources.append(path)

            icon_type = QStyle.StandardPixmap.SP_DirIcon if path.is_dir() else QStyle.StandardPixmap.SP_FileIcon
            item = QListWidgetItem(self.style().standardIcon(icon_type), str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.source_list.addItem(item)
        self._refresh_count()
        self._update_buttons()

    def _choose_files(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choisir des fichiers audio",
            self._last_source_dir(),
            f"Fichiers audio ({patterns});;Tous les fichiers (*)",
        )
        if files:
            self.settings.setValue("last_source_dir", str(Path(files[0]).parent))
            self.add_sources([Path(f) for f in files])

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier", self._last_source_dir())
        if folder:
            self.settings.setValue("last_source_dir", str(Path(folder).parent))
            self.add_sources([Path(folder)])

    def _remove_selected(self) -> None:
        for item in self.source_list.selectedItems():
            path = Path(item.data(Qt.ItemDataRole.UserRole))
            if path in self.sources:
                self.sources.remove(path)
            self.source_list.takeItem(self.source_list.row(item))
        self._refresh_count()
        self._update_buttons()

    def _clear_sources(self) -> None:
        self.sources.clear()
        self.source_list.clear()
        self._refresh_count()
        self._update_buttons()

    def _refresh_count(self) -> None:
        count = len(collect_audio_files(self.sources, self.recursive_check.isChecked()))
        self.count_label.setText(f"{count} fichier{'s' if count > 1 else ''} audio")

    # ------------------------------------------------------------------ sortie

    def _choose_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie", str(self._output_dir()))
        if folder:
            self.output_edit.setText(folder)

    def _open_output(self) -> None:
        path = self._output_dir()
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    # ------------------------------------------------------------------ séparation

    def start(self) -> None:
        files = collect_audio_files(self.sources, self.recursive_check.isChecked())
        if not files:
            QMessageBox.information(self, APP_NAME, "Aucun fichier audio à traiter. Ajoute des fichiers ou un dossier.")
            return

        output_dir = self._output_dir()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, f"Impossible de créer le dossier de sortie :\n{exc}")
            return

        self._save_settings()
        self.log_view.clear()
        self._log(f"{len(files)} fichier(s) à traiter, sortie dans : {output_dir}")

        self.progress_bar.setRange(0, 0)  # animation d'attente pendant le chargement du modèle
        self.status_label.setText("Chargement du modèle…")

        self.worker = SeparationWorker(
            files=files,
            output_dir=output_dir,
            model_filename=self._model_filename(),
            output_format=self.format_combo.currentText(),
            single_stem=self.stem_combo.currentData(),
            skip_existing=self.skip_check.isChecked(),
        )
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self._log)
        self.worker.file_started.connect(self._on_file_started)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self._on_thread_done)

        self._set_running(True)
        self.thread.start()

    def cancel(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self.btn_cancel.setEnabled(False)
            self._log("Annulation demandée, arrêt après le morceau en cours…")

    def _on_file_started(self, index: int, total: int, name: str) -> None:
        if self.progress_bar.maximum() != total:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(index - 1)
        self.status_label.setText(f"Morceau {index}/{total} : {name}")

    def _on_progress(self, done: int, total: int) -> None:
        self.progress_bar.setValue(done)

    def _on_finished(self, ok: int, skipped: int, errors: int) -> None:
        parts = [f"{ok} séparé(s)"]
        if skipped:
            parts.append(f"{skipped} ignoré(s)")
        if errors:
            parts.append(f"{errors} en erreur")
        summary = "Terminé : " + ", ".join(parts) + "."
        self.status_label.setText(summary)
        self._log(summary)
        self.progress_bar.setRange(0, max(self.progress_bar.maximum(), 1))
        self.progress_bar.setValue(self.progress_bar.maximum())

    def _on_failed(self, details: str) -> None:
        self._log(details)
        last_line = details.strip().splitlines()[-1] if details.strip() else "erreur inconnue"
        self.status_label.setText("Échec de la séparation, voir le journal.")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, APP_NAME, f"La séparation a échoué :\n\n{last_line}")

    def _on_thread_done(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()
        if self.thread is not None:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
        self._set_running(False)

    # ------------------------------------------------------------------ état

    def _set_running(self, running: bool) -> None:
        for widget in (
            self.source_list,
            self.btn_add_files,
            self.btn_add_folder,
            self.params_box,
            self.output_box,
        ):
            widget.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self._update_buttons()

    def _update_buttons(self) -> None:
        running = self.thread is not None
        self.btn_remove.setEnabled(not running and bool(self.source_list.selectedItems()))
        self.btn_clear.setEnabled(not running and self.source_list.count() > 0)
        self.btn_run.setEnabled(not running and bool(self.sources))
        self.btn_cancel.setEnabled(running and self.btn_cancel.isEnabled())

    def _log(self, message: str) -> None:
        self.log_view.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {message}")

    def closeEvent(self, event) -> None:
        if self.thread is not None and self.thread.isRunning():
            answer = QMessageBox.question(
                self,
                APP_NAME,
                "Une séparation est en cours. Quitter quand même ?\nLe morceau en cours ne sera pas terminé.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._save_settings()
            os._exit(0)  # le calcul GPU ne peut pas être interrompu proprement
        self._save_settings()
        event.accept()
