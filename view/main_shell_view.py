# view/main_shell_view.py

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QListWidgetItem, QLabel, QVBoxLayout, QGridLayout
from PyQt6.QtCore import Qt, QSize # Adicione a importação de QSize
from PyQt6.QtGui import QIcon
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager
import os

class MainShellView(QMainWindow):
    # (dentro da classe MainShellView, substitua o método __init__)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HASTA 360 - Gestão Integrada")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1024, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- NAVEGAÇÃO LATERAL ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(70)
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(40, 40))
        self.main_layout.addWidget(self.nav_list)

        home_menu = QListWidgetItem(icon_manager.get_icon("dash"), "")
        home_menu.setToolTip("Home")
        self.nav_list.addItem(home_menu)

        item_contratos = QListWidgetItem(icon_manager.get_icon("contratos"), "")
        item_contratos.setToolTip("Contratos")
        self.nav_list.addItem(item_contratos)

        item_atas = QListWidgetItem(icon_manager.get_icon("atas"), "")
        item_atas.setToolTip("Atas")
        self.nav_list.addItem(item_atas)
        
        # --- ÁREA DE CONTEÚDO PRINCIPAL ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- TELA DE BOAS-VINDAS (RECONSTRUÍDA E REFINADA) ---
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(50, 30, 50, 30)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("HASTA 360")
        title_label.setObjectName("WelcomeTitle")
        title_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #8AB4F7; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel(
            "HASTA 360 é um projeto em desenvolvimento para automatizar processos repetitivos relacionados a licitações e acordos administrativos. "
            "Com um foco na otimização e eficiência, o projeto oferece ferramentas para manipulação de documentos PDF, DOCX e XLSX, geração de "
            "relatórios, e automação de tarefas via RPA. O objetivo principal é melhorar a qualidade de vida no trabalho, minimizando erros e reduzindo a "
            "quantidade de cliques necessários para completar uma tarefa."
        )
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 14px; color: #ccc; margin-bottom: 40px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(subtitle_label)

        # --- ALTERAÇÕES NO LAYOUT DAS FUNCIONALIDADES ---
        features_grid = QGridLayout() # Usa um Grid para melhor alinhamento
        features_grid.setSpacing(25) # Espaçamento entre os itens

        # Função auxiliar para criar cada linha de funcionalidade
        def create_feature_widget(icon_name, title, description):
            widget = QWidget()
            row_layout = QHBoxLayout(widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(20) # Espaço entre ícone e texto

            icon_label = QLabel()
            icon_label.setPixmap(icon_manager.get_icon(icon_name).pixmap(48, 48)) # Ícone maior
            row_layout.addWidget(icon_label)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            title_label = QLabel(f"<b>{title}</b>")
            title_label.setStyleSheet("font-size: 16px;")
            description_label = QLabel(description)
            description_label.setStyleSheet("font-size: 13px; color: #aaa;")
            text_layout.addWidget(title_label)
            text_layout.addWidget(description_label)
            
            row_layout.addLayout(text_layout)
            row_layout.addStretch() # Empurra para a esquerda, mantendo o texto junto ao ícone
            return widget

        # Adiciona as funcionalidades ao grid
        features_grid.addWidget(create_feature_widget("atas", "Atas", "Automação para criação de Atas de Registro de Preços."), 0, 0)
        features_grid.addWidget(create_feature_widget("contratos", "Contratos", "Gerenciamento de contratos administrativos."), 1, 0)
        features_grid.addWidget(create_feature_widget("sapiens", "Web Scraping", "Coleta automática de dados do Comprasnet."), 2, 0)
        features_grid.addWidget(create_feature_widget("api", "API PNCP e ComprasnetContratos", "Consulta de dados do PNCP e ComprasnetContratos via API."), 3, 0)
        
        welcome_layout.addLayout(features_grid)
        welcome_layout.addStretch()
        # --- FIM DAS ALTERAÇÕES ---

        footer_label = QLabel("Para mais informações, entre em contato pelo e-mail: <b>obtencaoceimbra@gmail.com</b>")
        footer_label.setStyleSheet("font-size: 12px; color: #ccc; margin-top: 20px;")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(footer_label)
        
        self.stacked_widget.addWidget(welcome_widget)
        # --- FIM DA TELA DE BOAS-VINDAS ---

    def set_window_icon(self):
        """Define o ícone da janela a partir de um arquivo na pasta utils/icons."""
        # Caminho do ícone na pasta original
        icon_path = resource_path("utils/icons/mn.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"⚠ Arquivo de ícone não encontrado: {icon_path}")