# Contratos/controller/controller_table.py

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QStandardItem, QFont, QColor, QBrush, QTextDocument
from PyQt6.QtWidgets import QHeaderView, QTableView, QAbstractItemView, QStyledItemDelegate

from datetime import datetime, date
import sqlite3
from utils.icon_loader import icon_manager

class RichTextDelegate(QStyledItemDelegate):
    """Renderiza HTML (UserRole), mantendo texto simples (DisplayRole) para busca."""
    def paint(self, painter, option, index):
        html = index.data(Qt.ItemDataRole.UserRole)
        if not html:
            return super().paint(painter, option, index)

        doc = QTextDocument()
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width())

        painter.save()
        painter.translate(option.rect.topLeft())
        rectf = QRectF(0, 0, option.rect.width(), option.rect.height())
        doc.drawContents(painter, rectf)
        painter.restore()

    def sizeHint(self, option, index):
        html = index.data(Qt.ItemDataRole.UserRole)
        if not html:
            return super().sizeHint(option, index)

        doc = QTextDocument()
        doc.setHtml(html)
        doc.setTextWidth(option.rect.width())
        return doc.size().toSize()
    
# =============================================================================
# NOVAS FUNÇÕES AUXILIARES CENTRALIZADAS
# =============================================================================

def _format_contract_number(contrato: dict) -> str:
    """
    Formata o número do contrato para o novo padrão de visualização.
    Ex: 787310 e 0004/2025 -> "87310/25-4/00"
    """
    try:
        # 1. Obter a UASG (código completo)
        uasg_completo = str(contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", ""))
        # 2. Pegar os últimos 5 dígitos
        uasg_5_dig = uasg_completo[-5:] if uasg_completo else "UASG?"
        
        # 3. Obter o "numero" (ex: "0004/2025")
        numero_barra_ano = str(contrato.get("numero", "N/A"))
        
        numero_parte_formatada = "N/A"
        ano_2_dig = "XX"
        
        # 4. Dividir o "numero"
        if "/" in numero_barra_ano and len(numero_barra_ano.split('/')) == 2:
            numero_split, ano_split = numero_barra_ano.split('/')
            
            # --- ✅ ESTA É A MUDANÇA ---
            # Remove os zeros à esquerda
            numero_parte_formatada = numero_split.lstrip('0')
            
            # Se o número era "0" ou "000", lstrip vai deixar vazio.
            # Corrigimos isso para que mostre "0".
            if not numero_parte_formatada:
                numero_parte_formatada = "0"
            # --- FIM DA MUDANÇA ---
            
            # Regra: Pega os últimos 2 dígitos do ano
            ano_2_dig = ano_split[-2:] if len(ano_split) >= 2 else ano_split
        
        # 5. Montar o texto final
        return f"{uasg_5_dig}/{ano_2_dig}-{numero_parte_formatada}/00"

    except Exception as e:
        print(f"Erro ao formatar número do contrato: {e}")
        return str(contrato.get("numero", "Erro Format"))
    
def _create_status_item(status_text: str) -> QStandardItem:
    """Cria e formata um QStandardItem para a coluna 'Status'."""
    status_item = QStandardItem(status_text)
    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    color, weight = _get_status_style(status_text)
    
    status_item.setForeground(QBrush(color) if isinstance(color, QColor) else color)
    
    # Usa a lógica correta para aplicar o peso da fonte (inspirado no seu 'atas_controller')
    font = status_item.font()
    if not font:
        font = QFont() # Fallback
    font.setWeight(weight)
    status_item.setFont(font)
    
    return status_item

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
    status_styles = {
        "SEÇÃO CONTRATOS": (Qt.GlobalColor.white, QFont.Weight.Bold),
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
    return status_styles.get(status_text, (Qt.GlobalColor.white, QFont.Weight.Normal))

def _format_date_br(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return str(date_str)

# =============================================================================
# FUNÇÕES PRINCIPAIS ATUALIZADAS
# =============================================================================

def populate_table(controller, data):
    """Preenche a tabela com os dados fornecidos, ordenando do maior para o menor tempo de vigência."""
    _populate_or_update_table(controller, data, repopulation=True)

def update_row_from_details(controller, details_info):
    """
    Atualiza APENAS a linha selecionada com as novas informações (status, objeto, etc.)
    fornecidas pelo diálogo de detalhes.
    """
    table = controller.view.table
    proxy_index = table.selectionModel().currentIndex()
    if not proxy_index.isValid():
        return
        
    source_index = table.model().mapToSource(proxy_index)
    selected_row_index = source_index.row()

    if selected_row_index >= 0 and selected_row_index < len(controller.current_data):
        contrato_data = controller.current_data[selected_row_index]
        
        # Atualiza os dados locais para refletir a mudança imediatamente
        contrato_data['objeto'] = details_info.get('objeto', contrato_data.get('objeto'))

        # Chama a função de atualização de linha ÚNICA
        _update_row_content(controller, selected_row_index, contrato_data, new_status=details_info.get('status'))
        print(f"✅ Linha {selected_row_index} atualizada com os novos detalhes.")

def _update_row_content(controller, row_index, contrato, new_status=None):
    """
    Função centralizada que ATUALIZA o conteúdo de UMA ÚNICA linha da tabela,
    buscando dados do banco de dados quando necessário.
    """
    model = controller.view.table.model().sourceModel()
    today = date.today()
    contrato_id = contrato.get("id", "")

    # Função auxiliar local
    def create_centered_item(text):
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

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
    status_text = "SEÇÃO CONTRATOS"
    objeto_text = contrato.get("objeto", "Não informado")
    
        # --- ✅ NOVO LAYOUT: 7 COLUNAS ---
    formatted_contract_number = _format_contract_number(contrato)

    # Processo (visual) = licitacao_numero (API)
    processo_visual = str(contrato.get("licitacao_numero", "") or "")
    contrato_plain = f"{formatted_contract_number}\nProcesso: {processo_visual}"
    contrato_html = (
        f"<div>{formatted_contract_number}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>Processo: {processo_visual}</div>"
    )
    item_contrato = QStandardItem(contrato_plain)
    item_contrato.setData(contrato_html, Qt.ItemDataRole.UserRole)
    item_contrato.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    model.setItem(row_index, 1, item_contrato)

    # NUP (visual) = processo (API) -> dentro de Fornecedor
    forn = str(contrato.get("fornecedor", {}).get("nome", "") or "")
    nup_visual = str(contrato.get("processo", "") or "")
    forn_plain = f"{forn}\nNUP: {nup_visual}"
    forn_html = (
        f"<div>{forn}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>NUP: {nup_visual}</div>"
    )
    item_forn = QStandardItem(forn_plain)
    item_forn.setData(forn_html, Qt.ItemDataRole.UserRole)
    item_forn.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    model.setItem(row_index, 2, item_forn)

    # Vigência (compacta)
    ini = _format_date_br(contrato.get("vigencia_inicio", ""))
    fim = _format_date_br(contrato.get("vigencia_fim", ""))
    vig_plain = f"Início: {ini}\nFim: {fim}"
    vig_html = (
        f"<div>Início: {ini}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>Fim: {fim}</div>"
    )
    item_vig = QStandardItem(vig_plain)
    item_vig.setData(vig_html, Qt.ItemDataRole.UserRole)
    item_vig.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    model.setItem(row_index, 3, item_vig)

    # Objeto / Valor / Status
    model.setItem(row_index, 4, create_centered_item(objeto_text))
    model.setItem(row_index, 5, create_centered_item(contrato.get("valor_global", "Não informado")))
    model.setItem(row_index, 6, _create_status_item(status_text))

def _populate_or_update_table(controller, data_source, repopulation=True):
    """Função auxiliar para popular (repopulation=True) ou atualizar (repopulation=False) a tabela."""
    today = date.today()
    model = controller.view.table.model().sourceModel()
    
    # Esta função auxiliar agora é definida *após* 'header' ser criado
    # (movido para dentro do bloco 'if repopulation')
    
    if repopulation:
        # --- 1. Ordenação dos dados ---
        contratos_ordenados = []
        for contrato_data in data_source:
            dias_restantes_calc = float('inf')
            vigencia_fim_str = contrato_data.get("vigencia_fim", "")
            if vigencia_fim_str:
                try:
                    vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                    dias_restantes_calc = (vigencia_fim - today).days
                except ValueError:
                    dias_restantes_calc = float('-inf') 
            if dias_restantes_calc >= -100:
                contratos_ordenados.append((dias_restantes_calc, contrato_data))

        contratos_ordenados.sort(reverse=True, key=lambda x: x[0])
        controller.current_data = [contrato for _, contrato in contratos_ordenados]

        # --- 2. Configuração do Modelo e Headers ---
        controller.view.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        model.setRowCount(len(controller.current_data))
        model.setColumnCount(7)
        model.setHorizontalHeaderLabels(["Dias", "Contrato", "Fornecedor", "Vigência", "Objeto", "Valor Global", "Status"])

        # Delegate para renderizar as “sub-linhas”
        delegate = RichTextDelegate(controller.view.table)
        controller.view.table.setItemDelegateForColumn(1, delegate)  # Contrato (com Processo dentro)
        controller.view.table.setItemDelegateForColumn(2, delegate)  # Fornecedor (com NUP dentro)
        controller.view.table.setItemDelegateForColumn(3, delegate)  # Vigência (início/fim)

        header = controller.view.table.horizontalHeader()
        
        # --- Função auxiliar de centralização (definida aqui pois usa 'header') ---
        def create_centered_item(text):
            item = QStandardItem(str(text))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setMaximumSectionSize(350) # Limita o tamanho máximo
            return item
        
        # --- 3. Configuração do Layout da Tabela (inspirado no seu exemplo) ---
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Dias
        header.resizeSection(0, 80)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Contrato
        header.resizeSection(1, 180)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)      # Fornecedor
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Vigência
        header.resizeSection(3, 170)

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)      # Objeto
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Valor Global

        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Status
        header.resizeSection(6, 180)

    # --- 4. Preenchimento dos Dados ---
    # Este loop agora preenche TODAS as colunas, sem chamar _update_row_content
    
    # Determina a fonte de dados (a lista ordenada ou a lista original)
    data_to_iterate = controller.current_data if repopulation else data_source
    
    for row_index, contrato in enumerate(data_to_iterate):
        
        # --- Coluna 0: Dias ---
        vigencia_fim_str = contrato.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - today).days
            except ValueError:
                dias_restantes = "Erro Data"
        else:
            dias_restantes = "Sem Data"
        model.setItem(row_index, 0, _create_dias_item(dias_restantes))
        
        # --- Coluna 7: Status (Precisa ser buscado antes de 'repopulation') ---
        status_text = "SEÇÃO CONTRATOS"  # Status padrão
        objeto_text = contrato.get("objeto", "Não informado") # Padrão: Objeto original
        contrato_id = contrato.get("id", "")
        
        try:
            if contrato_id and hasattr(controller, 'model') and controller.model:
                conn = controller.model._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT status, objeto_editado FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
                status_row = cursor.fetchone()
                if status_row and status_row['status']:
                    status_text = status_row['status']
                
                    if status_row['objeto_editado']:
                        objeto_text = status_row['objeto_editado']
                conn.close()
        except sqlite3.Error as e:
            print(f"Erro ao buscar status do DB para contrato {contrato_id}: {e}")
            status_text = "Erro DB"
        
        # --- Colunas 1-6 (Apenas se for 'repopulation') ---
        if repopulation:
            formatted_contract_number = _format_contract_number(contrato)

            # Contrato + Processo (licitacao_numero)
            processo_visual = str(contrato.get("licitacao_numero", "") or "")
            contrato_plain = f"{formatted_contract_number}\nProcesso: {processo_visual}"
            contrato_html = (
                f"<div>{formatted_contract_number}</div>"
                f"<div style='color:#7a7a7a; font-size:9pt;'>Processo: {processo_visual}</div>"
            )
            item_contrato = QStandardItem(contrato_plain)
            item_contrato.setData(contrato_html, Qt.ItemDataRole.UserRole)
            item_contrato.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            model.setItem(row_index, 1, item_contrato)

            # Fornecedor + NUP (processo)
            forn = str(contrato.get("fornecedor", {}).get("nome", "") or "")
            nup_visual = str(contrato.get("processo", "") or "")
            forn_plain = f"{forn}\nNUP: {nup_visual}"
            forn_html = (
                f"<div>{forn}</div>"
                f"<div style='color:#7a7a7a; font-size:9pt;'>NUP: {nup_visual}</div>"
            )
            item_forn = QStandardItem(forn_plain)
            item_forn.setData(forn_html, Qt.ItemDataRole.UserRole)
            item_forn.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            model.setItem(row_index, 2, item_forn)

            # Vigência
            ini = _format_date_br(contrato.get("vigencia_inicio", ""))
            fim = _format_date_br(contrato.get("vigencia_fim", ""))
            vig_plain = f"Início: {ini}\nFim: {fim}"
            vig_html = (
                f"<div>Início: {ini}</div>"
                f"<div style='color:#7a7a7a; font-size:9pt;'>Fim: {fim}</div>"
            )
            item_vig = QStandardItem(vig_plain)
            item_vig.setData(vig_html, Qt.ItemDataRole.UserRole)
            item_vig.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            model.setItem(row_index, 3, item_vig)

            # Objeto / Valor / Status
            model.setItem(row_index, 4, create_centered_item(str(objeto_text)))
            model.setItem(row_index, 5, create_centered_item(str(contrato.get("valor_global", "Não informado"))))
            model.setItem(row_index, 6, _create_status_item(status_text))

            controller.view.table.verticalHeader().setDefaultSectionSize(44)
            #controller.view.table.resizeRowsToContents()


    if repopulation:
        print(f"✅ Tabela carregada com {len(controller.current_data)} contratos.")
