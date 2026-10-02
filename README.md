# Audio Separator Local

Petite application graphique pour séparer la voix et l'instrumentale de fichiers audio,
en local et sur GPU, grâce à [audio-separator](https://github.com/nomadkaraoke/python-audio-separator).

- Glisser-déposer de fichiers ou de dossiers (avec ou sans sous-dossiers)
- Choix du modèle, des pistes à garder et du format de sortie
- Sortie par défaut dans `~/Musique/audio_separator_local`

## Prérequis

- Linux (testé sur Fedora 44) ou Windows
- GPU NVIDIA recommandé (fonctionne aussi sur CPU, beaucoup plus lentement)
- `uv` et `ffmpeg`

## Installation (Fedora)

```bash
sudo dnf install uv ffmpeg-free
git clone <url-du-depot> audio-separator-local
cd audio-separator-local
./install.sh
```

L'application apparaît ensuite dans les Activités.

## Lancer depuis le terminal

```bash
uv run audio-separator-local
```

## Désinstaller

```bash
./uninstall.sh
```

Les modèles téléchargés sont stockés dans `~/.cache/audio-separator-models`.
