from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QHeaderView, QGridLayout, QMenu, QTableView
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
import os

from controller.detalhe_controller import setup_search_bar, MultiColumnFilterProxyModel
from model.uasg_model import resource_path

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
        self.input_layout.addWidget(self.uasg_input)

        self.fetch_button = QPushButton("Criação ou atualização da tabela")
        self.fetch_button.clicked.connect(self.controller.fetch_and_create_table)
        self.input_layout.addWidget(self.fetch_button)

        self.delete_button = QPushButton("Deletar Arquivo e Banco de Dados")
        self.delete_button.clicked.connect(self.controller.delete_uasg_data)
        self.input_layout.addWidget(self.delete_button)

        self.tabs.addTab(self.input_tab, "Buscar UASG")

        # Table Tab
        self.table_tab = QWidget()
        self.table_layout = QVBoxLayout(self.table_tab)

        # Adiciona os botões
        self.buttons_grid = QGridLayout()
        self.menu_button = QPushButton("UASG")
        self.menu_button.setMenu(QMenu(self.menu_button))  # Conecta o botão ao menu
        self.buttons_grid.addWidget(self.menu_button, 0, 0)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.controller.clear_table)
        self.buttons_grid.addWidget(self.clear_button, 0, 1)

        self.table_layout.addLayout(self.buttons_grid)

        # Adiciona a tabela
        self.table = QTableView()
        self.table.setStyleSheet("""
        QTableView::item:selected {
                background-color: rgba(163, 213, 255, 0.4);
            }
        """)
        self.model = QStandardItemModel()  # Modelo base
        self.proxy_model = MultiColumnFilterProxyModel()  # Proxy model
        # Adiciona a barra de busca
        icons = {
            "magnifying-glass": QIcon("caminho/para/icone_lupa.png")  # Substitua pelo caminho do ícone
        }
        self.search_bar = setup_search_bar(icons, self.table_layout, self.proxy_model, self.table)
        
        self.proxy_model.setSourceModel(self.model)  # Define o modelo base
        self.table.setModel(self.proxy_model)  # Aplica o proxy model à tabela
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.controller.show_context_menu)
        self.table.verticalHeader().setVisible(False)

        self.table_layout.addWidget(self.table)

        self.tabs.addTab(self.table_tab, "Visualizar Tabelas")

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
    
    