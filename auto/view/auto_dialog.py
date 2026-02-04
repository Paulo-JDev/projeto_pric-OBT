# auto/view/auto_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QPlainTextEdit, QFrame, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QSize
from utils.icon_loader import icon_manager
from datetime import datetime
from integration.view.trello_tab import TrelloTab

class AutoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Central de Automações")
        self.setWindowIcon(icon_manager.get_icon("automation"))
        self.setMinimumSize(800, 600)
        
        # Layout Principal da Janela
        self.main_layout = QVBoxLayout(self)
        
        # Cabeçalho Principal (Fica fixo acima das abas)
        self.header_title = QLabel("Automações do Sistema")
        self.header_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #8AB4F7;")
        self.main_layout.addWidget(self.header_title)

        # Widget de Abas
        self.tabs = QTabWidget()
        
        # --- Aba 1: Banco de Dados ---
        self.db_tab = QWidget()
        self.setup_db_tab() # Este método agora contém o layout da aba DB
        self.tabs.addTab(self.db_tab, "Banco de Dados")
        
        # --- Aba 2: Trello ---
        self.trello_tab = TrelloTab()
        self.tabs.addTab(self.trello_tab, "Integração Trello")
        
        self.main_layout.addWidget(self.tabs)

        # Rodapé com Botão Fechar (Fica fixo abaixo das abas)
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        self.close_button = QPushButton("Fechar")
        self.close_button.setFixedWidth(120)
        self.close_button.setMinimumHeight(35)
        self.close_button.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_button)
        self.main_layout.addLayout(footer_layout)

    def setup_db_tab(self):
        """Configura o layout específico da aba de Banco de Dados."""
        layout = QVBoxLayout(self.db_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grupo da Automação de DB
        self.db_group = QFrame()
        self.db_group.setObjectName("automation_frame")
        self.db_group.setStyleSheet("""
            #automation_frame {
                border: 1px solid #3d3d3d;
                border-radius: 10px;
            }
        """)
        db_layout = QVBoxLayout(self.db_group)
        
        title_layout = QHBoxLayout()
        db_icon = QLabel()
        db_icon.setPixmap(icon_manager.get_icon("database").pixmap(24, 24))
        title_layout.addWidget(db_icon)
        
        db_title = QLabel("Atualização de Base Offline (Preservando Dados)")
        db_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #ffffff;")
        title_layout.addWidget(db_title)
        title_layout.addStretch()
        db_layout.addLayout(title_layout)
        
        db_desc = QLabel(
            "Esta automação exporta seus Status e Contratos Manuais, substitui o arquivo "
            "de banco de dados (.db) e restaura tudo automaticamente para a nova base."
        )
        db_desc.setWordWrap(True)
        db_desc.setStyleSheet("color: #bbbbbb;")
        db_layout.addWidget(db_desc)
        
        self.btn_start_db_auto = QPushButton(" Iniciar Automação de Banco de Dados")
        self.btn_start_db_auto.setIcon(icon_manager.get_icon("automation"))
        self.btn_start_db_auto.setIconSize(QSize(24, 24))
        self.btn_start_db_auto.setMinimumHeight(50)
        self.btn_start_db_auto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start_db_auto.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #1e1e1e;
                border: 2px solid #8AB4F7;
                color: #8AB4F7;
            }
            QPushButton:hover {
                background-color: #8AB4F7;
                color: #1e1e1e;
            }
        """)
        db_layout.addWidget(self.btn_start_db_auto)
        layout.addWidget(self.db_group)

        # Área de Log
        log_label = QLabel("Progresso da Automação:")
        log_label.setStyleSheet("font-weight: bold; color: #8AB4F7;")
        layout.addWidget(log_label)

        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("Aguardando início do processo...")
        self.log_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #181818;
                color: #00FF41;
                font-family: 'Consolas', 'Monospace';
                font-size: 13px;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_edit)

    def log(self, message):
        """Adiciona uma linha de log com timestamp na interface."""
        now = datetime.now().strftime("%H:%M:%S")
        self.log_edit.appendPlainText(f"[{now}] > {message}")
        self.log_edit.verticalScrollBar().setValue(
            self.log_edit.verticalScrollBar().maximum()
        )

    def clear_log(self):
        self.log_edit.clear()

    def set_loading_state(self, is_loading):
        self.btn_start_db_auto.setEnabled(not is_loading)
        self.close_button.setEnabled(not is_loading)
        if is_loading:
            self.btn_start_db_auto.setText(" Processando Automação...")
        else:
            self.btn_start_db_auto.setText(" Iniciar Automação de Banco de Dados")
