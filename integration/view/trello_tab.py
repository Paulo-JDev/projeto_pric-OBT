# integration/view/trello_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt

class TrelloTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # --- SEÇÃO CREDENCIAIS ---
        cred_group = QFrame()
        cred_group.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; padding: 10px;")
        cred_layout = QFormLayout(cred_group)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_toggle_creds = QPushButton("Mostrar Credenciais")
        self.btn_toggle_creds.setCheckable(True)
        self.btn_toggle_creds.clicked.connect(self.toggle_creds_visibility)

        cred_layout.addRow("API Key:", self.api_key_input)
        cred_layout.addRow("Token:", self.token_input)
        cred_layout.addRow("", self.btn_toggle_creds)
        
        self.layout.addWidget(QLabel("<b>Acesso à API Trello</b>"))
        self.layout.addWidget(cred_group)

        # --- MAPEAMENTO DE STATUS ---
        self.layout.addWidget(QLabel("<b>Mapeamento: Status -> ID da Lista Trello</b>"))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.mapping_form = QFormLayout(scroll_content)

        # Lista de status conforme o sistema
        self.status_list = [
            "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "SIGAD", "ASSINADO", 
            "PUBLICADO", "PORTARIA", "ALERTA PRAZO", "NOTA TÉCNICA", "AGU", "PRORROGADO"
        ]
        
        self.mapping_inputs = {}
        for status in self.status_list:
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"ID da lista para {status}")
            self.mapping_form.addRow(f"{status}:", input_field)
            self.mapping_inputs[status] = input_field

        scroll.setWidget(scroll_content)
        self.layout.addWidget(scroll)

        self.btn_save_creds = QPushButton("Salvar Configurações Trello")
        self.btn_save_creds.setStyleSheet("background-color: #8AB4F7; color: black; font-weight: bold; height: 35px;")
        self.layout.addWidget(self.btn_save_creds)

    def toggle_creds_visibility(self, checked):
        # Mensagem avisando que a pessoa não esta outorizada para ver as credenciais
        print("Avisando que a pessoa não esta outorizada para ver as credenciais")
        """mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(mode)
        self.token_input.setEchoMode(mode)
        self.btn_toggle_creds.setText("Ocultar Credenciais" if checked else "Mostrar Credenciais")"""
