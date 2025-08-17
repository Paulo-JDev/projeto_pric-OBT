# view/settings_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGroupBox
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(450, 250)

        self.main_layout = QVBoxLayout(self)

        # Layout para o seletor de modo
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Modo de Obtenção de Dados:")
        self.mode_button = QPushButton("Carregando...")
        self.mode_button.setCheckable(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_button)
        self.main_layout.addLayout(mode_layout)

        offline_group = QGroupBox("Gerenciamento do Banco de Dados Offline")
        offline_layout = QVBoxLayout(offline_group)

        offline_label = QLabel("<b>Busca para uso OFFLINE:</b>")
        offline_layout.addWidget(offline_label)
        
        self.offline_uasg_input = QLineEdit()
        self.offline_uasg_input.setPlaceholderText("Digite a UASG para baixar ou deletar (Ex: 787010)")
        offline_layout.addWidget(self.offline_uasg_input)
        
        offline_buttons_layout = QHBoxLayout()
        self.create_db_button = QPushButton("Fazer DB")
        self.delete_db_button = QPushButton("Excluir UASG do DB")
        offline_buttons_layout.addWidget(self.create_db_button)
        offline_buttons_layout.addWidget(self.delete_db_button)
        offline_layout.addLayout(offline_buttons_layout)
        
        self.main_layout.addWidget(offline_group)
        # --- FIM DA NOVA SEÇÃO ---

        self.main_layout.addStretch()

        # Botão Fechar
        self.close_button = QPushButton("Fechar")
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()
        close_button_layout.addWidget(self.close_button)
        self.main_layout.addLayout(close_button_layout)