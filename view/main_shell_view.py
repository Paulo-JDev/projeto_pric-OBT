# view/main_shell_view.py

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QListWidgetItem, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QSize # Adicione a importação de QSize
from PyQt6.QtGui import QIcon
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager
import os


class MainShellView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contratos360 - Gestão Integrada")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1024, 600)
        self.set_window_icon()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- NAVEGAÇÃO LATERAL MODIFICADA ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(70)  # Largura reduzida
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(40, 40)) # Ícones maiores
        self.main_layout.addWidget(self.nav_list)

        home_menu = QListWidgetItem(icon_manager.get_icon("dash"), "") # Texto vazio
        home_menu.setToolTip("Home")  # Dica de ferramenta
        self.nav_list.addItem(home_menu)

        # Adiciona os itens de navegação sem texto e com tooltips
        item_contratos = QListWidgetItem(icon_manager.get_icon("contratos"), "") # Texto vazio
        item_contratos.setToolTip("Contratos")  # Dica de ferramenta
        self.nav_list.addItem(item_contratos)

        item_atas = QListWidgetItem(icon_manager.get_icon("atas"), "") # Texto vazio
        item_atas.setToolTip("Atas")  # Dica de ferramenta
        self.nav_list.addItem(item_atas)

        """item_relatorios = QListWidgetItem(icon_manager.get_icon("edit"), "") # Texto vazio
        item_relatorios.setToolTip("Relatórios")  # Dica de ferramenta
        self.nav_list.addItem(item_relatorios)

        item_configuracoes = QListWidgetItem(icon_manager.get_icon("configuracoes"), "") # Texto vazio
        item_configuracoes.setToolTip("Configurações")  # Dica de ferramenta
        self.nav_list.addItem(item_configuracoes)

        item_sobre = QListWidgetItem(icon_manager.get_icon("sobre"), "") # Texto vazio
        item_sobre.setToolTip("Sobre")  # Dica de ferramenta
        self.nav_list.addItem(item_sobre)"""
        # --- FIM DAS MODIFICAÇÕES ---

        # 2. Área de Conteúdo Principal (empilhada)
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Tela de Boas-Vindas
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_label = QLabel(
            "Aplicativo para Controle de Contratos e Atas,\n"
            "com funcionalidades de produtividade e Organização\n"
            "com mudanças e atualizações"
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setObjectName("WelcomeLabel")
        welcome_layout.addWidget(welcome_label)
        self.stacked_widget.addWidget(welcome_widget)

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        # Caminho do ícone na pasta original
        icon_path = resource_path("utils/icons/mn.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")