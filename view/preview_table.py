# view/preview_table.py
from PyQt6.QtWidgets import QTableView, QHeaderView, QLabel, QVBoxLayout, QFrame, QPushButton
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
from datetime import datetime, date
from utils.utils import MultiColumnFilterProxyModel
from utils.icon_loader import icon_manager

def create_preview_table_widget(controller):
    """Cria o widget completo da tabela de pré-visualização."""
    right_frame = QFrame()
    right_layout = QVBoxLayout(right_frame)

    right_layout.addWidget(QLabel("<b>Contratos em andamento</b>"))

    # Botão de atualização
    refresh_button = QPushButton("Atualizar Pré-visualização")
    refresh_button.setIcon(icon_manager.get_icon("refresh"))
    refresh_button.clicked.connect(controller.populate_previsualization_table)
    right_layout.addWidget(refresh_button)

    # Configuração da Tabela
    preview_table = QTableView()
    preview_model = QStandardItemModel()
    preview_proxy_model = MultiColumnFilterProxyModel()
    preview_proxy_model.setSourceModel(preview_model)
    preview_table.setModel(preview_proxy_model)

    preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    preview_table.verticalHeader().setVisible(False)
    preview_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
    preview_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    right_layout.addWidget(preview_table)

    # Retorna os objetos que precisam ser acessados externamente
    return right_frame, preview_table, preview_model

def populate_preview_table(preview_model, data):
    """Popula a tabela de pré-visualização com dados filtrados."""
    preview_model.clear()
    preview_model.setHorizontalHeaderLabels(["UASG", "Dias", "Contrato/Ata", "Processo", "Fornecedor", "Status"])

    for row_data in data:
        row_items = []

        # 1. UASG
        uasg_code = row_data.get("uasg_code", "N/A")
        row_items.append(QStandardItem(str(uasg_code)))

        # 2. Dias
        vigencia_fim_str = row_data.get("vigencia_fim", "")
        dias_restantes = "Sem Data"
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - date.today()).days
            except ValueError:
                dias_restantes = "Erro Data"
        dias_item = QStandardItem(str(dias_restantes))
        row_items.append(dias_item)

        # 3. Contrato/Ata
        contrato_numero = row_data.get("numero", "N/A")
        row_items.append(QStandardItem(str(contrato_numero)))

        # 4. Processo
        processo_numero = row_data.get("processo", "N/A")
        row_items.append(QStandardItem(str(processo_numero)))

        # 5. Fornecedor
        fornecedor_nome = row_data.get("fornecedor_nome", "N/A")
        row_items.append(QStandardItem(str(fornecedor_nome)))

        # 6. Status
        status_text = row_data.get("status", "N/A")
        row_items.append(QStandardItem(str(status_text)))

        preview_model.appendRow(row_items)