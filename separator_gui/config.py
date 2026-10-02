"""Constantes et fonctions utilitaires partagées par l'application."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths

APP_NAME = "Audio Separator Local"
APP_ID = "audio-separator-local"

ICON_PATH = Path(__file__).resolve().parent / "assets" / f"{APP_ID}.svg"

# Même dossier que celui utilisé avec la CLI : les modèles déjà téléchargés sont réutilisés
MODEL_DIR = Path.home() / ".cache" / "audio-separator-models"

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus", ".aac", ".wma"}

# (libellé affiché, nom de fichier du modèle)
# Tous ces modèles produisent deux pistes : "Vocals" et "Instrumental"
MODELS = [
    ("BS-Roformer 317 (meilleure qualité)", "model_bs_roformer_ep_317_sdr_12.9755.ckpt"),
    ("BS-Roformer 368", "model_bs_roformer_ep_368_sdr_12.9628.ckpt"),
    ("MDX23C InstVoc HQ", "MDX23C-8KFFT-InstVoc_HQ.ckpt"),
    ("MDX-Net Inst HQ 3 (rapide)", "UVR-MDX-NET-Inst_HQ_3.onnx"),
]

# (libellé affiché, valeur passée à output_single_stem)
STEMS = [
    ("Instrumentale seulement", "Instrumental"),
    ("Voix seulement", "Vocals"),
    ("Instrumentale et voix", None),
]

OUTPUT_FORMATS = ["mp3", "flac", "wav"]


def music_dir() -> Path:
    """Dossier Musique de l'utilisateur (~/Musique sous Fedora en français)."""
    music = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)
    return Path(music) if music else Path.home() / "Music"


def default_output_dir() -> Path:
    return music_dir() / "audio_separator_local"


def is_audio_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS


def collect_audio_files(sources: list[Path], recursive: bool = True) -> list[Path]:
    """Transforme une liste de fichiers et dossiers en liste de fichiers audio, sans doublons."""
    found: dict[Path, None] = {}
    for src in sources:
        if is_audio_file(src):
            found[src.resolve()] = None
        elif src.is_dir():
            pattern = "**/*" if recursive else "*"
            for path in sorted(src.glob(pattern)):
                if is_audio_file(path):
                    found[path.resolve()] = None
    return list(found)


def output_names(track: Path) -> dict[str, str]:
    """Noms des fichiers de sortie, sans extension : « Titre (Instrumental) »."""
    return {
        "Vocals": f"{track.stem} (Vocals)",
        "Instrumental": f"{track.stem} (Instrumental)",
    }


def expected_outputs(track: Path, output_dir: Path, fmt: str, single_stem: str | None) -> list[Path]:
    names = output_names(track)
    stems = [single_stem] if single_stem else list(names)
    return [output_dir / f"{names[stem]}.{fmt}" for stem in stems]
