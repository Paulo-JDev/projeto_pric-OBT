# Contratos/view/settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(500, 400)
        
        self.main_layout = QVBoxLayout(self)
        
        # ==================== MODO DE OBTENÇÃO DE DADOS ====================
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Modo de Obtenção de Dados:")
        self.mode_button = QPushButton("Carregando...")
        self.mode_button.setCheckable(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_button)
        self.main_layout.addLayout(mode_layout)
        
        # ==================== ✅ LOCAL DO BANCO DE DADOS (DARK MODE) ====================
        db_path_group = QGroupBox("Local do Banco de Dados")
        db_path_layout = QVBoxLayout(db_path_group)
        
        # ✅ Label com estilo dark mode
        self.db_path_label = QLabel("Caminho Atual: Carregando...")
        self.db_path_label.setWordWrap(True)
        self.db_path_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #1e1e1e;
                color: #8AB4F7;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        db_path_layout.addWidget(self.db_path_label)
        
        # Botão para alterar o caminho
        self.change_db_path_button = QPushButton("Alterar Local...")
        self.change_db_path_button.setIcon(icon_manager.get_icon("open_icon"))
        self.change_db_path_button.setObjectName("header_button")  # ✅ Usa o estilo do tema
        db_path_layout.addWidget(self.change_db_path_button, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # ✅ Texto explicativo com estilo dark mode
        info_label = QLabel(
            "💡 <i>Alterar o local permite mover o banco de dados para outra pasta "
            "(ex: pen drive, rede). A configuração é salva automaticamente.</i>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                font-style: italic;
                padding: 5px;
            }
        """)
        db_path_layout.addWidget(info_label)
        
        self.main_layout.addWidget(db_path_group)
        
        # ==================== GERENCIAMENTO DO BANCO OFFLINE ====================
        offline_group = QGroupBox("Gerenciamento do Banco de Dados Offline")
        offline_layout = QVBoxLayout(offline_group)
        
        offline_label = QLabel("<b>Busca para uso OFFLINE:</b>")
        offline_layout.addWidget(offline_label)
        
        self.offline_uasg_input = QLineEdit()
        self.offline_uasg_input.setPlaceholderText("Digite a UASG para baixar ou deletar (Ex: 787010)")
        offline_layout.addWidget(self.offline_uasg_input)
        
        offline_buttons_layout = QHBoxLayout()
        
        self.create_db_button = QPushButton("Fazer DB")
        self.create_db_button.setIcon(icon_manager.get_icon("database"))
        self.create_db_button.setObjectName("header_button")  # ✅ Usa o estilo do tema
        
        self.delete_db_button = QPushButton("Excluir UASG")
        self.delete_db_button.setIcon(icon_manager.get_icon("delete"))
        self.delete_db_button.setObjectName("header_button")  # ✅ Usa o estilo do tema
        
        offline_buttons_layout.addWidget(self.create_db_button)
        offline_buttons_layout.addWidget(self.delete_db_button)
        offline_layout.addLayout(offline_buttons_layout)
        
        self.main_layout.addWidget(offline_group)
        
        # ==================== ESPAÇAMENTO E BOTÃO FECHAR ====================
        self.main_layout.addStretch()
        
        # Botão Fechar
        self.close_button = QPushButton("Fechar")
        self.close_button.setIcon(icon_manager.get_icon("close"))
        self.close_button.setObjectName("header_button")  # ✅ Usa o estilo do tema
        
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()
        close_button_layout.addWidget(self.close_button)
        self.main_layout.addLayout(close_button_layout)
