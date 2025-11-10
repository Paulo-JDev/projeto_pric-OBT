# atas/view/atas_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, 
                             QPushButton, QLineEdit, QHeaderView, QTabWidget, QMenu)
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager
from utils.utils import MultiColumnFilterProxyModel, setup_search_bar

class AtasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        title_label = QLabel("Gestão de Atas Administrativas")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #8AB4F7;")
        main_layout.addWidget(title_label)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Aba 1: Tabela de Pré-visualização ---
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        preview_toolbar_layout = QHBoxLayout()
        self.preview_search_container = QVBoxLayout()
        preview_toolbar_layout.addLayout(self.preview_search_container, 1)

        self.refresh_preview_button = QPushButton(" Atualizar")
        self.refresh_preview_button.setIcon(icon_manager.get_icon("refresh"))
        preview_toolbar_layout.addWidget(self.refresh_preview_button)

        self.preview_table = QTableView()
        self.preview_table.setStyleSheet("QTableView::item:selected { background-color: rgba(163, 213, 255, 0.4); }")
        self.preview_model = QStandardItemModel()
        self.preview_proxy_model = MultiColumnFilterProxyModel()
        self.preview_proxy_model.setSourceModel(self.preview_model)
        self.preview_table.setModel(self.preview_proxy_model)
        self.preview_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_search_bar = setup_search_bar(
            {"magnifying-glass": icon_manager.get_icon("find")}, 
            self.preview_search_container, self.preview_proxy_model, self.preview_table
        )
        preview_layout.addLayout(preview_toolbar_layout)
        preview_layout.addWidget(self.preview_table)
        self.tabs.addTab(self.preview_tab, "Tabela de Pré-Visualização")

        # --- Aba 2: Tabela Principal ---
        self.main_table_tab = QWidget()
        table_layout = QVBoxLayout(self.main_table_tab)
        toolbar_layout = QHBoxLayout()
        self.search_layout_container = QVBoxLayout()
        toolbar_layout.addLayout(self.search_layout_container, 1)

        self.add_button = QPushButton(" Adicionar")
        self.add_button.setIcon(icon_manager.get_icon("plus"))
        toolbar_layout.addWidget(self.add_button)

        self.delete_button = QPushButton(" Excluir")
        self.delete_button.setIcon(icon_manager.get_icon("delete"))
        toolbar_layout.addWidget(self.delete_button)

        # ✨ BOTÃO "PLANILHA" (antigo "Dados") ✨
        self.planilha_button = QPushButton(" Planilha")
        self.planilha_button.setIcon(icon_manager.get_icon("excel")) # Ícone mais genérico para planilha
        self.planilha_menu = QMenu(self)
        self.import_action = self.planilha_menu.addAction(icon_manager.get_icon("importar"), "Importar Planilha")
        self.export_completo_action = self.planilha_menu.addAction(icon_manager.get_icon("excel_down"), "Exportar Tabela Completa")
        self.planilha_menu.addSeparator()
        self.template_vazio_action = self.planilha_menu.addAction(icon_manager.get_icon("excel"), "Gerar Tabela Vazia")
        self.export_para_importacao_action = self.planilha_menu.addAction(icon_manager.get_icon("excel_up"), "Exportar para Re-importação")
        self.planilha_button.setMenu(self.planilha_menu)
        toolbar_layout.addWidget(self.planilha_button)

        # ✨ NOVO BOTÃO "DB" ✨
        self.db_button = QPushButton(" DB")
        self.db_button.setIcon(icon_manager.get_icon("database"))
        self.db_menu = QMenu(self)
        self.change_db_location_action = self.db_menu.addAction(icon_manager.get_icon("folder"), "Mudar Local do DB")
        self.db_menu.addSeparator()
        self.export_main_json_action = self.db_menu.addAction(icon_manager.get_icon("json_export"), "Exportar Dados Principais (JSON)")
        self.import_main_json_action = self.db_menu.addAction(icon_manager.get_icon("json_import"), "Importar Dados Principais (JSON)")
        self.db_menu.addSeparator()
        self.export_complementary_json_action = self.db_menu.addAction(icon_manager.get_icon("json_export_extra"), "Exportar Dados Complementares (JSON)")
        self.import_complementary_json_action = self.db_menu.addAction(icon_manager.get_icon("json_import_extra"), "Importar Dados Complementares (JSON)")
        self.db_button.setMenu(self.db_menu)
        toolbar_layout.addWidget(self.db_button)

        self.refresh_table_button = QPushButton(" Atualizar")
        self.refresh_table_button.setIcon(icon_manager.get_icon("refresh"))
        toolbar_layout.addWidget(self.refresh_table_button)

        table_layout.addLayout(toolbar_layout)
        self.table_view = QTableView()
        self.table_view.setStyleSheet("QTableView::item:selected { background-color: rgba(163, 213, 255, 0.4); }")
        self.table_model = QStandardItemModel()
        self.proxy_model = MultiColumnFilterProxyModel()
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_bar = setup_search_bar(
            {"magnifying-glass": icon_manager.get_icon("find")}, 
            self.search_layout_container, self.proxy_model, self.table_view
        )
        table_layout.addWidget(self.table_view)
        self.tabs.addTab(self.main_table_tab, "Tabela Principal")
