from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

def create_status_tab(self):
    """Cria a aba 'Status' com dropdown de seleção, botões e lista de comentários"""
    self.status_tab = QWidget()
    layout = QVBoxLayout(self.status_tab)

    # Layout horizontal para Status
    status_layout = QHBoxLayout()

    # Adicionar espaço elástico para empurrar o dropdown para a direita
    status_layout.addStretch()
    
    # Label e dropdown para status
    status_label = QLabel("Status:")
    status_label.setObjectName("status_label")
    status_layout.addWidget(status_label)
    
    # Dropdown para selecionar status
    self.status_dropdown = QComboBox()
    self.status_dropdown.setObjectName("seta_baixo")
    self.status_dropdown.addItems([
        "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "ASSINADO", "PUBLICADO",
        "ALERTA PRAZO", "ATA GERADA", "NOTA TÉCNICA", "AGU", "PRORROGADO"
    ])
    self.status_dropdown.setFixedWidth(220)  # Aumentando a largura
    status_layout.addWidget(self.status_dropdown)

    layout.addLayout(status_layout)

    # ==== SEÇÃO DE REGISTROS ====
    # Layout horizontal para botões de registro
    registro_buttons_layout = QHBoxLayout()
    
    # Botão para adicionar registro
    self.add_record_button = QPushButton("Adicionar Registro")
    self.add_record_button.setObjectName("add_record_button")
    self.add_record_button.setIcon(icon_manager.get_icon("registrar_status"))
    self.add_record_button.clicked.connect(self.registro_def)
    registro_buttons_layout.addWidget(self.add_record_button)
    
    # Botão "Excluir Registro"
    self.delete_registro_button = QPushButton("Excluir Registro")
    self.delete_registro_button.setObjectName("delete_registro_button")
    self.delete_registro_button.setIcon(icon_manager.get_icon("delete"))
    self.delete_registro_button.clicked.connect(self.delete_registro)
    registro_buttons_layout.addWidget(self.delete_registro_button)
    
    # Adicionar espaço elástico para empurrar os botões para a esquerda
    registro_buttons_layout.addStretch()
    
    layout.addLayout(registro_buttons_layout)
    
    # Frame para registros com borda mais clara
    registros_frame = QFrame()
    registros_frame.setObjectName("registros_frame")
    registros_frame.setFrameShape(QFrame.Shape.StyledPanel)
    registros_layout = QVBoxLayout(registros_frame)
    registros_layout.setContentsMargins(5, 5, 5, 5)
    
    # Lista de registros
    self.registro_list = QListWidget()
    self.registro_list.setObjectName("registro_list")
    registros_layout.addWidget(self.registro_list)
    
    layout.addWidget(registros_frame)
    
    # ==== SEÇÃO DE COMENTÁRIOS ====
    # Layout horizontal para botões de comentário
    comentario_buttons_layout = QHBoxLayout()
    
    # Botão "Adicionar Comentário"
    self.add_comment_button = QPushButton("Adicionar Comentário")
    self.add_comment_button.setObjectName("add_comment_button")
    self.add_comment_button.setIcon(icon_manager.get_icon("comments"))
    self.add_comment_button.clicked.connect(self.add_comment)
    comentario_buttons_layout.addWidget(self.add_comment_button)

    # Botão "Excluir Comentário"
    self.delete_comment_button = QPushButton("Excluir Comentário")
    self.delete_comment_button.setObjectName("delete_comment_button")
    self.delete_comment_button.setIcon(icon_manager.get_icon("delete_comment"))
    self.delete_comment_button.clicked.connect(self.delete_comment)
    comentario_buttons_layout.addWidget(self.delete_comment_button)
    
    # Adicionar espaço elástico para empurrar os botões para a esquerda
    comentario_buttons_layout.addStretch()
    
    layout.addLayout(comentario_buttons_layout)

    # Frame para comentários com borda mais clara
    comentarios_frame = QFrame()
    comentarios_frame.setObjectName("comentarios_frame")
    comentarios_frame.setFrameShape(QFrame.Shape.StyledPanel)
    comentarios_layout = QVBoxLayout(comentarios_frame)
    comentarios_layout.setContentsMargins(5, 5, 5, 5)
    
    # Lista de comentários
    self.comment_list = QListWidget()
    self.comment_list.setObjectName("comment_list")
    comentarios_layout.addWidget(self.comment_list)
    
    layout.addWidget(comentarios_frame)

    return self.status_tab


