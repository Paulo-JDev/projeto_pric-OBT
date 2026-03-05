# integration/view/trello_tab.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QFormLayout, QScrollArea, QTabWidget
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

        # --- ABAS DE MAPEAMENTO ---
        self.tabs = QTabWidget()
        
        # Aba Contratos
        self.tab_contratos = self._create_mapping_tab([
            "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "SIGAD", "ASSINADO", "PLANILHA",
            "PUBLICADO", "PORT. MARINHA", "PORTARIA", "ALERTA PRAZO", "NOTA TÉCNICA", "AGU", "PRORROGADO"
        ])
        self.mapping_inputs_contratos = self.tab_contratos.inputs

        # Aba Atas
        self.tab_atas = self._create_mapping_tab([
            "SEÇÃO ATAS", "ATA GERADA", "EMPRESA", "SIGDEM", "ASSINADO", "PLANILHA", 
            "PUBLICADO", "PORT. MARINHA", "PORTARIA", "ALERTA PRAZO", "NOTA TÉCNICA", "AGU", "PRORROGADO", "SIGAD"
        ])
        self.mapping_inputs_atas = self.tab_atas.inputs

        self.tabs.addTab(self.tab_contratos.scroll, "Mapeamento Contratos")
        self.tabs.addTab(self.tab_atas.scroll, "Mapeamento Atas")
        self.layout.addWidget(self.tabs)

        self.btn_save_creds = QPushButton("Salvar Configurações Trello")
        self.layout.addWidget(self.btn_save_creds)

    def _create_mapping_tab(self, status_list):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QFormLayout(content)
        inputs = {}
        for status in status_list:
            field = QLineEdit()
            layout.addRow(f"{status}:", field)
            inputs[status] = field
        scroll.setWidget(content)
        # Objeto auxiliar para facilitar acesso
        content.scroll = scroll
        content.inputs = inputs
        return content

    def _setup_mapping_fields(self, layout, status_list, input_dict):
        for status in status_list:
            field = QLineEdit()
            field.setPlaceholderText(f"ID da lista para {status}")
            layout.addRow(f"{status}:", field)
            input_dict[status] = field

    def toggle_creds_visibility(self, checked):
        # Mensagem avisando que a pessoa não esta outorizada para ver as credenciais
        print("Avisando que a pessoa não esta outorizada para ver as credenciais")
        """mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.api_key_input.setEchoMode(mode)
        self.token_input.setEchoMode(mode)
        self.btn_toggle_creds.setText("Ocultar Credenciais" if checked else "Mostrar Credenciais")"""
