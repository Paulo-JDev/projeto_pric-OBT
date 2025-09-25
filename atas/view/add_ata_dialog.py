# atas/view/add_ata_dialog.py

import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QComboBox)
from PyQt6.QtCore import pyqtSignal
from utils.icon_loader import icon_manager
from utils.utils import resource_path
import os # Necessário para encontrar o JSON
import sys

class AddAtaDialog(QDialog):
    ata_added = pyqtSignal(dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Item")
        self.setWindowIcon(icon_manager.get_icon("plus"))
        self.setMinimumWidth(500)
        self.setStyleSheet("QWidget { font-size: 14px; }")
        self.setup_ui()
        self._load_tipos_from_json()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        first_line_layout = QHBoxLayout()
        self.tipo_cb = QComboBox()
        self.numero_le = QLineEdit()
        self.ano_le = QLineEdit()
        self.numero_le.setPlaceholderText("Ex: 90142")
        self.ano_le.setPlaceholderText("Ex: 2025")
        first_line_layout.addWidget(QLabel("Tipo:"))
        first_line_layout.addWidget(self.tipo_cb, 1)
        first_line_layout.addWidget(QLabel("Número:"))
        first_line_layout.addWidget(self.numero_le)
        first_line_layout.addWidget(QLabel("Ano:"))
        first_line_layout.addWidget(self.ano_le)
        self.layout.addLayout(first_line_layout)

        objeto_layout = QHBoxLayout()
        self.objeto_le = QLineEdit()
        self.objeto_le.setPlaceholderText("Exemplo: 'Material de Limpeza' (Utilizar no máximo 3 palavras)")
        objeto_layout.addWidget(QLabel("Objeto:"))
        objeto_layout.addWidget(self.objeto_le)
        self.layout.addLayout(objeto_layout)

        parecer_layout = QHBoxLayout()
        self.parecer_le = QLineEdit()
        self.parecer_le.setPlaceholderText("Exemplo: '787000/2024-032/00'")
        parecer_layout.addWidget(QLabel("Contrato/Ata/Parecer:"))
        parecer_layout.addWidget(self.parecer_le)
        self.layout.addLayout(parecer_layout)

        self.add_button = QPushButton("Adicionar Item")
        self.add_button.setIcon(icon_manager.get_icon("aproved"))
        self.add_button.clicked.connect(self.add_ata)
        self.layout.addWidget(self.add_button)
        
        self.numero_le.setFocus()

    def _load_tipos_from_json(self):
        """Carrega os tipos de ata de um arquivo JSON de forma robusta."""
        try:
            # Usa a nova função para encontrar o caminho correto
            json_path = resource_path("utils/json/tipos_ata.json")

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tipos = data.get('tipos', [])
            self.tipo_cb.addItems(tipos)

            if "Pregão Eletrônico" in tipos:
                self.tipo_cb.setCurrentText("Pregão Eletrônico")

        except Exception as e:
            print(f"ERRO: Não foi possível carregar tipos_ata.json: {e}")
            QMessageBox.critical(self, "Erro de Arquivo", 
                                f"Não foi possível carregar o arquivo de configuração de tipos de ata:\n"
                                f"{json_path}\n\nVerifique se o arquivo existe.")
            self.tipo_cb.addItem("Erro")
            self.tipo_cb.setEnabled(False)

    def add_ata(self):
        """Valida os campos e emite o sinal com os dados da nova ata."""
        numero = self.numero_le.text().strip()
        ano = self.ano_le.text().strip()
        parecer = self.parecer_le.text().strip() # Obtém o valor do parecer

        # Validação dos campos obrigatórios
        if not numero or not ano or not parecer:
            QMessageBox.warning(self, "Campos Obrigatórios", 
                                "Os campos 'Número', 'Ano' e 'Contrato/Ata/Parecer' são obrigatórios.")
            return

        nova_ata = {
            'modalidade': self.tipo_cb.currentText(),
            'numero': numero,
            'ano': ano,
            'objeto': self.objeto_le.text().strip() or "Não informado",
            'contrato_ata_parecer': parecer, # Usa a variável já validada
            'empresa': "A ser definida",
        }
        
        self.ata_added.emit(nova_ata)
        self.accept()
