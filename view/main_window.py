from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QHeaderView, QGridLayout, QMenu, QTableView
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
import os

from utils.utils import setup_search_bar, MultiColumnFilterProxyModel
from model.uasg_model import resource_path
from utils.icon_loader import icon_manager

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Gerenciador de UASG")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(1150, 600)

        self.set_window_icon()
        self.load_styles()

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
        self.uasg_input.setPlaceholderText("Ex: 787010")
        self.input_layout.addWidget(self.uasg_input)

        self.fetch_button = QPushButton("Criação ou atualização da tabela")
        self.fetch_button.setIcon(icon_manager.get_icon("api"))
        self.fetch_button.clicked.connect(self.controller.fetch_and_create_table)
        self.input_layout.addWidget(self.fetch_button)

        self.delete_button = QPushButton("Deletar Arquivo e Banco de Dados")
        self.delete_button.setIcon(icon_manager.get_icon("delete"))
        self.delete_button.clicked.connect(self.controller.delete_uasg_data)
        self.input_layout.addWidget(self.delete_button)

        self.tabs.addTab(self.input_tab, icon_manager.get_icon("dash"), "Buscar UASG")

        # Table Tab
        self.table_tab = QWidget()
        self.table_layout = QVBoxLayout(self.table_tab)
        self.table_layout.setSpacing(5)  # Reduz o espaçamento entre elementos
        self.table_layout.setContentsMargins(10, 5, 10, 10)  # Reduz a margem superior

        # Adiciona os botões
        self.buttons_grid = QGridLayout()
        self.buttons_grid.setContentsMargins(0, 0, 0, 0)  # Remove margens internas
        self.buttons_grid.setSpacing(15)  # Espaçamento entre botões
        
        # Botão UASG com menu
        self.menu_button = QPushButton("UASG")
        self.menu_button.setIcon(icon_manager.get_icon("data-server"))
        menu = QMenu(self.menu_button)
        self.menu_button.setMenu(menu)
        self.menu_button.setObjectName("header_button")  # Nome para CSS
        self.buttons_grid.addWidget(self.menu_button, 0, 0)

        # Botão Limpar
        self.clear_button = QPushButton("Limpar")
        self.clear_button.setIcon(icon_manager.get_icon("limp-blue"))
        self.clear_button.clicked.connect(self.controller.clear_table)
        self.clear_button.setObjectName("header_button")  # Nome para CSS
        self.buttons_grid.addWidget(self.clear_button, 0, 1)

        # Botão Mensagens com tamanho fixo
        self.msg_button = QPushButton("Mensagens")
        self.msg_button.setIcon(icon_manager.get_icon("mensagem"))
        self.msg_button.clicked.connect(self.controller.show_msg_dialog)
        self.msg_button.setObjectName("header_button")  # Nome para CSS
        self.buttons_grid.addWidget(self.msg_button, 0, 2)
        
        # Label para UASG atual
        self.uasg_info_label = QLabel("UASG: -")
        self.uasg_info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.uasg_info_label.setObjectName("uasg_info_label")  # Nome para CSS
        self.buttons_grid.addWidget(self.uasg_info_label, 0, 4)
        
        # Espaçador para empurrar o label para a direita
        self.buttons_grid.setColumnStretch(3, 1)
        # Remover stretch dos botões para que tenham tamanho uniforme
        self.buttons_grid.setColumnStretch(0, 0)
        self.buttons_grid.setColumnStretch(1, 0)
        self.buttons_grid.setColumnStretch(2, 0)

        self.table_layout.addLayout(self.buttons_grid)

        # Adiciona a tabela
        self.table = QTableView()
        self.table.setStyleSheet("""
        QTableView::item:selected {
                background-color: rgba(163, 213, 255, 0.4);
            }
        """)
        self.table.setContentsMargins(0, 0, 0, 0)  # Remove margens
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Barra de rolagem apenas quando necessário
        
        self.model = QStandardItemModel()  # Modelo base
        self.proxy_model = MultiColumnFilterProxyModel()  # Proxy model
        
        # Adiciona a barra de busca
        icons = {
            "magnifying-glass": icon_manager.get_icon("find")
        }
        self.search_bar = setup_search_bar(icons, self.table_layout, self.proxy_model, self.table)
        
        # Pequeno espaço entre a barra de busca e a tabela
        self.table_layout.addSpacing(2)
        
        self.proxy_model.setSourceModel(self.model)  # Define o modelo base
        self.table.setModel(self.proxy_model)  # Aplica o proxy model à tabela
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.controller.show_context_menu)
        self.table.verticalHeader().setVisible(False)

        self.table_layout.addWidget(self.table)

        self.tabs.addTab(self.table_tab, icon_manager.get_icon("table"), "Visualizar Tabelas")

    def load_styles(self):
        """Carrega os estilos do arquivo style.qss."""
        style_path = resource_path("style.qss")  # Usa resource_path para garantir o caminho correto

        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠ Arquivo {style_path} não encontrado. Estilos não foram aplicados.")

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        # Caminho do ícone na pasta original
        icon_path = resource_path("utils/icons/mn.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")
    
    