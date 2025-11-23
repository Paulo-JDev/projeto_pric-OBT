# Contratos/view/menus/status_options_dialog.py
# A janela para os botões de status.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QSize, Qt
from utils.icon_loader import icon_manager

class StatusOptionsDialog(QDialog):
    """
    Menu de opções para Importar/Exportar Status (JSON).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciamento de Status")
        self.setFixedSize(350, 220)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        lbl_title = QLabel("Backup e Restauração de Status")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = lbl_title.font()
        font.setBold(True)
        font.setPointSize(10)
        lbl_title.setFont(font)
        layout.addWidget(lbl_title)

        # Botão 1: Exportar Status
        self.btn_export_status = QPushButton("Exportar Status (Backup)")
        self.btn_export_status.setIcon(icon_manager.get_icon("exportar"))
        self.btn_export_status.setIconSize(QSize(24, 24))
        self.btn_export_status.setMinimumHeight(50)
        layout.addWidget(self.btn_export_status)
        
        # Botão 2: Importar Status
        self.btn_import_status = QPushButton("Importar Status (Restaurar)")
        self.btn_import_status.setIcon(icon_manager.get_icon("importar"))
        self.btn_import_status.setIconSize(QSize(24, 24))
        self.btn_import_status.setMinimumHeight(50)
        layout.addWidget(self.btn_import_status)
        
        layout.addStretch()