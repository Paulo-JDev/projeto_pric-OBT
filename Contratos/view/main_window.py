from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QLineEdit, QPushButton,
    QHeaderView, QGridLayout, QMenu, QTableView, QMessageBox, QHBoxLayout, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem
from datetime import datetime, date
import os

from utils.utils import setup_search_bar, MultiColumnFilterProxyModel
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager
from Contratos.view.dashboard_tab import create_dashboard_tab

from Contratos.view.preview_table import *

class MainWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        """self.setWindowTitle("Gerenciador de UASG")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(1150, 600)"""

        self.set_window_icon()

        self.layout = QVBoxLayout(self) 

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

       # =========================================================================================
        # Novo layout para a aba de Entrada (Buscar UASG)
        # =========================================================================================
        self.input_tab = QWidget()
        self.input_layout = QHBoxLayout(self.input_tab)

        # Frame da Esquerda - Botões de Ação
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_frame.setFixedWidth(300)
        
        # O botão de configurações permanece no mesmo lugar
        settings_hbox = QHBoxLayout()
        settings_hbox.addStretch()
        self.settings_button = QPushButton()
        self.settings_button.setIcon(icon_manager.get_icon("config"))
        self.settings_button.setIconSize(QSize(40, 40))
        self.settings_button.setFixedSize(70, 70)
        self.settings_button.setObjectName("settings_icon_button")
        settings_hbox.addWidget(self.settings_button)
        left_layout.addLayout(settings_hbox)
        
        left_layout.addWidget(QLabel("Digite o número do UASG:"))
        self.uasg_input = QLineEdit()
        self.uasg_input.setPlaceholderText("Ex: 787010")
        self.uasg_input.setFixedWidth(200)
        left_layout.addWidget(self.uasg_input)
        
        self.fetch_button = QPushButton("Criação ou atualização da tabela")
        self.fetch_button.setIcon(icon_manager.get_icon("api"))
        self.fetch_button.clicked.connect(self.controller.fetch_and_create_table)
        left_layout.addWidget(self.fetch_button)
        
        self.delete_button = QPushButton("Deletar Arquivo e Banco de Dados")
        self.delete_button.setIcon(icon_manager.get_icon("delete"))
        self.delete_button.clicked.connect(self.controller.delete_uasg_data)
        left_layout.addWidget(self.delete_button)
        
        self.export_status_button = QPushButton("Exportar Status")
        self.export_status_button.setIcon(icon_manager.get_icon("exportar"))
        self.export_status_button.clicked.connect(self.controller.export_status_data)
        left_layout.addWidget(self.export_status_button)
        
        self.import_status_button = QPushButton("Importar Status")
        self.import_status_button.setIcon(icon_manager.get_icon("importar"))
        self.import_status_button.clicked.connect(self.controller.import_status_data)
        left_layout.addWidget(self.import_status_button)

        self.export_button = QPushButton("Exportar Tabela")
        self.export_button.setIcon(icon_manager.get_icon("excel_down"))
        self.export_button.clicked.connect(self.controller.export_table_to_excel)
        left_layout.addWidget(self.export_button)
        
        left_layout.addStretch() # Empurra tudo para cima
        
        status_hbox = QHBoxLayout()
        self.status_icon_label = QLabel()
        self.status_icon_label.setFixedSize(60, 60)
        status_hbox.addWidget(self.status_icon_label)
        status_hbox.addStretch()
        left_layout.addLayout(status_hbox)

        self.input_layout.addWidget(left_frame)

        # Frame da Direita - Pré-visualização
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        right_frame, self.preview_table, self.preview_model = create_preview_table_widget(self.controller)
        self.input_layout.addWidget(right_frame)

        self.tabs.addTab(self.input_tab, icon_manager.get_icon("dash"), "Buscar UASG")
        
        # Table Tab =====================================================================
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

        # Botão Mensagens com tamanho fixo
        self.msg_button = QPushButton("Mensagens")
        self.msg_button.setIcon(icon_manager.get_icon("mensagem"))
        self.msg_button.clicked.connect(self.controller.show_msg_dialog)
        self.msg_button.setObjectName("header_button")  # Nome para CSS
        self.buttons_grid.addWidget(self.msg_button, 0, 1)

        # Botão Limpar
        self.clear_button = QPushButton() 
        self.clear_button.setFixedSize(32, 32)
        self.clear_button.clicked.connect(self.controller.clear_table)
        self.clear_button.setObjectName("icon_button")
        self.buttons_grid.addWidget(self.clear_button, 0, 2)
        
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
        #self.buttons_grid.setColumnStretch(3, 0)

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

        # Dashboard Tab =================================================================
        self.dashboard_tab = create_dashboard_tab(self)
        self.tabs.addTab(self.dashboard_tab, icon_manager.get_icon("dashboard"), "Dashboard")

        self.tabs.setCurrentIndex(0)

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        # Caminho do ícone na pasta original
        icon_path = resource_path("utils/icons/mn.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Sair do aplicativo",
            "Tem certeza que deseja sair?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Botão padrão
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def update_status_icon(self, mode):
        """Atualiza o ícone de status com base no modo recebido."""
        if mode == "Online":
            self.status_icon_label.setPixmap(icon_manager.get_icon("link").pixmap(60, 60))
            self.status_icon_label.setToolTip("Modo Online: Buscando dados da API pública.")
        else: # Offline
            self.status_icon_label.setPixmap(icon_manager.get_icon("database").pixmap(60, 60))
            self.status_icon_label.setToolTip("Modo Offline: Usando dados salvos localmente.")

    def update_clear_button_icon(self, mode):
        """Atualiza o ícone do botão de limpar com base no modo."""
        if mode == "Online":
            self.clear_button.setIcon(icon_manager.get_icon("link"))
            self.clear_button.setToolTip("Limpar Tabela (Modo Online)")
        else: # Offline
            self.clear_button.setIcon(icon_manager.get_icon("database"))
            self.clear_button.setToolTip("Limpar Tabela (Modo Offline)")

    def populate_preview_table(self, data):
        """Delega a população da tabela para a função importada."""
        populate_preview_table(self.preview_model, data)
        # Ajusta as colunas após popular
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
