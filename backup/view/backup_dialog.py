from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy,
    QLineEdit
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class BackupDialog(QDialog):
    """
    Janela de diálogo para gerenciar backups locais e online.
    Atualizado para ter checkboxes globais.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Backup do Sistema")
        self.setWindowIcon(icon_manager.get_icon("database"))
        self.setMinimumSize(600, 450) # Aumentei ligeiramente a altura
        self.setStyleSheet(parent.styleSheet() if parent else "")

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Seção 1: Seleção de Módulos (AGORA É GLOBAL) ---
        filter_group = QFrame()
        filter_group.setFrameShape(QFrame.Shape.StyledPanel)
        filter_group.setStyleSheet("QFrame { border: 1px solid #444; border-radius: 5px; padding: 10px; }")
        filter_layout = QVBoxLayout(filter_group)
        
        filter_title = QLabel("<b>Módulos para Backup:</b>")
        filter_title.setStyleSheet("border: none; padding: 0;")
        filter_layout.addWidget(filter_title)
        
        self.check_contratos = QCheckBox("Backup do Módulo de Contratos")
        self.check_contratos.setChecked(True)
        self.check_contratos.setStyleSheet("border: none; padding: 0;")
        filter_layout.addWidget(self.check_contratos)
        
        self.check_atas = QCheckBox("Backup do Módulo de Atas")
        self.check_atas.setChecked(True)
        self.check_atas.setStyleSheet("border: none; padding: 0;")
        filter_layout.addWidget(self.check_atas)
        
        main_layout.addWidget(filter_group) # Adiciona ao layout principal
        
        # --- Seção 2: Abas de Tipo de Backup ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        local_tab = self.create_local_backup_tab()
        online_tab = self.create_online_backup_tab()

        self.tabs.addTab(local_tab, "Backup Local")
        self.tabs.addTab(online_tab, "Backup Online")

    def create_local_backup_tab(self):
        """Cria o conteúdo da aba de Backup Local."""
        local_tab_widget = QWidget()
        layout = QVBoxLayout(local_tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 20, 10, 10) # Margem superior

        # --- Seção 1: Seleção de Local ---
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
        path_select_layout.addWidget(self.path_label, 1)
        
        path_layout.addLayout(path_select_layout)
        layout.addWidget(path_group)

        layout.addStretch()

        # --- Seção 2: Botões de Ação ---
        button_layout = QHBoxLayout()
        
        self.btn_abrir_local = QPushButton("Abrir Local")
        self.btn_abrir_local.setToolTip("Abrir a pasta de backup selecionada")
        self.btn_abrir_local.setIcon(icon_manager.get_icon("folder128"))
        button_layout.addWidget(self.btn_abrir_local)
        
        button_layout.addStretch()
        
        self.btn_disparar_backup = QPushButton("Disparar Backup Local")
        self.btn_disparar_backup.setIcon(icon_manager.get_icon("save"))
        self.btn_disparar_backup.setStyleSheet("font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.btn_disparar_backup)
        
        layout.addLayout(button_layout)
        
        return local_tab_widget

    def create_online_backup_tab(self):
        """Cria a aba de Backup Online (E-mail)."""
        online_tab_widget = QWidget()
        layout = QVBoxLayout(online_tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 20, 10, 10)

        # --- Seção 1: Destinatário ---
        email_group = QFrame()
        email_layout = QVBoxLayout(email_group)
        email_layout.addWidget(QLabel("<b>Destinatário do E-mail:</b>"))

        email_select_layout = QHBoxLayout()
        self.btn_definir_email = QPushButton("Definir/Alterar Email")
        self.btn_definir_email.setIcon(icon_manager.get_icon("edit"))
        email_select_layout.addWidget(self.btn_definir_email)
        
        self.email_label = QLabel("Nenhum e-mail definido.")
        self.email_label.setStyleSheet("color: #aaa; font-style: italic;")
        self.email_label.setWordWrap(True)
        email_select_layout.addWidget(self.email_label, 1)
        
        email_layout.addLayout(email_select_layout)
        layout.addWidget(email_group)

        # --- Seção 2: Aviso ---
        aviso_label = QLabel(
            "⚠️ **Aviso:** O backup online é enviado por e-mail e "
            "possui um limite de ~25MB. Se os seus bancos de dados "
            "forem maiores, o envio falhará. Use o Backup Local neste caso."
        )
        aviso_label.setWordWrap(True)
        aviso_label.setStyleSheet(
            "color: #FFA500; background-color: #2a2a2a; "
            "border: 1px solid #555; border-radius: 5px; padding: 10px;"
        )
        layout.addWidget(aviso_label)

        layout.addStretch()

        # --- Seção 3: Botão de Ação ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_disparar_backup_online = QPushButton("Disparar Backup Online")
        self.btn_disparar_backup_online.setIcon(icon_manager.get_icon("icon_send")) # Ícone de envio
        self.btn_disparar_backup_online.setStyleSheet("font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.btn_disparar_backup_online)
        
        layout.addLayout(button_layout)
        
        return online_tab_widget
