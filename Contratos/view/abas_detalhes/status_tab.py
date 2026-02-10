# view/abas_detalhes/status_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QFrame
)
from utils.icon_loader import icon_manager

def create_status_tab(self):
    """Cria a aba 'Status' com layout corrigido e botão CA-Trello integrado."""
    self.status_tab = QWidget()
    main_layout = QVBoxLayout(self.status_tab)

    # ==== SEÇÃO STATUS (TOPO) ====
    status_layout = QHBoxLayout()
    status_layout.addStretch() 
    
    status_label = QLabel("Status:")
    status_label.setObjectName("status_label")
    status_layout.addWidget(status_label)
    
    self.status_dropdown = QComboBox()
    self.status_dropdown.setObjectName("seta_baixo")
    self.status_dropdown.addItems([
        "SEÇÃO CONTRATOS", "EMPRESA", "SIGDEM", "SIGAD","ASSINADO", "PUBLICADO",
        "PORTARIA", "ALERTA PRAZO", "NOTA TÉCNICA", "AGU", "PRORROGADO"
    ])
    self.status_dropdown.setFixedWidth(220)
    status_layout.addWidget(self.status_dropdown)
    main_layout.addLayout(status_layout)

    # ==== COLUNA DE REGISTROS (CENTRO) ====
    registros_section = QVBoxLayout()
    
    registros_frame = QFrame()
    registros_frame.setObjectName("registros_frame")
    registros_frame.setFrameShape(QFrame.Shape.StyledPanel)
    registros_list_layout = QVBoxLayout(registros_frame)
    
    self.registro_list = QListWidget()
    self.registro_list.setObjectName("registro_list")
    registros_list_layout.addWidget(self.registro_list)
    registros_section.addWidget(registros_frame)

    # --- LINHA 1 DE BOTÕES: Gerenciamento de Registros ---
    registro_mgmt_layout = QHBoxLayout()
    self.add_record_button = QPushButton(" Adicionar Registro")
    self.add_record_button.setIcon(icon_manager.get_icon("registrar_status"))
    self.add_record_button.clicked.connect(self.registro_def)
    
    self.delete_registro_button = QPushButton(" Excluir Registro")
    self.delete_registro_button.setIcon(icon_manager.get_icon("delete"))
    self.delete_registro_button.clicked.connect(self.delete_registro)

    
    self.copy_registro_button = QPushButton(" Copiar Registro")
    self.copy_registro_button.setIcon(icon_manager.get_icon("copy"))
    self.copy_registro_button.clicked.connect(self.copy_registro_def)
    
    registro_mgmt_layout.addWidget(self.add_record_button)
    registro_mgmt_layout.addWidget(self.delete_registro_button)
    registro_mgmt_layout.addWidget(self.copy_registro_button)
    registros_section.addLayout(registro_mgmt_layout)

    # Adiciona tudo ao layout principal
    main_layout.addLayout(registros_section)

    return self.status_tab
