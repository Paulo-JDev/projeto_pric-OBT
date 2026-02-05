# integration/view/trello_config_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QFrame)
from PyQt6.QtCore import Qt

class TrelloConfigView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # --- SEÇÃO CREDENCIAIS ---
        cred_frame = QFrame()
        cred_frame.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; padding: 10px;")
        cred_layout = QFormLayout(cred_frame)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_toggle_creds = QPushButton("Mostrar Chaves")
        self.btn_toggle_creds.setCheckable(True)
        self.btn_toggle_creds.clicked.connect(self.toggle_echo_mode)

        cred_layout.addRow("Trello API Key:", self.api_key_input)
        cred_layout.addRow("Trello Token:", self.token_input)
        cred_layout.addRow("", self.btn_toggle_creds)
        
        layout.addWidget(QLabel("<b>Configurações de Acesso</b>"))
        layout.addWidget(cred_frame)

        # --- SEÇÃO MAPEAMENTO DE LISTAS (Contratos) ---
        mapping_frame = QFrame()
        mapping_layout = QFormLayout(mapping_frame)

        # Aqui você cria um campo para cada status mapeado no seu sistema
        self.list_ids = {
            "Assinado": QLineEdit(),
            "Em Execução": QLineEdit(),
            "Finalizado": QLineEdit(),
            "Atrasado": QLineEdit()
        }

        for status, widget in self.list_ids.items():
            widget.setPlaceholderText(f"ID da Lista para {status}")
            mapping_layout.addRow(f"Lista {status}:", widget)

        layout.addWidget(QLabel("<b>Mapeamento de Status -> Listas do Trello</b>"))
        layout.addWidget(mapping_frame)

        self.btn_save = QPushButton("Salvar Configurações Trello")
        self.btn_save.setStyleSheet("background-color: #8AB4F7; color: black; font-weight: bold;")
        layout.addWidget(self.btn_save)
        layout.addStretch()

    def toggle_echo_mode(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(mode)
        self.token_input.setEchoMode(mode)
        self.btn_toggle_creds.setText("Ocultar Chaves" if checked else "Mostrar Chaves")
