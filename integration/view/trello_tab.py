# integration/view/trello_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QPlainTextEdit, QListWidget, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from utils.icon_loader import icon_manager
from datetime import datetime

class TrelloTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # --- SEÇÃO CONFIGURAÇÃO (OCULTÁVEL) ---
        self.btn_toggle_config = QPushButton(" Mostrar/Ocultar Configurações da API")
        self.btn_toggle_config.setCheckable(True)
        self.layout.addWidget(self.btn_toggle_config)

        self.config_frame = QFrame()
        self.config_frame.setVisible(False) # Inicia oculto
        self.config_frame.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; padding: 10px;")
        config_layout = QVBoxLayout(self.config_frame)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Token")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.list_id_input = QLineEdit()
        self.list_id_input.setPlaceholderText("ID da Lista")

        config_layout.addWidget(QLabel("API Key:"))
        config_layout.addWidget(self.api_key_input)
        config_layout.addWidget(QLabel("Token:"))
        config_layout.addWidget(self.token_input)
        config_layout.addWidget(QLabel("ID da Lista:"))
        config_layout.addWidget(self.list_id_input)

        self.btn_save_creds = QPushButton("Salvar Configurações Trello")
        config_layout.addWidget(self.btn_save_creds)
        
        self.layout.addWidget(self.config_frame)
        self.btn_toggle_config.clicked.connect(lambda: self.config_frame.setVisible(self.btn_toggle_config.isChecked()))

        # --- LISTA DE CONTRATOS ---
        self.layout.addWidget(QLabel("Selecione os Contratos para Sincronizar:"))
        self.contract_list = QListWidget()
        # Habilita seleção múltipla com checkbox
        self.contract_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.contract_list.setStyleSheet("background-color: #1e1e1e; color: white;")
        self.layout.addWidget(self.contract_list)

        self.btn_sync_trello = QPushButton(" Sincronizar Selecionados com Trello")
        self.btn_sync_trello.setMinimumHeight(40)
        self.btn_sync_trello.setStyleSheet("background-color: #1e1e1e; border: 2px solid #8AB4F7; color: #8AB4F7; font-weight: bold;")
        self.layout.addWidget(self.btn_sync_trello)

        self.trello_log = QPlainTextEdit()
        self.trello_log.setReadOnly(True)
        self.trello_log.setMaximumHeight(100)
        self.trello_log.setStyleSheet("background-color: #181818; color: #00FF41;")
        self.layout.addWidget(self.trello_log)

    def log(self, message):
        self.trello_log.appendPlainText(f"> {message}")

    def get_credentials(self):
        """Retorna as credenciais preenchidas."""
        return {
            "key": self.api_key_input.text().strip(),
            "token": self.token_input.text().strip(),
            "list_id": self.list_id_input.text().strip()
        }
