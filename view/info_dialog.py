from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, 
    QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class InfoDialog(QDialog):
    """
    Janela pop-up que exibe as informações "Sobre" o projeto.
    O conteúdo foi movido da antiga tela de boas-vindas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Informações do Projeto")
        self.setWindowIcon(icon_manager.get_icon("init")) # Ícone de "info"
        self.setMinimumSize(700, 500)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        # Layout principal da janela
        welcome_layout = QVBoxLayout(self)
        welcome_layout.setContentsMargins(50, 30, 50, 30)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- CONTEÚDO MOVIDO DE main_shell_view.py ---
        title_label = QLabel("CA 360")
        title_label.setObjectName("WelcomeTitle")
        title_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #8AB4F7; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel(
            "CA 360 é um projeto em desenvolvimento para automatizar processos repetitivos relacionados a licitações e acordos administrativos. "
            "Com um foco na otimização e eficiência, o projeto oferece ferramentas para manipulação de documentos PDF, DOCX e XLSX, geração de "
            "relatórios, e automação de tarefas via RPA. O objetivo principal é melhorar a qualidade de vida no trabalho, minimizando erros e reduzindo a "
            "quantidade de cliques necessários para completar uma tarefa."
        )
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 14px; color: #ccc; margin-bottom: 40px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(subtitle_label)

        features_grid = QGridLayout()
        features_grid.setSpacing(25)

        def create_feature_widget(icon_name, title, description):
            widget = QWidget()
            row_layout = QHBoxLayout(widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(20)

            icon_label = QLabel()
            icon_label.setPixmap(icon_manager.get_icon(icon_name).pixmap(48, 48))
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
            row_layout.addStretch()
            return widget

        features_grid.addWidget(create_feature_widget("atas", "Atas", "Automação para criação de Atas de Registro de Preços."), 0, 0)
        features_grid.addWidget(create_feature_widget("contratos", "Contratos", "Gerenciamento de contratos administrativos."), 1, 0)
        features_grid.addWidget(create_feature_widget("sapiens", "Web Scraping", "Coleta automática de dados do Comprasnet."), 2, 0)
        features_grid.addWidget(create_feature_widget("api", "API PNCP e ComprasnetContratos", "Consulta de dados do PNCP e ComprasnetContratos via API."), 3, 0)
        
        welcome_layout.addLayout(features_grid)
        welcome_layout.addStretch()

        footer_label = QLabel('Para mais informações, entre em contato pelo e-mail: <a href="mailto:obtencaoceimbra@gmail.com" ' \
        'style="color: #4A9EFF; text-decoration: none;">obtencaoceimbra@gmail.com</a>')
        footer_label.setStyleSheet("font-size: 12px; color: #ccc; margin-top: 20px;")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setOpenExternalLinks(True)  # Permite abrir o link
        footer_label.setTextFormat(Qt.TextFormat.RichText)  # Habilita HTML
        welcome_layout.addWidget(footer_label)
        # --- FIM DO CONTEÚDO MOVIDO ---

        # Botão de Fechar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)
        
        welcome_layout.addLayout(button_layout)
