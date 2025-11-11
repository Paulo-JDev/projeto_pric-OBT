from PyQt6.QtWidgets import QHeaderView, QTableView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QFont, QColor, QBrush
from datetime import datetime, date
import sqlite3 # Adicionado para buscar status do DB
from utils.icon_loader import icon_manager

def populate_table(controller, data):
    """Preenche a tabela com os dados fornecidos, ordenando do maior para o menor tempo de vigência."""
    _populate_or_update_table(controller, data, repopulation=True)

def update_row_from_details(controller, details_info):
    """
    Atualiza APENAS a linha selecionada com as novas informações (status, objeto, etc.)
    fornecidas pelo diálogo de detalhes.
    """
    table = controller.view.table
    # Precisamos obter o índice do modelo fonte, não do proxy
    proxy_index = table.selectionModel().currentIndex()
    if not proxy_index.isValid():
        return
        
    source_index = table.model().mapToSource(proxy_index)
    selected_row_index = source_index.row()

    if selected_row_index >= 0 and selected_row_index < len(controller.current_data):
        contrato_data = controller.current_data[selected_row_index]
        
        # Atualiza os dados locais para refletir a mudança imediatamente
        contrato_data['objeto'] = details_info.get('objeto', contrato_data.get('objeto'))

        _update_row_content(controller, selected_row_index, contrato_data, new_status=details_info.get('status'))
        print(f"✅ Linha {selected_row_index} atualizada com os novos detalhes.")

def _update_row_content(controller, row_index, contrato, new_status=None):
    """
    Função centralizada que preenche ou atualiza o conteúdo de UMA ÚNICA linha da tabela,
    buscando dados do banco de dados quando necessário.
    """
    model = controller.view.table.model().sourceModel()
    today = date.today()
    contrato_id = contrato.get("id", "")

    # --- Coluna 0: Dias ---
    vigencia_fim_str = contrato.get("vigencia_fim", "")
    dias_restantes = "Sem Data"
    if vigencia_fim_str:
        try:
            vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
            dias_restantes = (vigencia_fim - today).days
        except ValueError:
            dias_restantes = "Erro Data"
    model.setItem(row_index, 0, _create_dias_item(dias_restantes))

    # --- Colunas de Dados (1 a 6) ---
    def create_centered_item(text):
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    # Busca o objeto e o status do DB para garantir a persistência
    status_text = "SEÇÃO CONTRATOS"
    objeto_text = contrato.get("objeto", "Não informado")
    
    try:
        if contrato_id and hasattr(controller, 'model') and controller.model:
            conn = controller.model._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT status, objeto_editado FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
            saved_data = cursor.fetchone()
            if saved_data:
                status_text = saved_data['status'] or status_text
                objeto_text = saved_data['objeto_editado'] or objeto_text
            conn.close()
    except sqlite3.Error as e:
        print(f"Erro ao buscar dados salvos para o contrato {contrato_id}: {e}")

    # Se um novo status foi passado (após salvar), ele tem prioridade
    if new_status:
        status_text = new_status
        
    model.setItem(row_index, 1, create_centered_item(contrato.get("numero", "")))
    model.setItem(row_index, 2, create_centered_item(contrato.get("licitacao_numero", "")))
    model.setItem(row_index, 3, create_centered_item(contrato.get("fornecedor", {}).get("nome", "")))
    model.setItem(row_index, 4, create_centered_item(contrato.get("processo", "")))
    # --- LÓGICA DO OBJETO ATUALIZADA AQUI ---
    model.setItem(row_index, 5, create_centered_item(objeto_text))
    model.setItem(row_index, 6, create_centered_item(contrato.get("valor_global", "Não informado")))

    # --- Coluna 7: Status ---
    status_item = QStandardItem(status_text)
    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    color, weight = _get_status_style(status_text)
    status_item.setForeground(QBrush(color) if isinstance(color, QColor) else color)
    status_item.setFont(QFont("", -1, weight))
    model.setItem(row_index, 7, status_item)

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
            dias_item.setIcon(icon_manager.get_icon("head_skull"))
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
        "PORTARIA": (QColor(230, 230, 150), QFont.Weight.Bold), # Amarelo menos saturado
        "EMPRESA": (QColor(230, 230, 150), QFont.Weight.Bold),    # Amarelo menos saturado
        "SIGDEM": (QColor(230, 180, 100), QFont.Weight.Bold),   # Laranja menos saturado
        "ASSINADO": (QColor(230, 180, 100), QFont.Weight.Bold), # Laranja menos saturado
        "PUBLICADO": (QColor(135, 206, 250), QFont.Weight.Bold), # Azul claro
        "ALERTA PRAZO": (QColor(255, 160, 160), QFont.Weight.Bold), # Vermelho menos saturado
        "NOTA TÉCNICA": (QColor(255, 160, 160), QFont.Weight.Bold),  # Vermelho menos saturado
        "AGU": (QColor(255, 160, 160), QFont.Weight.Bold),      # Vermelho menos saturado
        "PRORROGADO": (QColor(135, 206, 250), QFont.Weight.Bold), # Azul claro
        "SIGAD" : (QColor(230, 180, 100), QFont.Weight.Bold)
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
        header.setMaximumSectionSize(350)
        return item
    
    if repopulation:
        # Lista para armazenar os contratos com os dias restantes calculados
        contratos_ordenados = []
        for contrato_data in data_source:
            dias_restantes_calc = float('inf')
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
            _update_row_content(controller, row_index, contrato)

    if repopulation:
        print(f"✅ Tabela carregada com {len(controller.current_data)} contratos.")
