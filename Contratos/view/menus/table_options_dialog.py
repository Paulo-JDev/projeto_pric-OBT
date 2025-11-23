# Contratos/view/menus/table_options_dialog.py
# A janela para os botões de tabela.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QSize, Qt
from utils.icon_loader import icon_manager

class TableOptionsDialog(QDialog):
    """
    Menu de opções para operações relacionadas à Tabela (Excel, Links, BI).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opções de Tabela")
        self.setFixedSize(350, 280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        lbl_title = QLabel("Gerenciamento de Tabela")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = lbl_title.font()
        font.setBold(True)
        font.setPointSize(10)
        lbl_title.setFont(font)
        layout.addWidget(lbl_title)
        
        # Botão 1: Exportar Tabela (Excel)
        self.btn_export_excel = QPushButton("Exportar Tabela (Excel)")
        self.btn_export_excel.setIcon(icon_manager.get_icon("excel_down"))
        self.btn_export_excel.setIconSize(QSize(24, 24))
        self.btn_export_excel.setMinimumHeight(50)
        layout.addWidget(self.btn_export_excel)
        
        # Botão 2: Importar Links
        self.btn_import_links = QPushButton("Importar Links da Planilha")
        self.btn_import_links.setIcon(icon_manager.get_icon("link"))
        self.btn_import_links.setIconSize(QSize(24, 24))
        self.btn_import_links.setMinimumHeight(50)
        layout.addWidget(self.btn_import_links)
        
        # Botão 3: Exportar Dados BI (Futuro)
        self.btn_export_bi = QPushButton("Exportar Dados para BI")
        self.btn_export_bi.setIcon(icon_manager.get_icon("graph")) 
        self.btn_export_bi.setIconSize(QSize(24, 24))
        self.btn_export_bi.setMinimumHeight(50)
        layout.addWidget(self.btn_export_bi)
        
        layout.addStretch()