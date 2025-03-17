from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QHeaderView, QGridLayout, QMenu, QTableView
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItemModel
from pathlib import Path
import os

from controller.detalhe_controller import setup_search_bar, MultiColumnFilterProxyModel

class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Gerenciador de UASG")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(1000, 600)

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
        self.menu_button.setMenu(QMenu(self.menu_button))
        self.buttons_grid.addWidget(self.menu_button, 0, 0)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.controller.clear_table)
        self.buttons_grid.addWidget(self.clear_button, 0, 1)

        self.table_layout.addLayout(self.buttons_grid)
        # self.table_layout.setSpacing(0)  # Remove espaçamento entre widgets
        # self.table_layout.setContentsMargins(0, 10, 0, 0)  # Remove margens ao redor do layout

        # Adiciona a tabela
        self.table = QTableView()
        self.table.setStyleSheet("""
            QTableView::item {
                border-bottom: 1px solid #333333;    /* Borda inferior das células */
                border-right: 1px solid #333333; /* Borda lateral direita */
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
        """Carrega os estilos do arquivo style.qss"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.abspath(os.path.join(base_dir, ".."))
        style_path = os.path.join(project_dir, "style.qss")

        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠ Arquivo {style_path} não encontrado. Estilos não foram aplicados.")

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        base_dir = Path(__file__).parent.parent  # Pasta do arquivo atual
        icons_dir = base_dir / "utils" / "icons"  # Caminho para a pasta de ícones
        icon_file = "mn.png"  # Substitua pelo nome do seu arquivo de ícone
        icon_path = icons_dir / icon_file

        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))  # Define o ícone da janela
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")
    
    