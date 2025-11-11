from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class BackupDialog(QDialog):
    """
    Janela de diálogo para gerenciar backups locais e online.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Backup do Sistema")
        self.setWindowIcon(icon_manager.get_icon("database")) # Ícone sugestivo
        self.setMinimumSize(600, 400)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Criar as abas
        local_tab = self.create_local_backup_tab()
        online_tab = self.create_online_backup_tab()

        self.tabs.addTab(local_tab, "Backup Local")
        self.tabs.addTab(online_tab, "Backup Online")

    def create_local_backup_tab(self):
        """Cria o conteúdo da aba de Backup Local."""
        local_tab_widget = QWidget()
        layout = QVBoxLayout(local_tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Seção 1: Seleção de Módulos ---
        filter_group = QFrame()
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.addWidget(QLabel("<b>Módulos para Backup:</b>"))
        
        self.check_contratos = QCheckBox("Backup do Módulo de Contratos")
        self.check_contratos.setChecked(True)
        filter_layout.addWidget(self.check_contratos)
        
        self.check_atas = QCheckBox("Backup do Módulo de Atas")
        self.check_atas.setChecked(True)
        filter_layout.addWidget(self.check_atas)
        
        layout.addWidget(filter_group)

        # --- Seção 2: Seleção de Local ---
        path_group = QFrame()
        path_layout = QVBoxLayout(path_group)
        path_layout.addWidget(QLabel("<b>Local de Destino:</b>"))
        
        path_select_layout = QHBoxLayout()
        self.select_path_button = QPushButton("Selecionar Pasta")
        self.select_path_button.setIcon(icon_manager.get_icon("open-folder"))
        path_select_layout.addWidget(self.select_path_button)
        
        self.path_label = QLabel("Nenhum local selecionado.")
        self.path_label.setStyleSheet("color: #aaa; font-style: italic;")
        self.path_label.setWordWrap(True)
        path_select_layout.addWidget(self.path_label, 1) # O '1' permite que o label expanda
        
        path_layout.addLayout(path_select_layout)
        layout.addWidget(path_group)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # --- Seção 3: Botões de Ação ---
        button_layout = QHBoxLayout()
        
        # Botão Dica: Abrir Local
        self.btn_abrir_local = QPushButton("Abrir Local")
        self.btn_abrir_local.setToolTip("Abrir a pasta de backup selecionada")
        self.btn_abrir_local.setIcon(icon_manager.get_icon("folder128")) # Ícone sugestivo
        button_layout.addWidget(self.btn_abrir_local)
        
        button_layout.addStretch()
        
        # Botão Principal: Disparar Backup
        self.btn_disparar_backup = QPushButton("Disparar Backup")
        self.btn_disparar_backup.setIcon(icon_manager.get_icon("save")) # Ícone de salvar
        self.btn_disparar_backup.setStyleSheet("font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.btn_disparar_backup)
        
        layout.addLayout(button_layout)
        
        return local_tab_widget

    def create_online_backup_tab(self):
        """Cria a aba de Backup Online (placeholder)."""
        online_tab_widget = QWidget()
        layout = QVBoxLayout(online_tab_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel("Backup Online (Em Desenvolvimento)")
        label.setStyleSheet("font-size: 16px; color: #888;")
        
        layout.addWidget(label)
        return online_tab_widget
