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
        
        # Layout para a barra de pesquisa e o botão de atualizar
        preview_toolbar_layout = QHBoxLayout()
        self.preview_search_container = QVBoxLayout()
        preview_toolbar_layout.addLayout(self.preview_search_container, 1)

        # --- NOVO BOTÃO DE ATUALIZAR ---
        self.refresh_preview_button = QPushButton(" Atualizar")
        self.refresh_preview_button.setIcon(icon_manager.get_icon("refresh"))
        preview_toolbar_layout.addWidget(self.refresh_preview_button)
        # --- FIM DA ADIÇÃO ---
        
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
        preview_layout.addLayout(preview_toolbar_layout) # Adiciona o layout com o botão
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

        self.dados_button = QPushButton(" Dados")
        self.dados_button.setIcon(icon_manager.get_icon("database"))
        self.dados_menu = QMenu(self)
        self.import_action = self.dados_menu.addAction(icon_manager.get_icon("importar"), "Importar Planilha")
        self.export_completo_action = self.dados_menu.addAction(icon_manager.get_icon("excel_down"), "Exportar Tabela Completa")
        self.dados_menu.addSeparator()
        self.template_vazio_action = self.dados_menu.addAction(icon_manager.get_icon("excel"), "Gerar Tabela Vazia")
        self.export_para_importacao_action = self.dados_menu.addAction(icon_manager.get_icon("excel_up"), "Exportar para Re-importação")
        self.dados_button.setMenu(self.dados_menu)
        toolbar_layout.addWidget(self.dados_button)
        
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
