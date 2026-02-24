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
# FUNÇÕES AUXILIARES
# =============================================================================

def _format_contract_number(contrato: dict) -> str:
    """
    Formata o número do contrato para o novo padrão de visualização.
    Ex: UASG 787310 e numero "0004/2025" -> "87310/25-4/00"
    """
    try:
        # 1. Obter a UASG (código completo)
        uasg_completo = str(
            contrato.get("contratante", {})
                    .get("orgao", {})
                    .get("unidade_gestora", {})
                    .get("codigo", "")
        )

        # 2. Pegar os últimos 5 dígitos
        uasg_5_dig = uasg_completo[-5:] if uasg_completo else "UASG?"

        # 3. Obter o "numero" (ex: "0004/2025")
        numero_barra_ano = str(contrato.get("numero", "N/A"))

        numero_parte_formatada = "N/A"
        ano_2_dig = "XX"

        # 4. Dividir o "numero"
        if "/" in numero_barra_ano:
            partes = numero_barra_ano.split("/")
            if len(partes) == 2:
                numero_split, ano_split = partes

                # Remove zeros à esquerda
                numero_parte_formatada = numero_split.lstrip("0") or "0"

                # Pega os últimos 2 dígitos do ano
                ano_2_dig = ano_split[-2:] if len(ano_split) >= 2 else ano_split

        # 5. Montar o texto final
        return f"{uasg_5_dig}/{ano_2_dig}-{numero_parte_formatada}/00"

    except Exception as e:
        print(f"Erro ao formatar número do contrato: {e}")
        return str(contrato.get("numero", "Erro Format"))


def _get_status_style(status_text: str):
    """Retorna (cor, peso_fonte) para um determinado status."""
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
        "SIGAD": (QColor(230, 180, 100), QFont.Weight.Bold),
    }
    return status_styles.get(status_text, (Qt.GlobalColor.white, QFont.Weight.Normal))


def _create_status_item(status_text: str) -> QStandardItem:
    """Cria e formata um QStandardItem para a coluna 'Status'."""
    status_item = QStandardItem(status_text)
    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    color, weight = _get_status_style(status_text)
    status_item.setForeground(QBrush(color) if isinstance(color, QColor) else color)

    font = status_item.font() or QFont()
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
    else:  # "Sem Data" ou "Erro Data"
        dias_item.setForeground(QBrush(QColor("#AAAAAA")))
        dias_item.setIcon(icon_manager.get_icon("time"))

    return dias_item


def _format_date_br(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(date_str)


def _calc_dias_restantes(vigencia_fim_str: str, today: date) -> int | str:
    """Retorna int (dias) ou 'Sem Data' / 'Erro Data'."""
    if not vigencia_fim_str:
        return "Sem Data"
    try:
        vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
        return (vigencia_fim - today).days
    except ValueError:
        return "Erro Data"
    
# Constante central — mude aqui para alterar o alinhamento de todas as colunas HTML
_ALIGN = "center"  # ou "left"

def _build_vigencia_html(ini: str, fim: str, align: str = _ALIGN) -> str:
    return (
        f"<div style='text-align:{align};'>Início: {ini}</div>"
        f"<div style='text-align:{align}; color:#7a7a7a; font-size:9pt;'>Fim: {fim}</div>"
    )

def _build_contrato_html(numero: str, pregao: str, align: str = _ALIGN) -> str:
    return (
        f"<div style='text-align:{align};'>{numero}</div>"
        f"<div style='text-align:{align}; color:#7a7a7a; font-size:9pt;'>Pregão: {pregao}</div>"
    )

def _build_fornecedor_html(nome: str, nup: str, align: str = _ALIGN) -> str:
    return (
        f"<div style='text-align:{align};'>{nome}</div>"
        f"<div style='text-align:{align}; color:#7a7a7a; font-size:9pt;'>NUP: {nup}</div>"
    )

def _build_objeto_html(ini: str, fim: str, align: str = _ALIGN) -> str:
    return (
        f"<div style='text-align:{align};'>Início: {ini}</div>"
        f"<div style='text-align:{align}; color:#7a7a7a; font-size:9pt;'>Fim: {fim}</div>"
    )

def _create_plain_and_html_vigencia(contrato: dict) -> tuple[str, str]:
    ini = _format_date_br(contrato.get("vigencia_inicio", ""))
    fim = _format_date_br(contrato.get("vigencia_fim", ""))
    vig_plain = f"Início: {ini}\nFim: {fim}"
    vig_html = (
        f"<div>Início: {ini}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>Fim: {fim}</div>"
    )
    return vig_plain, vig_html


def _create_plain_and_html_contrato(contrato: dict) -> tuple[str, str]:
    formatted_contract_number = _format_contract_number(contrato)
    processo_visual = str(contrato.get("licitacao_numero", "") or "")
    contrato_plain = f"{formatted_contract_number}\nPregão: {processo_visual}"
    contrato_html = (
        f"<div>{formatted_contract_number}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>Pregão: {processo_visual}</div>"
    )
    return contrato_plain, contrato_html


def _create_plain_and_html_fornecedor(contrato: dict) -> tuple[str, str]:
    forn = str(contrato.get("fornecedor", {}).get("nome", "") or "")
    nup_visual = str(contrato.get("processo", "") or "")
    forn_plain = f"{forn}\nNUP: {nup_visual}"
    forn_html = (
        f"<div>{forn}</div>"
        f"<div style='color:#7a7a7a; font-size:9pt;'>NUP: {nup_visual}</div>"
    )
    return forn_plain, forn_html


def _get_status_and_objeto_from_db(controller, contrato_id, objeto_padrao: str) -> tuple[str, str]:
    """
    Busca status e objeto_editado no banco (status_contratos).
    Retorna (status_text, objeto_resultante).
    """
    status_text = "SEÇÃO CONTRATOS"
    objeto_text = objeto_padrao

    if not contrato_id or not getattr(controller, "model", None):
        return status_text, objeto_text

    try:
        conn = controller.model._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, objeto_editado FROM status_contratos WHERE contrato_id = ?",
            (contrato_id,),
        )
        status_row = cursor.fetchone()
        if status_row and status_row["status"]:
            status_text = status_row["status"]
            if status_row["objeto_editado"]:
                objeto_text = status_row["objeto_editado"]
        conn.close()
    except sqlite3.Error as e:
        print(f"Erro ao buscar status do DB para contrato {contrato_id}: {e}")
        status_text = "Erro DB"

    return status_text, objeto_text


# =============================================================================
# FUNÇÕES CENTRAIS DE POPULAÇÃO / ATUALIZAÇÃO
# =============================================================================

def _fill_row(model, row_index: int, contrato: dict, today: date,
              status_text: str, objeto_text: str):
    """
    Preenche TODAS as colunas (0 a 6) de uma linha do model, com base nos dados do contrato
    e no status/objeto já resolvidos.
    """

    # --- Coluna 0: Dias ---
    dias_restantes = _calc_dias_restantes(contrato.get("vigencia_fim", ""), today)
    model.setItem(row_index, 0, _create_dias_item(dias_restantes))

    # Vigência
    ini = _format_date_br(contrato.get("vigencia_inicio", ""))
    fim = _format_date_br(contrato.get("vigencia_fim", ""))
    item_vig = QStandardItem(f"Início: {ini}\nFim: {fim}")
    item_vig.setData(_build_vigencia_html(ini, fim), Qt.ItemDataRole.UserRole)
    model.setItem(row_index, 1, item_vig)

    # Contrato
    numero = _format_contract_number(contrato)
    pregao = str(contrato.get("licitacao_numero", "") or "")
    item_contrato = QStandardItem(f"{numero}\nPregão: {pregao}")
    item_contrato.setData(_build_contrato_html(numero, pregao), Qt.ItemDataRole.UserRole)
    model.setItem(row_index, 2, item_contrato)

    # Fornecedor
    nome = str(contrato.get("fornecedor", {}).get("nome", "") or "")
    nup = str(contrato.get("processo", "") or "")
    item_forn = QStandardItem(f"{nome}\nNUP: {nup}")
    item_forn.setData(_build_fornecedor_html(nome, nup), Qt.ItemDataRole.UserRole)
    model.setItem(row_index, 3, item_forn)

    # --- Coluna 4: Objeto ---
    item_objeto = QStandardItem(str(objeto_text))
    item_objeto.setData(_build_objeto_html(objeto_text), Qt.ItemDataRole.UserRole)
    model.setItem(row_index, 4, item_objeto)

    # --- Coluna 5: Valor Global ---
    item_valor = QStandardItem(str(contrato.get("valor_global", "Não informado")))
    item_valor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    model.setItem(row_index, 5, item_valor)

    # --- Coluna 6: Status ---
    model.setItem(row_index, 6, _create_status_item(status_text))


def populate_table(controller, data):
    """
    Preenche a tabela com os dados fornecidos, ordenando do maior para o menor tempo de vigência.
    """
    _populate_or_update_table(controller, data, repopulation=True)


def update_row_from_details(controller, details_info):
    """
    Atualiza APENAS a linha selecionada com as novas informações (status, objeto, etc.)
    fornecidas pelo diálogo de detalhes.
    """
    table: QTableView = controller.view.table
    proxy_index = table.selectionModel().currentIndex()
    if not proxy_index.isValid():
        return

    source_index = table.model().mapToSource(proxy_index)
    selected_row_index = source_index.row()

    if 0 <= selected_row_index < len(controller.current_data):
        contrato_data = controller.current_data[selected_row_index]

        # Atualiza o dado local imediatamente
        contrato_data["objeto"] = details_info.get("objeto", contrato_data.get("objeto"))

        new_status = details_info.get("status")
        _update_row_content(controller, selected_row_index, contrato_data, new_status=new_status)
        print(f"✅ Linha {selected_row_index} atualizada com os novos detalhes.")


def _update_row_content(controller, row_index: int, contrato: dict, new_status: str | None = None):
    """
    Atualiza o conteúdo de UMA ÚNICA linha da tabela.
    Usa a lógica centralizada de _fill_row para manter consistência.
    """
    proxy_model = controller.view.table.model()
    model = proxy_model.sourceModel()
    today = date.today()
    contrato_id = contrato.get("id", "")

    objeto_padrao = contrato.get("objeto", "Não informado")
    status_text, objeto_text = _get_status_and_objeto_from_db(controller, contrato_id, objeto_padrao)

    # Se veio um novo status do diálogo, ele prevalece sobre o do banco
    if new_status:
        status_text = new_status

    _fill_row(model, row_index, contrato, today, status_text, objeto_text)


def _populate_or_update_table(controller, data_source, repopulation: bool = True):
    """
    Função auxiliar para popular (repopulation=True) ou atualizar (repopulation=False) a tabela.
    """
    today = date.today()
    proxy_model = controller.view.table.model()
    model = proxy_model.sourceModel()

    if repopulation:
        # --- 1. Ordenação dos dados ---
        contratos_ordenados = []
        for contrato_data in data_source:
            dias_restantes_calc = float("inf")
            vigencia_fim_str = contrato_data.get("vigencia_fim", "")
            if vigencia_fim_str:
                try:
                    vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                    dias_restantes_calc = (vigencia_fim - today).days
                except ValueError:
                    # Coloca com -inf para cair no fim da ordenação
                    dias_restantes_calc = float("-inf")

            # Filtra se desejar (como antes: >= -100)
            if dias_restantes_calc >= -100:
                contratos_ordenados.append((dias_restantes_calc, contrato_data))

        contratos_ordenados.sort(reverse=True, key=lambda x: x[0])
        controller.current_data = [contrato for _, contrato in contratos_ordenados]

        # --- 2. Configuração do Modelo e Headers ---
        controller.view.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        model.setRowCount(len(controller.current_data))
        model.setColumnCount(7)
        model.setHorizontalHeaderLabels(
            ["Dias", "Vigência", "Contrato", "Fornecedor", "Objeto", "Valor Global", "Status"]
        )

        # Delegates para renderizar HTML nas colunas necessárias
        delegate = RichTextDelegate(controller.view.table)
        controller.view.table.setItemDelegateForColumn(1, delegate)  # Vigência
        controller.view.table.setItemDelegateForColumn(2, delegate)  # Contrato
        controller.view.table.setItemDelegateForColumn(3, delegate)  # Fornecedor

        header: QHeaderView = controller.view.table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setMaximumSectionSize(350)

        # Configuração de tamanho e redimensionamento por coluna
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)      # Dias
        header.resizeSection(0, 80)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)      # Vigência
        header.resizeSection(1, 130)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)      # Contrato
        header.resizeSection(2, 170)

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Fornecedor
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)          # Objeto
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Valor Global

        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)      # Status
        header.resizeSection(6, 180)

        controller.view.table.verticalHeader().setDefaultSectionSize(44)

    # --- 3. Preenchimento / Atualização dos Dados ---
    data_to_iterate = controller.current_data if repopulation else data_source

    for row_index, contrato in enumerate(data_to_iterate):
        contrato_id = contrato.get("id", "")
        objeto_padrao = contrato.get("objeto", "Não informado")

        status_text, objeto_text = _get_status_and_objeto_from_db(controller, contrato_id, objeto_padrao)
        _fill_row(model, row_index, contrato, today, status_text, objeto_text)

    if repopulation:
        print(f"✅ Tabela carregada com {len(controller.current_data)} contratos.")
