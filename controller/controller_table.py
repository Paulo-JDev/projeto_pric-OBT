from PyQt6.QtWidgets import QHeaderView, QTableView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QFont, QColor, QBrush
from datetime import datetime, date
import sqlite3 # Adicionado para buscar status do DB
from utils.icon_loader import icon_manager

def populate_table(controller, data):
    """Preenche a tabela com os dados fornecidos, ordenando do maior para o menor tempo de vigência."""
    _populate_or_update_table(controller, data, repopulation=True)

def update_status_column(controller):
    """Atualiza apenas a coluna de status da tabela sem recarregar todos os dados."""
    if not controller.current_data:
        return
    _populate_or_update_table(controller, controller.current_data, repopulation=False)
    print("✅ Colunas de status e dias atualizadas.")

def _create_dias_item(dias_restantes_valor):
    """Cria e formata um QStandardItem para a coluna 'Dias'."""
    dias_item = QStandardItem(str(dias_restantes_valor))
    dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
    else: # "Sem Data" ou "Erro Data"
        dias_item.setForeground(QBrush(QColor("#AAAAAA")))
        dias_item.setIcon(icon_manager.get_icon("time"))
    return dias_item

def _get_status_style(status_text):
    """Retorna a cor e a fonte para um determinado status."""
    # Mapeamento de status para cores e fontes
    status_styles = {
        "SEÇÃO CONTRATOS": (Qt.GlobalColor.white, QFont.Weight.Bold),
        "ATA GERADA": (QColor(144, 238, 144), QFont.Weight.Bold), # Verde claro menos saturado
        "EMPRESA": (QColor(230, 230, 150), QFont.Weight.Bold),    # Amarelo menos saturado
        "SIGDEM": (QColor(230, 180, 100), QFont.Weight.Bold),   # Laranja menos saturado
        "ASSINADO": (QColor(144, 238, 144), QFont.Weight.Bold), # Verde claro
        "PUBLICADO": (QColor(135, 206, 250), QFont.Weight.Bold), # Azul claro
        "ALERTA PRAZO": (QColor(255, 160, 160), QFont.Weight.Bold), # Vermelho menos saturado
        "NOTA TÉCNICA": (QColor(230, 230, 150), QFont.Weight.Bold), # Amarelo menos saturado
        "AGU": (QColor(135, 206, 250), QFont.Weight.Bold),      # Azul claro
        "PRORROGADO": (QColor(144, 238, 144), QFont.Weight.Bold) # Verde claro
    }
    return status_styles.get(status_text, (Qt.GlobalColor.white, QFont.Weight.Normal))

def _populate_or_update_table(controller, data_source, repopulation=True):
    """Função auxiliar para popular(adicionar) ou atualizar a tabela."""
    today = date.today()
    model = controller.view.table.model().sourceModel()

    # Função auxiliar para criar e centralizar itens
    def create_centered_item(text):
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
    
    if repopulation:
        # Lista para armazenar os contratos com os dias restantes calculados
        contratos_ordenados = []
        for contrato_data in data_source:
            vigencia_fim_str = contrato_data.get("vigencia_fim", "")
            if vigencia_fim_str:
                try:
                    vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                    dias_restantes_calc = (vigencia_fim - today).days
                except ValueError:
                    dias_restantes_calc = float('-inf')  # Se a data for inválida, coloca no final
            if dias_restantes_calc >= -100:
                contratos_ordenados.append((dias_restantes_calc, contrato_data))

        # Ordenar do maior tempo para o menor (negativos no final)
        contratos_ordenados.sort(reverse=True, key=lambda x: x[0])
        controller.current_data = [contrato for _, contrato in contratos_ordenados] # Atualiza a fonte de dados ordenada

        controller.view.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        model.setRowCount(len(controller.current_data))
        model.setColumnCount(8)
        model.setHorizontalHeaderLabels(["Dias", "Contrato/Ata", "Processo", "Fornecedor", "N° de Série", "Objeto", "Valor Global", "Status"])

        header = controller.view.table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 110)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(2, 105)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(4, 175)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(7, 180)

    for row_index, contrato in enumerate(data_source if not repopulation else controller.current_data):
        vigencia_fim_str = contrato.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - today).days
            except ValueError:
                dias_restantes = "Erro Data"
        else:
            dias_restantes = "Sem Data"
        dias_item = _create_dias_item(dias_restantes)
        model.setItem(row_index, 0, dias_item)
        
        # Buscar status salvo para o contrato atual do banco de dados
        status_text = "SEÇÃO CONTRATOS"  # Status padrão
        contrato_id = contrato.get("id", "")
        
        try:
            if contrato_id and hasattr(controller, 'model') and controller.model:
                conn = controller.model._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
                status_row = cursor.fetchone()
                if status_row and status_row['status']:
                    status_text = status_row['status']
                conn.close()
            else:
                if not contrato_id:
                    print(f"ID do contrato não encontrado para a linha {row_index} ao buscar status.")
                if not (hasattr(controller, 'model') and controller.model):
                    print("Instância do modelo não encontrada no controller ao buscar status.")
                # Mantém status_text como "SEÇÃO CONTRATOS" se não puder buscar

        except sqlite3.Error as e:
            print(f"Erro ao buscar status do DB para contrato {contrato_id}: {e}")
            status_text = "Erro DB" # Indica um erro específico do banco de dados

        if repopulation:
            model.setItem(row_index, 1, create_centered_item(str(contrato.get("numero", ""))))
            model.setItem(row_index, 2, create_centered_item(str(contrato.get("licitacao_numero", ""))))
            model.setItem(row_index, 3, create_centered_item(contrato.get("fornecedor", {}).get("nome", "")))
            model.setItem(row_index, 4, create_centered_item(str(contrato.get("processo", ""))))
            model.setItem(row_index, 5, create_centered_item(str(contrato.get("objeto", "Não informado"))))
            model.setItem(row_index, 6, create_centered_item(str(contrato.get("valor_global", "Não informado"))))

        # Adiciona o status à coluna "Status" com formatação condicional
        status_item = create_centered_item(status_text)
        color, weight = _get_status_style(status_text)
        status_item.setForeground(QBrush(color) if isinstance(color, QColor) else color)
        status_item.setFont(QFont("", -1, weight))
        model.setItem(row_index, 7, status_item)

    if repopulation:
        print(f"✅ Tabela carregada com {len(controller.current_data)} contratos.")