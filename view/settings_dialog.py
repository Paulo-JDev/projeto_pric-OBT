# view/settings_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(400, 180)

        self.main_layout = QVBoxLayout(self)

        # Layout para o seletor de modo
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Modo de Obtenção de Dados:")
        self.mode_button = QPushButton("Carregando...")
        self.mode_button.setCheckable(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_button)
        self.main_layout.addLayout(mode_layout)

        self.main_layout.addStretch()

        self.close_button = QPushButton("Fechar")
        self.main_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)