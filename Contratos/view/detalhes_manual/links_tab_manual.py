# Contratos/view/detalhes_manual/links_tab_manual.py

"""
Aba de Links para CONTRATOS MANUAIS.
Não possui links automáticos (Comprasnet/PNCP).
Apenas campos editáveis para documentos.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QHBoxLayout, QGroupBox
)
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager


def create_links_tab_manual(parent):
    """
    Cria a aba de Links para contratos manuais.
    Sem links automáticos, apenas campos editáveis.
    """
    links_tab = QWidget()
    main_layout = QVBoxLayout(links_tab)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(20)

    # ==================== TÍTULO ====================
    title = QLabel("Links de Documentos do Contrato Manual")
    title.setStyleSheet("font-size: 14px; font-weight: bold;")
    main_layout.addWidget(title)

    # ==================== GRUPO DE LINKS ====================
    links_group = QGroupBox("DOCUMENTOS")
    links_layout = QFormLayout(links_group)
    links_layout.setVerticalSpacing(15)

    # Função helper para criar campos de link
    def create_link_field(label_text, field_name, placeholder):
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; min-width: 180px;")
        
        hbox = QHBoxLayout()
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setMinimumWidth(500)
        
        # Armazena referência no parent
        setattr(parent, field_name, line_edit)
        
        hbox.addWidget(line_edit, stretch=1)
        
        # Botão de copiar
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        copy_btn.setToolTip("Copiar")
        copy_btn.clicked.connect(lambda: parent.copy_to_clipboard(line_edit))
        hbox.addWidget(copy_btn, stretch=0)
        
        # Botão de abrir link
        open_btn = QPushButton()
        open_btn.setIcon(icon_manager.get_icon("link"))
        open_btn.setIconSize(QSize(16, 16))
        open_btn.setFixedSize(24, 24)
        open_btn.setToolTip("Abrir Link")
        open_btn.clicked.connect(lambda: parent.open_link(line_edit.text()))
        hbox.addWidget(open_btn, stretch=0)
        
        links_layout.addRow(label, hbox)
        return line_edit

    # ==================== CAMPOS DE LINKS ====================
    parent.link_contrato_le = create_link_field(
        "Link PDF do Contrato:", 
        "link_contrato_le", 
        "Cole o link do PDF do contrato"
    )
    
    parent.link_ta_le = create_link_field(
        "Link Termo Aditivo (TA):", 
        "link_ta_le", 
        "Cole o link do Termo Aditivo"
    )
    
    parent.link_portaria_le = create_link_field(
        "Link Portaria:", 
        "link_portaria_le", 
        "Cole o link da Portaria"
    )
    
    parent.link_pncp_espc_le = create_link_field(
        "Link PNCP Específico:", 
        "link_pncp_espc_le", 
        "Cole o link específico do contrato no PNCP"
    )
    
    parent.link_portal_marinha_le = create_link_field(
        "Link Portal Marinha:", 
        "link_portal_marinha_le", 
        "Cole o link do Portal da Marinha"
    )

    main_layout.addWidget(links_group)
    main_layout.addStretch()

    return links_tab
