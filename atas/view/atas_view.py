# atas/view/atas_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, 
                             QPushButton, QLineEdit, QHeaderView, QMenu)
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
        
        # Cria o menu que ficará associado ao botão
        self.dados_menu = QMenu(self)
        self.import_action = self.dados_menu.addAction(icon_manager.get_icon("importar"), "Importar Planilha")
        self.export_completo_action = self.dados_menu.addAction(icon_manager.get_icon("excel_down"), "Exportar Tabela Completa")
        self.dados_menu.addSeparator()
        self.template_vazio_action = self.dados_menu.addAction(icon_manager.get_icon("excel"), "Gerar Tabela Vazia")
        self.export_para_importacao_action = self.dados_menu.addAction(icon_manager.get_icon("excel_up"), "Exportar para Re-importação")

        self.dados_button.setMenu(self.dados_menu)
        toolbar_layout.addWidget(self.dados_button)
        
        main_layout.addLayout(toolbar_layout)

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
        
        # --- LIGAÇÃO DO SINAL DE DUPLO CLIQUE ---
        # A lógica será tratada pelo controller
        # self.table_view.doubleClicked.connect(self.on_double_click) 

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        icons = {"magnifying-glass": icon_manager.get_icon("find")}
        self.search_bar = setup_search_bar(icons, self.search_layout_container, self.proxy_model, self.table_view)

        main_layout.addWidget(self.table_view)

    # O método 'show_context_menu' foi movido para o controller
    # para manter a View mais limpa