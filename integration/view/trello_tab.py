# integration/view/trello_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QSize
from utils.icon_loader import icon_manager
from datetime import datetime

class TrelloTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # --- SEÇÃO: CONFIGURAÇÕES DE ACESSO ---
        config_frame = QFrame()
        config_frame.setObjectName("trello_config_frame")
        config_frame.setStyleSheet("""
            #trello_config_frame {
                border: 1px solid #3d3d3d;
                border-radius: 10px;
            }
            QLabel { color: #8AB4F7; font-weight: bold; }
            QLineEdit { 
                background-color: #1e1e1e; 
                border: 1px solid #3d3d3d; 
                color: white; 
                padding: 8px; 
                border-radius: 5px; 
            }
        """)
        config_layout = QVBoxLayout(config_frame)

        header_layout = QHBoxLayout()
        trello_icon = QLabel()
        # Usando ícone de sincronização ou automation como placeholder
        trello_icon.setPixmap(icon_manager.get_icon("synchronize").pixmap(24, 24))
        header_layout.addWidget(trello_icon)
        
        title = QLabel("Configurações da API Trello")
        title.setStyleSheet("font-size: 16px; color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        config_layout.addLayout(header_layout)

        # Campos de Entrada
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Insira sua API Key do Trello...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Insira seu Token de Acesso...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.list_id_input = QLineEdit()
        self.list_id_input.setPlaceholderText("ID da Lista onde os cards serão criados...")

        config_layout.addWidget(QLabel("API Key:"))
        config_layout.addWidget(self.api_key_input)
        config_layout.addWidget(QLabel("Token:"))
        config_layout.addWidget(self.token_input)
        config_layout.addWidget(QLabel("ID da Lista (Trello):"))
        config_layout.addWidget(self.list_id_input)

        self.layout.addWidget(config_frame)

        # --- SEÇÃO: AÇÕES ---
        actions_layout = QHBoxLayout()
        
        self.btn_sync_trello = QPushButton(" Sincronizar Novos Contratos")
        self.btn_sync_trello.setIcon(icon_manager.get_icon("icon_send"))
        self.btn_sync_trello.setIconSize(QSize(20, 20))
        self.btn_sync_trello.setMinimumHeight(45)
        self.btn_sync_trello.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sync_trello.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                border: 2px solid #8AB4F7;
                color: #8AB4F7;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8AB4F7; color: #1e1e1e; }
        """)
        
        actions_layout.addWidget(self.btn_sync_trello)
        self.layout.addLayout(actions_layout)

        # --- SEÇÃO: LOG DE INTEGRAÇÃO ---
        self.layout.addWidget(QLabel("Log de Integração:"))
        self.trello_log = QPlainTextEdit()
        self.trello_log.setReadOnly(True)
        self.trello_log.setStyleSheet("""
            QPlainTextEdit {
                background-color: #181818;
                color: #00FF41;
                font-family: 'Consolas', 'Monospace';
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
        """)
        self.layout.addWidget(self.trello_log)

    def log(self, message):
        """Adiciona mensagem ao log do Trello."""
        now = datetime.now().strftime("%H:%M:%S")
        self.trello_log.appendPlainText(f"[{now}] Trello > {message}")

    def get_credentials(self):
        """Retorna as credenciais preenchidas."""
        return {
            "key": self.api_key_input.text().strip(),
            "token": self.token_input.text().strip(),
            "list_id": self.list_id_input.text().strip()
        }
