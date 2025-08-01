# view/abas_detalhes/status_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QFrame
)
from utils.icon_loader import icon_manager

def create_status_tab(self):
    """Cria a aba 'Status' com layout vertical lado a lado para registros e comentários."""
    self.status_tab = QWidget()
    main_layout = QVBoxLayout(self.status_tab)

    # ==== SEÇÃO STATUS (TOPO) ====
    status_layout = QHBoxLayout()
    status_layout.addStretch() # Empurra para a direita
    
    status_label = QLabel("Status:")
    status_label.setObjectName("status_label")
    status_layout.addWidget(status_label)
    
    self.status_dropdown = QComboBox()
    self.status_dropdown.setObjectName("seta_baixo")
    self.status_dropdown.addItems([
        "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "ASSINADO", "PUBLICADO",
        "ALERTA PRAZO", "ATA GERADA", "NOTA TÉCNICA", "AGU", "PRORROGADO"
    ])
    self.status_dropdown.setFixedWidth(220)
    status_layout.addWidget(self.status_dropdown)
    main_layout.addLayout(status_layout)

    # ==== LAYOUT DE CONTEÚDO (LADO A LADO) ====
    content_layout = QHBoxLayout()
    content_layout.setSpacing(15)

    # ---- COLUNA ESQUERDA: REGISTROS ----
    registros_section = QVBoxLayout()
    
    # Frame para a lista de registros
    registros_frame = QFrame()
    registros_frame.setObjectName("registros_frame")
    registros_frame.setFrameShape(QFrame.Shape.StyledPanel)
    registros_list_layout = QVBoxLayout(registros_frame)
    registros_list_layout.setContentsMargins(5, 5, 5, 5)
    
    self.registro_list = QListWidget()
    self.registro_list.setObjectName("registro_list")
    registros_list_layout.addWidget(self.registro_list)
    registros_section.addWidget(registros_frame) # Adiciona o frame à seção

    # Botões para registros (abaixo da lista)
    registro_buttons_layout = QHBoxLayout()
    self.add_record_button = QPushButton("Adicionar Registro")
    self.add_record_button.setIcon(icon_manager.get_icon("registrar_status"))
    self.add_record_button.clicked.connect(self.registro_def)
    registro_buttons_layout.addWidget(self.add_record_button)
    
    self.delete_registro_button = QPushButton("Excluir Registro")
    self.delete_registro_button.setIcon(icon_manager.get_icon("delete"))
    self.delete_registro_button.clicked.connect(self.delete_registro)
    registro_buttons_layout.addWidget(self.delete_registro_button)
    registros_section.addLayout(registro_buttons_layout) # Adiciona botões à seção

    content_layout.addLayout(registros_section) # Adiciona seção de registros ao layout principal

    # ---- COLUNA DIREITA: COMENTÁRIOS ----
    comentarios_section = QVBoxLayout()

    # Frame para a lista de comentários
    comentarios_frame = QFrame()
    comentarios_frame.setObjectName("comentarios_frame")
    comentarios_frame.setFrameShape(QFrame.Shape.StyledPanel)
    comentarios_list_layout = QVBoxLayout(comentarios_frame)
    comentarios_list_layout.setContentsMargins(5, 5, 5, 5)
    
    self.comment_list = QListWidget()
    self.comment_list.setObjectName("comment_list")
    comentarios_list_layout.addWidget(self.comment_list)
    comentarios_section.addWidget(comentarios_frame) # Adiciona o frame à seção

    # Botões para comentários (abaixo da lista)
    comentario_buttons_layout = QHBoxLayout()
    self.add_comment_button = QPushButton("Adicionar Comentário")
    self.add_comment_button.setIcon(icon_manager.get_icon("comments"))
    self.add_comment_button.clicked.connect(self.add_comment)
    comentario_buttons_layout.addWidget(self.add_comment_button)

    self.delete_comment_button = QPushButton("Excluir Comentário")
    self.delete_comment_button.setIcon(icon_manager.get_icon("delete_comment"))
    self.delete_comment_button.clicked.connect(self.delete_comment)
    comentario_buttons_layout.addWidget(self.delete_comment_button)
    comentarios_section.addLayout(comentario_buttons_layout) # Adiciona botões à seção

    content_layout.addLayout(comentarios_section) # Adiciona seção de comentários ao layout principal

    # Adiciona o layout de conteúdo (com as duas colunas) ao layout da aba
    main_layout.addLayout(content_layout)

    return self.status_tab