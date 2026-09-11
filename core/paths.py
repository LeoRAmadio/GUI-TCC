# core/paths.py
import os
import sys


def project_root() -> str:
    """Raiz da aplicação: pasta do código-fonte ou, no executável (PyInstaller), a pasta do bundle."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def artifact_path(*parts: str) -> str:
    """Caminho absoluto para um arquivo dentro de 'artifacts/' (independe do diretório de trabalho)."""
    return os.path.join(project_root(), "artifacts", *parts)
