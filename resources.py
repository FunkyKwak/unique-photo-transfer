from pathlib import Path
import sys


def resource_path(relative_path):
    """
    Retourne le chemin absolu d'une ressource.

    Fonctionne :
    - en développement (python main.py)
    - dans un exécutable PyInstaller
    """

    # Racine du projet (en dev)
    base_path = Path(__file__).parent

    # Dossier temporaire créé par PyInstaller
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)

    return str(base_path / relative_path)


