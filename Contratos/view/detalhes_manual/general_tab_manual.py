# Contratos/view/detalhes_manual/general_tab_manual.py

"""
Aba de Informações Gerais para CONTRATOS MANUAIS.
Todos os campos são editáveis.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager

def create_general_tab_manual(parent):
    """
    Cria a aba de Informações Gerais para contratos manuais.
    TODOS os campos são editáveis.
    """
    general_tab = QWidget()
    main_layout = QVBoxLayout(general_tab)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    if not parent.data:
        main_layout.addWidget(QLabel("Erro: Nenhum dado foi carregado para o contrato."))
        return general_tab

    # ==================== TÍTULO ====================
    title_layout = QHBoxLayout()
    
    brasil_icon = QLabel()
    brasil_icon.setPixmap(icon_manager.get_icon("brasil_2").pixmap(32, 32))
    brasil_icon.setFixedSize(32, 32)
    title_layout.addWidget(brasil_icon)
    
    numero_contrato = parent.data.get('numero', 'N/A')
    title_label = QLabel(f"Contrato Manual {numero_contrato}")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")  # Dourado para destacar
    title_layout.addWidget(title_label)
    title_layout.addStretch(1)
    
    main_layout.addLayout(title_layout)

    # ==================== LAYOUT LADO A LADO ====================
    content_layout = QHBoxLayout()
    content_layout.setSpacing(20)

    # ==================== COLUNA ESQUERDA ====================
    left_column = QVBoxLayout()
    left_column.setSpacing(15)

    info_group = QGroupBox("INFORMAÇÕES")
    info_layout = QFormLayout(info_group)
    info_layout.setVerticalSpacing(10)

    # Função helper para criar campos EDITÁVEIS
    def create_editable_field(label_text, field_name, initial_value=""):
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; min-width: 140px;")
        
        hbox = QHBoxLayout()
        
        line_edit = QLineEdit(initial_value)
        line_edit.setStyleSheet("min-width: 300px; max-width: 300px;")
        line_edit.setPlaceholderText(f"Digite {label_text.lower()}")
        
        # Armazena referência no parent
        setattr(parent, field_name, line_edit)
        
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        copy_btn.setToolTip("Copiar")
        copy_btn.clicked.connect(lambda: parent.copy_to_clipboard(line_edit))
        
        hbox.addWidget(line_edit, stretch=0)
        hbox.addWidget(copy_btn, stretch=0)
        hbox.addStretch(1)
        
        info_layout.addRow(label, hbox)
        return line_edit

    # ==================== CAMPOS EDITÁVEIS ====================
    parent.line_edits = {}
    
    parent.line_edits["numero"] = create_editable_field(
        "Número:", "manual_numero", parent.data.get('numero', '')
    )
    
    parent.line_edits["licitacao_numero"] = create_editable_field(
        "Número Licitação:", "manual_licitacao", parent.data.get('licitacao_numero', '')
    )
    
    parent.line_edits["processo"] = create_editable_field(
        "NUP:", "manual_nup", parent.data.get('processo', '')
    )
    
    parent.line_edits["valor_global"] = create_editable_field(
        "Valor Global:", "manual_valor", parent.data.get('valor_global', '')
    )
    
    parent.line_edits["cnpj"] = create_editable_field(
        "CNPJ:", "manual_cnpj", 
        parent.data.get('fornecedor', {}).get('cnpj_cpf_idgener', '')
    )
    
    parent.line_edits["empresa"] = create_editable_field(
        "Empresa:", "manual_empresa", 
        parent.data.get('fornecedor', {}).get('nome', '')
    )
    
    parent.line_edits["vigencia_inicio"] = create_editable_field(
        "Início Vigência:", "manual_vigencia_inicio", 
        parent.data.get('vigencia_inicio', '')
    )
    
    parent.line_edits["vigencia_fim"] = create_editable_field(
        "Fim Vigência:", "manual_vigencia_fim", 
        parent.data.get('vigencia_fim', '')
    )

    # Campo Objeto (editável com botão de edição)
    objeto_label = QLabel("Objeto:")
    objeto_label.setStyleSheet("font-weight: bold; min-width: 140px;")
    
    parent.objeto_edit = QLineEdit()
    parent.objeto_edit.setText(parent.data.get("objeto", ""))
    parent.objeto_edit.setMinimumWidth(300)
    parent.objeto_edit.setMaximumWidth(300)
    parent.objeto_edit.setPlaceholderText("Digite o objeto do contrato")
    
    hbox = QHBoxLayout()
    hbox.addWidget(parent.objeto_edit, stretch=1)
    
    edit_obj_btn = QPushButton()
    edit_obj_btn.setIcon(icon_manager.get_icon("edit"))
    edit_obj_btn.setIconSize(QSize(16, 16))
    edit_obj_btn.setFixedSize(24, 24)
    edit_obj_btn.setToolTip("Editar Objeto")
    edit_obj_btn.clicked.connect(parent.open_object_editor)
    hbox.addWidget(edit_obj_btn, stretch=0)
    
    copy_btn = QPushButton()
    copy_btn.setIcon(icon_manager.get_icon("copy"))
    copy_btn.setIconSize(QSize(16, 16))
    copy_btn.setFixedSize(24, 24)
    copy_btn.setToolTip("Copiar")
    copy_btn.clicked.connect(lambda: parent.copy_to_clipboard(parent.objeto_edit))
    hbox.addWidget(copy_btn, stretch=0)
    
    info_layout.addRow(objeto_label, hbox)
    
    left_column.addWidget(info_group)

    # ==================== COLUNA DIREITA ====================
    right_column = QVBoxLayout()
    right_column.setSpacing(15)

    # Seção de Opções
    options_group = QGroupBox("OPÇÕES")
    options_layout = QFormLayout(options_group)
    options_layout.setVerticalSpacing(10)

    parent.radio_groups = {}
    parent.radio_buttons = {}

    def create_radio_row(title, options):
        hbox = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; min-width: 120px;")
        hbox.addWidget(label)
        
        btn_group = QButtonGroup(parent)
        parent.radio_groups[title] = btn_group
        parent.radio_buttons[title] = {}
        
        for option in options:
            radio = QRadioButton(option)
            radio.setStyleSheet("margin-right: 15px;")
            hbox.addWidget(radio)
            btn_group.addButton(radio)
            parent.radio_buttons[title][option] = radio
        
        options_layout.addRow(hbox)

    create_radio_row("Pode Renovar?", ["Sim", "Não"])
    create_radio_row("Custeio?", ["Sim", "Não"])
    create_radio_row("Natureza Continuada?", ["Sim", "Não"])
    create_radio_row("Material/Serviço:", ["Material", "Serviço"])
    
    right_column.addWidget(options_group)

    # Seção de Gestão/Fiscalização
    gestao_group = QGroupBox("GESTÃO/FISCALIZAÇÃO")
    gestao_layout = QFormLayout(gestao_group)

    # Campos editáveis de gestão
    def create_gestao_field(label_text, field_name, initial_value=""):
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; min-width: 140px;")
        
        line_edit = QLineEdit(initial_value)
        line_edit.setMinimumWidth(320)
        line_edit.setMaximumWidth(320)
        line_edit.setPlaceholderText(f"Digite {label_text.lower()}")
        
        setattr(parent, field_name, line_edit)
        
        hbox = QHBoxLayout()
        hbox.addWidget(line_edit, stretch=1)
        
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        copy_btn.setToolTip("Copiar")
        copy_btn.clicked.connect(lambda: parent.copy_to_clipboard(line_edit))
        hbox.addWidget(copy_btn, stretch=0)
        
        gestao_layout.addRow(label, hbox)
        return line_edit

    create_gestao_field("Sigla OM Resp:", "manual_sigla_om", "")
    create_gestao_field("Órgão Responsável:", "manual_orgao", "")
    create_gestao_field("Tipo:", "manual_tipo", parent.data.get('tipo', ''))
    create_gestao_field("Modalidade:", "manual_modalidade", parent.data.get('modalidade', ''))
    
    parent.portaria_edit = create_gestao_field("Portaria:", "portaria_edit", "")
    parent.termo_aditivo_edit = create_gestao_field("Termo Aditivo:", "termo_aditivo_edit", "")
    
    right_column.addWidget(gestao_group)
    right_column.addStretch()

    # Adiciona colunas ao layout principal
    content_layout.addLayout(left_column, 60)
    content_layout.addLayout(right_column, 40)
    
    main_layout.addLayout(content_layout)
    main_layout.addStretch()

    return general_tab
