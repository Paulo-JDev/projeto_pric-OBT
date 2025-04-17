from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt

def create_status_tab(self):
    """Cria a aba 'Status' com dropdown de seleção, botões e lista de comentários"""
    self.status_tab = QWidget()
    layout = QVBoxLayout(self.status_tab)

    # Layout horizontal para Status
    status_layout = QHBoxLayout()

    # Dropdown para selecionar status
    self.status_dropdown = QComboBox()
    self.status_dropdown.addItems([
        "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "ASSINADO", "PUBLICADO",
        "ALERTA PRAZO", "ATA GERADA", "NOTA TÉCNICA", "AGU", "PRORROGADO"
    ])
    status_layout.addWidget(QLabel("Status:"))
    status_layout.addWidget(self.status_dropdown)

    layout.addLayout(status_layout)

    # Botão para adicionar registro
    self.add_record_button = QPushButton("Adicionar Registro")
    self.add_record_button.clicked.connect(self.registro_def)
    layout.addWidget(self.add_record_button)

    # Campo de texto para comentário
    self.comment_box = QTextEdit()
    layout.addWidget(self.comment_box)

    # Botão "Adicionar Comentário"
    self.add_comment_button = QPushButton("Adicionar Comentário")
    self.add_comment_button.clicked.connect(self.add_comment)
    layout.addWidget(self.add_comment_button)

    # Lista de comentários
    self.comment_list = QListWidget()
    layout.addWidget(self.comment_list)
   
    # Botão "Excluir Comentário"
    self.delete_comment_button = QPushButton("Excluir Comentário")
    self.delete_comment_button.clicked.connect(self.delete_comment)
    layout.addWidget(self.delete_comment_button)

    return self.status_tab


