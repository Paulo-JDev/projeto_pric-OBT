from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QHeaderView, QGridLayout, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Gerenciador de UASG")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Input Tab
        self.input_tab = QWidget()
        self.input_layout = QVBoxLayout(self.input_tab)

        self.label = QLabel("Digite o número do UASG:")
        self.input_layout.addWidget(self.label)

        self.uasg_input = QLineEdit()
        self.input_layout.addWidget(self.uasg_input)

        self.fetch_button = QPushButton("Buscar e Criar Tabela")
        self.fetch_button.clicked.connect(self.controller.fetch_and_create_table)
        self.input_layout.addWidget(self.fetch_button)

        self.delete_button = QPushButton("Deletar Arquivo e Banco de Dados")
        self.delete_button.clicked.connect(self.controller.delete_uasg_data)
        self.input_layout.addWidget(self.delete_button)

        self.tabs.addTab(self.input_tab, "Buscar UASG")

        # Table Tab
        self.table_tab = QWidget()
        self.table_layout = QVBoxLayout(self.table_tab)

        self.buttons_grid = QGridLayout()
        self.menu_button = QPushButton("UASG")
        self.menu_button.setMenu(QMenu(self.menu_button))
        self.buttons_grid.addWidget(self.menu_button, 0, 0)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.controller.clear_table)
        self.buttons_grid.addWidget(self.clear_button, 0, 1)

        self.table_layout.addLayout(self.buttons_grid)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.textChanged.connect(self.controller.filter_table)
        self.table_layout.addWidget(self.search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Dias", "Sigla OM", "Contrato/Ata", "Processo", "Fornecedor", "N° de Serie", "Objeto"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # Permite a exibição do menu de contexto
        self.table.customContextMenuRequested.connect(self.controller.show_context_menu) # Exibe o menu de contexto

        self.table.verticalHeader().setVisible(False) # Oculta os números das linhas

        self.table_layout.addWidget(self.table) # Adiciona a tabela ao layout

        self.tabs.addTab(self.table_tab, "Visualizar Tabelas")


#  ==========================================================================================================================================================

import os
import json
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QScrollArea, QWidget, QPushButton,
    QTabWidget, QFormLayout, QHBoxLayout, QLineEdit, QRadioButton, QButtonGroup, QComboBox, QTextEdit, QListWidget, QListWidgetItem, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard

class DetailsDialog(QDialog):
    save_file = "status_data.json"  # Arquivo para salvar o status e os comentários

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(800, 750)

        self.load_styles()

        self.data = data
        self.main_layout = QVBoxLayout(self)

        # Criar o TabWidget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Criar abas
        self.create_general_tab()
        self.create_object_tab()
        self.create_status_tab()  # Atualização na aba Status

        # Botão de salvar
        close_button = QPushButton("Salvar")
        close_button.clicked.connect(self.close_and_save)
        self.main_layout.addWidget(close_button)

        # Carregar dados salvos
        self.load_status()

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
            ("Contrato/Ata:", "contrato"),
            ("Número:", "numero"),
            ("NUP:", "processo"),
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

        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

        # Campo Empresa obtendo apenas o nome correto dentro de "fornecedor"
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

        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

        # Campo CNPJ obtendo a informação correta do JSON
        cnpj_label = QLabel("CNPJ:")
        cnpj_hbox = QHBoxLayout()
        
        # Acessando a chave "cnpj_cpf_idgener" dentro de "fornecedor"
        cnpj_value = self.data.get("fornecedor", {}).get("cnpj_cpf_idgener", "Não informado")
        self.cnpj_edit = QLineEdit(str(cnpj_value))
        self.cnpj_edit.setReadOnly(True)

        copy_cnpj_button = QPushButton("Copiar")
        copy_cnpj_button.clicked.connect(lambda: self.copy_to_clipboard(self.cnpj_edit))

        cnpj_hbox.addWidget(self.cnpj_edit)
        cnpj_hbox.addWidget(copy_cnpj_button)
        scroll_layout.addRow(cnpj_label, cnpj_hbox)

        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

        objeto_label = QLabel("Objeto:")
        objeto_hbox = QHBoxLayout()
        self.objeto_edit = QLineEdit(str(self.data.get("objeto", "Não informado")))
        copy_objeto_button = QPushButton("Copiar")
        copy_objeto_button.clicked.connect(lambda: self.copy_to_clipboard(self.objeto_edit))

        objeto_hbox.addWidget(self.objeto_edit)
        objeto_hbox.addWidget(copy_objeto_button)
        scroll_layout.addRow(objeto_label, objeto_hbox)

        #\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

        # Adicionar radio buttons (corrigido)
        self.radio_groups = {}
        self.radio_buttons = {}
        self.add_radio_buttons(scroll_layout)

        layout.addWidget(scroll)
        self.tabs.addTab(general_tab, "Informações Gerais")

    def create_object_tab(self):
        """Cria a aba para exibir o Objeto"""
        object_tab = QWidget()
        layout = QVBoxLayout(object_tab)

        key_label = QLabel("<b>Objeto:</b>")
        value_label = QLabel(self.objeto_edit.text())  # Pega do campo editável
        value_label.setWordWrap(True)

        layout.addWidget(key_label)
        layout.addWidget(value_label)

        self.tabs.addTab(object_tab, "Objeto")

    def create_status_tab(self):
        """Cria a aba 'Status' com dropdown de seleção, botões e lista de comentários"""
        self.status_tab = QWidget()
        layout = QVBoxLayout(self.status_tab)

        # Layout horizontal para Status
        status_layout = QHBoxLayout()

        # Dropdown para selecionar status
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems([
            "Ata Gerada", "Empresa", "SIGDEM", "Assinado", "Publicado",
            "Alerta Prazo", "Seção de Contratos", "Nota Técnica", "AGU", "Prorrogado"
        ])
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.status_dropdown)

        layout.addLayout(status_layout)

        # Botão para adicionar registro
        self.add_record_button = QPushButton("Adicionar Registro")
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

        self.tabs.addTab(self.status_tab, "Status")

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
            self.radio_groups[title] = radio_group  
            self.radio_buttons[title] = {}

            for option in choices:
                radio = QRadioButton(option)
                group_layout.addWidget(radio)
                radio_group.addButton(radio)
                self.radio_buttons[title][option] = radio  # Salvar referência dos botões

            layout.addRow(group)

    def add_comment(self):
        """Adiciona um comentário na lista"""
        comment_text = self.comment_box.toPlainText().strip()
        if comment_text:
            item = QListWidgetItem(comment_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.comment_list.addItem(item)
            self.comment_box.clear()  # Limpa a caixa de texto

    def delete_comment(self):
        """Remove os comentários selecionados"""
        for i in range(self.comment_list.count() - 1, -1, -1):  # Iteração reversa para remoção segura
            item = self.comment_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.comment_list.takeItem(i)

    def close_and_save(self):
        """Salva o status e os comentários ao fechar a janela"""
        self.save_status()
        self.close()

    def save_status(self):
        """Salva o status, comentários e opções dos radio buttons"""
        status_data = {
            "status": self.status_dropdown.currentText(),
            "comments": [self.comment_list.item(i).text() for i in range(self.comment_list.count())],
            "objeto": self.objeto_edit.text(),  
            "radio_options": {title: next(
                (option for option, button in self.radio_buttons[title].items() if button.isChecked()), "Não selecionado"
            ) for title in self.radio_buttons}
        }

        with open(self.save_file, "w", encoding="utf-8") as file:
            json.dump(status_data, file, ensure_ascii=False, indent=4)

    def load_status(self):
        """Carrega os dados salvos no JSON"""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r", encoding="utf-8") as file:
                status_data = json.load(file)

                self.status_dropdown.setCurrentText(status_data.get("status", ""))
                self.objeto_edit.setText(status_data.get("objeto", "Não informado"))

                for title, selected_value in status_data.get("radio_options", {}).items():
                    if selected_value in self.radio_buttons.get(title, {}):
                        self.radio_buttons[title][selected_value].setChecked(True)

                for comment in status_data.get("comments", []):
                    item = QListWidgetItem(comment)
                    item.setCheckState(Qt.CheckState.Checked)
                    self.comment_list.addItem(item)

    # def add_radio_buttons(self, layout):
    #     """Adiciona opções de radio buttons para escolha de atributos"""
    #     def create_radio_group(title, options):
    #         group = QWidget()
    #         group_layout = QHBoxLayout(group)
    #         group_layout.addWidget(QLabel(title))
    #         radio_group = QButtonGroup(self)
    #         for option in options:
    #             radio = QRadioButton(option)
    #             group_layout.addWidget(radio)
    #             radio_group.addButton(radio)
    #         layout.addRow(group)
        
    #     create_radio_group("Pode Renovar?", ["Sim", "Não"])
    #     create_radio_group("Custeio?", ["Sim", "Não"])
    #     create_radio_group("Natureza Continuada?", ["Sim", "Não"])
    #     create_radio_group("Material/Serviço?", ["Material", "Serviço"])


    def copy_to_clipboard(self, line_edit):
        """Copia o texto do campo para a área de transferência"""
        clipboard = QApplication.clipboard()
        clipboard.setText(line_edit.text())

    def load_styles(self):
        """Carrega os estilos do arquivo style.qss"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.abspath(os.path.join(base_dir, ".."))
        style_path = os.path.join(project_dir, "style.qss")

        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠ Arquivo {style_path} não encontrado. Estilos não foram aplicados.")
