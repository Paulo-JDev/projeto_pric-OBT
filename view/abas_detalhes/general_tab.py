from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt

def create_general_tab(self):
    """Cria a aba de Informações Gerais"""
    general_tab = QWidget()
    layout = QVBoxLayout(general_tab)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    scroll_layout = QFormLayout(scroll_widget)
    scroll.setWidget(scroll_widget)

    # Criar os campos conforme a imagem
    fields = [
        ("ID Processo:", "licitacao_numero"),
        ("Número:", "numero"),
        ("NUP:", "processo"),
        ("Vigencia Inicio:", "vigencia_inicio"),
        ("Vigencia Final:", "vigencia_fim"),
        ("Valor Global:", "valor_global"),
        ("Tipo: ", "tipo"),
    ]

    self.line_edits = {}  # Armazena os campos de entrada

    for label_text, field in fields:
        hbox = QHBoxLayout()
        label = QLabel(label_text)

        line_edit = QLineEdit(str(self.data.get(field, "Não informado")))
        line_edit.setReadOnly(True)

        # Criar botão de copiar
        copy_button = QPushButton("Copiar")
        copy_button.clicked.connect(lambda _, text=line_edit: self.copy_to_clipboard(text))

        hbox.addWidget(line_edit)
        hbox.addWidget(copy_button)

        self.line_edits[field] = line_edit
        scroll_layout.addRow(label, hbox)

    # Campo Empresa
    empresa_label = QLabel("Empresa:")
    empresa_hbox = QHBoxLayout()

    empresa_value = self.data.get("fornecedor", {}).get("nome", "Não informado")
    self.empresa_edit = QLineEdit(str(empresa_value))
    self.empresa_edit.setReadOnly(True)

    copy_empresa_button = QPushButton("Copiar")
    copy_empresa_button.clicked.connect(lambda: self.copy_to_clipboard(self.empresa_edit))

    empresa_hbox.addWidget(self.empresa_edit)
    empresa_hbox.addWidget(copy_empresa_button)
    scroll_layout.addRow(empresa_label, empresa_hbox)

    # Campo CNPJ
    cnpj_label = QLabel("CNPJ:")
    cnpj_hbox = QHBoxLayout()
    
    cnpj_value = self.data.get("fornecedor", {}).get("cnpj_cpf_idgener", "Não informado")
    self.cnpj_edit = QLineEdit(str(cnpj_value))
    self.cnpj_edit.setReadOnly(True)

    copy_cnpj_button = QPushButton("Copiar")
    copy_cnpj_button.clicked.connect(lambda: self.copy_to_clipboard(self.cnpj_edit))

    cnpj_hbox.addWidget(self.cnpj_edit)
    cnpj_hbox.addWidget(copy_cnpj_button)
    scroll_layout.addRow(cnpj_label, cnpj_hbox)

    # Campo Objeto
    objeto_label = QLabel("Objeto:")
    objeto_hbox = QHBoxLayout()
    self.objeto_edit = QLineEdit(str(self.data.get("objeto", "Não informado")))
    copy_objeto_button = QPushButton("Copiar")
    copy_objeto_button.clicked.connect(lambda: self.copy_to_clipboard(self.objeto_edit))

    objeto_hbox.addWidget(self.objeto_edit)
    objeto_hbox.addWidget(copy_objeto_button)
    scroll_layout.addRow(objeto_label, objeto_hbox)

    # # Adicionar radio buttons
    # self.add_radio_buttons(scroll_layout)
    add_radio_buttons(self, scroll_layout)  # Chamada da função movida

    layout.addWidget(scroll)
    return general_tab

def add_radio_buttons(self, layout):
    """Adiciona opções de radio buttons e corrige salvamento"""
    options = {
        "Pode Renovar?": ["Sim", "Não"],
        "Custeio?": ["Sim", "Não"],
        "Natureza Continuada?": ["Sim", "Não"],
        "Material/Serviço?": ["Material", "Serviço"]
    }

    for title, choices in options.items():
        group = QWidget()
        group_layout = QHBoxLayout(group)
        group_layout.addWidget(QLabel(title))

        radio_group = QButtonGroup(self)
        self.radio_groups[title] = radio_group  # Adiciona ao dicionário
        self.radio_buttons[title] = {}  # Inicializa o dicionário de botões

        for option in choices:
            radio = QRadioButton(option)
            group_layout.addWidget(radio)
            radio_group.addButton(radio)
            self.radio_buttons[title][option] = radio  # Salva referência dos botões

        layout.addRow(group)
