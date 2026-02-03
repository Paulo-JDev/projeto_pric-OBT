import sys
from pathlib import Path
from PyQt6.QtGui import QIcon

class IconManager:
    def __init__(self):
        self.icons_dir = self._find_icons_dir()

    def _find_icons_dir(self):
        """Encontra a pasta de ícones, mesmo no executável ou desenvolvimento."""
        # Se estiver rodando como executável (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent.parent  # Volta uma pasta (projeto/)
        
        # Procura a pasta 'icons' em lugares comuns
        possible_paths = [
            base_dir / "icons",
            base_dir / "utils" / "icons",
            base_dir / "resources" / "icons",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError("Pasta 'icons' não encontrada!")

    def get_icon(self, icon_name):
        """Retorna um QIcon pelo nome do arquivo (sem extensão)."""
        icon_path = self.icons_dir / f"{icon_name}.png"
        if not icon_path.exists():
            print(f"[AVISO] Ícone não encontrado: {icon_path}")
            return QIcon()  # Ícone vazio (não quebra o programa)
        return QIcon(str(icon_path))
    
    def got_ico(self, icon_name):
        """Retorna um QIcon pelo nome do arquivo (sem extensão)."""
        icon_path = self.icons_dir / f"{icon_name}.ico"
        if not icon_path.exists():
            print(f"[AVISO] Ícone não encontrado: {icon_path}")
            return QIcon()  # Ícone vazio (não quebra o programa)
        return QIcon(str(icon_path))

# Cria uma instância global para usar em todo o projeto
icon_manager = IconManager()