# Contratos/view/manual_contract_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager


class ManualContractDialog(QDialog):
    """
    Mini janela com 3 botões:
    - Adicionar Contrato
    - Exportar Lista de Contratos Manuais
    - Importar Lista de Contratos Manuais
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contratos Manuais")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ==================== BOTÃO 1: ADICIONAR ====================
        self.btn_add = QPushButton("Adicionar Contrato")
        self.btn_add.setIcon(icon_manager.get_icon("add"))
        self.btn_add.setIconSize(QSize(24, 24))
        self.btn_add.setMinimumHeight(50)
        layout.addWidget(self.btn_add)
        
        # ==================== BOTÃO 2: EXPORTAR ====================
        self.btn_export = QPushButton("Exportar Lista de Contratos Manuais")
        self.btn_export.setIcon(icon_manager.get_icon("exportar"))
        self.btn_export.setIconSize(QSize(24, 24))
        self.btn_export.setMinimumHeight(50)
        layout.addWidget(self.btn_export)
        
        # ==================== BOTÃO 3: IMPORTAR ====================
        self.btn_import = QPushButton("Importar Lista de Contratos Manuais")
        self.btn_import.setIcon(icon_manager.get_icon("importar"))
        self.btn_import.setIconSize(QSize(24, 24))
        self.btn_import.setMinimumHeight(50)
        layout.addWidget(self.btn_import)
