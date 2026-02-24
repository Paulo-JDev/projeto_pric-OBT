# view/preview_table.py
from PyQt6.QtWidgets import QTableView, QHeaderView, QLabel, QVBoxLayout, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from datetime import datetime, date
from utils.utils import MultiColumnFilterProxyModel
from utils.icon_loader import icon_manager

def _get_status_style(status_text):
    """Retorna a cor e a fonte para um determinado status."""
    status_styles = {
        "SEÇÃO CONTRATOS": (QColor("#FFFFFF"), QFont.Weight.Bold),
        "PORTARIA": (QColor(230, 230, 150), QFont.Weight.Bold),
        "EMPRESA": (QColor(230, 230, 150), QFont.Weight.Bold),
        "SIGDEM": (QColor(230, 180, 100), QFont.Weight.Bold),
        "ASSINADO": (QColor(230, 180, 100), QFont.Weight.Bold),
        "PUBLICADO": (QColor(135, 206, 250), QFont.Weight.Bold),
        "ALERTA PRAZO": (QColor(255, 160, 160), QFont.Weight.Bold),
        "NOTA TÉCNICA": (QColor(255, 160, 160), QFont.Weight.Bold),
        "AGU": (QColor(255, 160, 160), QFont.Weight.Bold),
        "PRORROGADO": (QColor(135, 206, 250), QFont.Weight.Bold),
        "SIGAD" : (QColor(230, 180, 100), QFont.Weight.Bold)
    }
    return status_styles.get(status_text, (QColor("#FFFFFF"), QFont.Weight.Normal))

def _create_centered_item(text):
    """Cria um QStandardItem com o texto centralizado."""
    item = QStandardItem(str(text))
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return item

def _create_preview_dias_item(dias_restantes_valor):
    """Cria e formata um QStandardItem para a coluna 'Dias' da pré-visualização."""
    dias_item = _create_centered_item(str(dias_restantes_valor))
    font = dias_item.font()
    font.setBold(True)
    dias_item.setFont(font)

    if isinstance(dias_restantes_valor, int):
        if dias_restantes_valor < 0:
            dias_item.setForeground(Qt.GlobalColor.red)
            dias_item.setIcon(icon_manager.get_icon("delete"))
        elif dias_restantes_valor <= 89:
            dias_item.setForeground(QBrush(QColor("#FFA500")))  # Laranja
            dias_item.setIcon(icon_manager.get_icon("alert"))
        elif dias_restantes_valor <= 179:
            dias_item.setForeground(QBrush(QColor("#FFD700")))  # Amarelo
            dias_item.setIcon(icon_manager.get_icon("mensagem"))
        else:
            dias_item.setForeground(QBrush(QColor("#32CD32")))  # Verde
            dias_item.setIcon(icon_manager.get_icon("aproved"))
    else:  # "Sem Data" ou "Erro Data"
        dias_item.setForeground(QBrush(QColor("#AAAAAA")))
        dias_item.setIcon(icon_manager.get_icon("time"))
    return dias_item

def create_preview_table_widget(controller):
    """Cria o widget completo da tabela de pré-visualização."""
    right_frame = QFrame()
    right_layout = QVBoxLayout(right_frame)

    right_layout.addWidget(QLabel("<b>Contratos em andamento</b>"))

    # Layout para os botões de ação
    button_layout = QHBoxLayout()
    
    refresh_button = QPushButton("Atualizar Pré-visualização")
    refresh_button.setIcon(icon_manager.get_icon("refresh"))
    refresh_button.clicked.connect(controller.populate_previsualization_table)
    button_layout.addWidget(refresh_button)

    # --- NOVO BOTÃO PARA AJUSTAR COLUNAS ---
    resize_button = QPushButton("Ajustar Colunas")
    resize_button.setIcon(icon_manager.get_icon("stats")) 
    button_layout.addWidget(resize_button)

    right_layout.addLayout(button_layout)

    preview_table = QTableView()
    preview_model = QStandardItemModel()
    preview_proxy_model = MultiColumnFilterProxyModel()
    preview_proxy_model.setSourceModel(preview_model)
    preview_table.setModel(preview_proxy_model)

    preview_table.verticalHeader().setVisible(False)
    preview_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
    preview_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
    preview_table.clicked.connect(controller.show_records_popup)

    # --- LÓGICA DE REDIMENSIONAMENTO MOVIDA PARA O BOTÃO ---
    def adjust_columns():
        """Define os modos de redimensionamento e os tamanhos das colunas."""
        header = preview_table.horizontalHeader()
        
        # Define um tamanho mínimo global para todas as colunas, para que não desapareçam
        header.setMinimumSectionSize(80)
        header.setMaximumSectionSize(250)

        # Define o modo de redimensionamento para interativo (o usuário pode ajustar)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Define larguras iniciais para colunas específicas
        header.resizeSection(0, 80)    # Coluna "UASG"
        header.resizeSection(1, 80)    # Coluna "Dias"
        header.resizeSection(2, 110)   # Coluna "Contrato/Ata"
        header.resizeSection(3, 160)   # Coluna "Processo"
        
        # Permite que as colunas de Fornecedor e Status se estiquem para preencher o espaço
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Fornecedor
        header.resizeSection(5, 250) # Status

    resize_button.clicked.connect(adjust_columns)

    right_layout.addWidget(preview_table)
    return right_frame, preview_table, preview_model

def populate_preview_table(preview_model, data):
    """Popula a tabela de pré-visualização com dados filtrados, ordenados e formatados."""
    preview_model.clear()
    preview_model.setHorizontalHeaderLabels(["UASG", "Dias", "Contrato/Ata", "NUP", "Fornecedor", "Status"])

    active, expired, no_date = [], [], []
    for row_data in data:
        vigencia_fim_str = row_data.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - date.today()).days
                row_data['dias_restantes'] = dias_restantes
                if dias_restantes < 0:
                    expired.append(row_data)
                else:
                    active.append(row_data)
            except ValueError:
                row_data['dias_restantes'] = "Erro Data"
                no_date.append(row_data)
        else:
            row_data['dias_restantes'] = "Sem Data"
            no_date.append(row_data)

    active.sort(key=lambda x: x['dias_restantes'])
    expired.sort(key=lambda x: x['dias_restantes'], reverse=True)
    
    sorted_data = active + expired + no_date

    for row_data in sorted_data:
        dias_item = _create_preview_dias_item(row_data['dias_restantes'])
        
        # --- LÓGICA DAS CORES DO STATUS ADICIONADA AQUI ---
        status_text = str(row_data.get("status", "N/A"))
        status_item = _create_centered_item(status_text)
        color, weight = _get_status_style(status_text)
        status_item.setForeground(QBrush(color))
        font = status_item.font()
        font.setWeight(weight)
        status_item.setFont(font)
        
        uasg_item = _create_centered_item(row_data.get("uasg_code", "N/A"))
        contrato_id = row_data.get("id")
        if contrato_id:
            # Guarda o ID no item sem exibi-lo na tela
            uasg_item.setData(contrato_id, Qt.ItemDataRole.UserRole)

        row_items = [
            uasg_item,
            dias_item,
            _create_centered_item(row_data.get("numero", "N/A")),
            _create_centered_item(row_data.get("processo", "N/A")),
            _create_centered_item(row_data.get("fornecedor_nome", "N/A")),
            status_item
        ]
        preview_model.appendRow(row_items)