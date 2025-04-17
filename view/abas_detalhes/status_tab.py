from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem, QGroupBox
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

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

    # ==== SEÇÃO DE REGISTROS ====
    registro_group = QGroupBox("Registros de Status")
    registro_layout = QVBoxLayout(registro_group)
    
    # Botão para adicionar registro
    self.add_record_button = QPushButton("Adicionar Registro")
    self.add_record_button.setIcon(icon_manager.get_icon("registrar_status"))
    self.add_record_button.clicked.connect(self.registro_def)
    registro_layout.addWidget(self.add_record_button)
    
    # Lista de registros
    self.registro_list = QListWidget()
    registro_layout.addWidget(self.registro_list)
    
    # Botão "Excluir Registro"
    self.delete_registro_button = QPushButton("Excluir Registro")
    self.delete_registro_button.setIcon(icon_manager.get_icon("delete"))
    self.delete_registro_button.clicked.connect(self.delete_registro)
    registro_layout.addWidget(self.delete_registro_button)
    
    layout.addWidget(registro_group)
    
    # ==== SEÇÃO DE COMENTÁRIOS ====
    comentario_group = QGroupBox("Comentários")
    comentario_layout = QVBoxLayout(comentario_group)
    
    # Botão "Adicionar Comentário"
    self.add_comment_button = QPushButton("Adicionar Comentário")
    self.add_comment_button.setIcon(icon_manager.get_icon("comments"))
    self.add_comment_button.clicked.connect(self.add_comment)
    comentario_layout.addWidget(self.add_comment_button)

    # Lista de comentários
    self.comment_list = QListWidget()
    comentario_layout.addWidget(self.comment_list)
   
    # Botão "Excluir Comentário"
    self.delete_comment_button = QPushButton("Excluir Comentário")
    self.delete_comment_button.setIcon(icon_manager.get_icon("delete_comment"))
    self.delete_comment_button.clicked.connect(self.delete_comment)
    comentario_layout.addWidget(self.delete_comment_button)
    
    layout.addWidget(comentario_group)

    return self.status_tab


