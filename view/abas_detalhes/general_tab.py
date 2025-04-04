from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from pathlib import Path
from datetime import datetime
from utils.icon_loader import icon_manager

def create_general_tab(self):
    """Cria a aba de Informações Gerais com layout lado a lado"""
    general_tab = QWidget()
    main_layout = QVBoxLayout(general_tab)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    # Verificação inicial dos dados
    if not self.data:
        main_layout.addWidget(QLabel("Erro: Nenhum dado foi carregado para o contrato."))
        return general_tab

    # Título do contrato
    contrato_title = QLabel(f"Contrato {self.data.get('numero', '')} - {self.data.get('objeto', '')[:50]}...")
    contrato_title.setStyleSheet("font-size: 16px; font-weight: bold;")
    main_layout.addWidget(contrato_title)

    # Layout principal lado a lado
    content_layout = QHBoxLayout()
    content_layout.setSpacing(20)

    # Coluna esquerda - Informações
    left_column = QVBoxLayout()
    left_column.setSpacing(15)

    # Seção de Informações Básicas
    info_group = QGroupBox("Informações")
    info_layout = QFormLayout(info_group)
    info_layout.setVerticalSpacing(10)
    info_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    info_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

    # Função para formatar data (de YYYY-MM-DD para DD/MM/YYYY)
    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return date_str

    # Função modificada com largura intermediária
    def create_field_row(label_text, field_name, parent_layout, full_width=False):
        hbox = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; min-width: 140px;")  # Largura aumentada para labels
        
        def get_nested_value(data, keys):
            keys = keys.split('.')
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key, {})
                else:
                    return "Não informado"
            return data if (data and data != {}) else "Não informado"
        
        value = get_nested_value(self.data, field_name)
        
        if field_name in ["vigencia_inicio", "vigencia_fim"]:
            value = format_date(value)
            
        line_edit = QLineEdit(str(value))
        line_edit.setReadOnly(True)
        line_edit.setStyleSheet("min-width: 300px; max-width: 300px;")  # Aumentado para 250px (quase o dobro)
        
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        copy_btn.setToolTip("Copiar")
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(line_edit))
        
        hbox.addWidget(line_edit, stretch=0)
        if not full_width:
            hbox.addWidget(copy_btn, stretch=0)
        hbox.addStretch(1)
        parent_layout.addRow(label, hbox)
        return line_edit

    # Campos principais
    self.line_edits = {
        "numero": create_field_row("Número:", "numero", info_layout),
        "licitacao_numero": create_field_row("Número Licitação:", "licitacao_numero", info_layout),
        "processo": create_field_row("NUP:", "processo", info_layout),
        "valor_global": create_field_row("Valor Global:", "valor_global", info_layout),
        "cnpj": create_field_row("CNPJ:", "fornecedor.cnpj_cpf_idgener", info_layout),
        "empresa": create_field_row("Empresa:", "fornecedor.nome", info_layout),
        "vigencia_inicio": create_field_row("Início Vigência:", "vigencia_inicio", info_layout),
        "vigencia_fim": create_field_row("Fim Vigência:", "vigencia_fim", info_layout)
    }
    
    # Campo "Objeto" editável
    objeto_label = QLabel("Objeto:")
    objeto_label.setStyleSheet("font-weight: bold; min-width: 140px;")
    self.objeto_edit = QLineEdit()
    self.objeto_edit.setText(self.data.get("objeto", ""))
    self.objeto_edit.setMinimumWidth(320)  # Largura específica para o objeto
    self.objeto_edit.setMaximumWidth(320)  # Fixa o tamanho
    hbox = QHBoxLayout()
    hbox.addWidget(self.objeto_edit, stretch=1)
    copy_btn = QPushButton()
    copy_btn.setIcon(icon_manager.get_icon("copy"))
    copy_btn.setIconSize(QSize(16, 16))
    copy_btn.setFixedSize(24, 24)
    copy_btn.setToolTip("Copiar")
    copy_btn.clicked.connect(lambda: self.copy_to_clipboard(self.objeto_edit))
    hbox.addWidget(copy_btn, stretch=0)
    info_layout.addRow(objeto_label, hbox)

    left_column.addWidget(info_group)
    
    # Coluna direita - Opções e Gestão
    right_column = QVBoxLayout()
    right_column.setSpacing(15)

    # Seção de Opções
    options_group = QGroupBox("Opções")
    options_layout = QFormLayout(options_group)
    options_layout.setVerticalSpacing(10)

    # Radio buttons
    def create_radio_row(title, options):
        hbox = QHBoxLayout()
        label = QLabel(title)
        label.setStyleSheet("font-weight: bold; min-width: 120px;")
        hbox.addWidget(label)
        
        btn_group = QButtonGroup(self)
        self.radio_groups[title] = btn_group
        self.radio_buttons[title] = {}
        
        for option in options:
            radio = QRadioButton(option)
            radio.setStyleSheet("margin-right: 15px;")
            hbox.addWidget(radio)
            btn_group.addButton(radio)
            self.radio_buttons[title][option] = radio
        
        options_layout.addRow(hbox)

    create_radio_row("Pode Renovar?", ["Sim", "Não"])
    create_radio_row("Custeio?", ["Sim", "Não"])
    create_radio_row("Natureza Continuada?", ["Sim", "Não"])
    create_radio_row("Material/Serviço:", ["Material", "Serviço"])

    right_column.addWidget(options_group)

    # Seção de Gestão/Fiscalização
    gestao_group = QGroupBox("Gestão/Fiscalização")
    gestao_layout = QFormLayout(gestao_group)
    gestao_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    
    # Campos de gestão
    create_field_row("Sigla OM Resp:", "contratante.orgao_origem.unidade_gestora_origem.nome_resumido", gestao_layout)
    create_field_row("UASG:", "contratante.orgao_origem.unidade_gestora_origem.codigo", gestao_layout)
    create_field_row("Órgão Responsável:", "contratante.orgao.unidade_gestora.nome_resumido", gestao_layout)
    create_field_row("Indicativo:", "indicativo", gestao_layout)
    right_column.addWidget(gestao_group)
    right_column.addStretch()

    # Adicionando colunas ao layout principal
    content_layout.addLayout(left_column, 60)
    content_layout.addLayout(right_column, 40)
    
    main_layout.addLayout(content_layout)
    main_layout.addStretch()

    return general_tab