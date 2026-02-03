# view/main_shell_view.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, 
    QListWidgetItem, QLabel, QVBoxLayout, QGridLayout, QPushButton # Adicionado QPushButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager
import os
# Importe o novo InfoDialog (não é estritamente necessário aqui, mas bom para referência)
# from view.info_dialog import InfoDialog

class MainShellView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CA 360 - Interface Principal")
        self.setWindowIcon(icon_manager.got_ico("mn"))
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1024, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- NAVEGAÇÃO LATERAL (Sem alterações) ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(70)
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(40, 40))
        self.main_layout.addWidget(self.nav_list)

        home_menu = QListWidgetItem(icon_manager.get_icon("dash"), "")
        home_menu.setToolTip("Home")
        self.nav_list.addItem(home_menu)

        item_contratos = QListWidgetItem(icon_manager.get_icon("contrato"), "")
        item_contratos.setToolTip("Contratos")
        self.nav_list.addItem(item_contratos)

        item_atas = QListWidgetItem(icon_manager.get_icon("atas"), "")
        item_atas.setToolTip("Atas")
        self.nav_list.addItem(item_atas)
        
        # --- ÁREA DE CONTEÚDO PRINCIPAL ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- TELA DE BOAS-VINDAS (REFEITA) ---
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centraliza o conteúdo
        welcome_layout.setSpacing(20)

        # Botão 1: Informações
        self.info_button = QPushButton(" Informações do Projeto")
        self.info_button.setIcon(icon_manager.get_icon("init")) # Ícone de Info
        self.info_button.setIconSize(QSize(32, 32))
        self.info_button.setFixedSize(300, 80)
        self.info_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        welcome_layout.addWidget(self.info_button)

        # Botão 2: Backup
        self.backup_button = QPushButton(" Backup do Sistema")
        self.backup_button.setIcon(icon_manager.get_icon("database")) # Ícone de DB/Backup
        self.backup_button.setIconSize(QSize(32, 32))
        self.backup_button.setFixedSize(300, 80)
        self.backup_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        welcome_layout.addWidget(self.backup_button)

        # Botão Automações
        self.automation_button = QPushButton(" Automações")
        self.automation_button.setIcon(icon_manager.get_icon("automation")) 
        self.automation_button.setIconSize(QSize(32, 32))
        self.automation_button.setFixedSize(300, 80)
        self.automation_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        welcome_layout.addWidget(self.automation_button)

        # Botão de Ajuda
        self.help_button = QPushButton(" Ajuda e Suporte")
        self.help_button.setIcon(icon_manager.get_icon("ajuda_more")) # Ícone de Ajuda
        self.help_button.setIconSize(QSize(32, 32))
        self.help_button.setFixedSize(300, 80)
        self.help_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        welcome_layout.addWidget(self.help_button)
        
        self.stacked_widget.addWidget(welcome_widget)
        # --- FIM DA TELA DE BOAS-VINDAS (REFEITA) ---

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        icon_path = resource_path("utils/icons/mn.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")
