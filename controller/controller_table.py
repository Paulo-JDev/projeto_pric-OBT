from PyQt6.QtWidgets import QHeaderView, QTableView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QFont, QColor, QBrush
from datetime import datetime, date
from pathlib import Path
import json

from model.uasg_model import resource_path
from utils.icon_loader import icon_manager

def populate_table(controller, data):
    """Preenche a tabela com os dados fornecidos, ordenando do maior para o menor tempo de vigência."""
    today = date.today()

    # Lista para armazenar os contratos com os dias restantes calculados
    contratos_ordenados = []

    for contrato in data:
        vigencia_fim_str = contrato.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - today).days
            except ValueError:
                dias_restantes = float('-inf')  # Se a data for inválida, coloca no final
        else:
            dias_restantes = float('-inf')  # Se a data estiver vazia, coloca no final
        
        contratos_ordenados.append((dias_restantes, contrato))

    # Ordenar do maior tempo para o menor (negativos no final)
    contratos_ordenados.sort(reverse=True, key=lambda x: x[0])

    # Atualiza controller.current_data com os contratos ordenados
    controller.current_data = [contrato for _, contrato in contratos_ordenados]

    controller.view.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    # Obtém o modelo base da tabela
    model = controller.view.table.model().sourceModel()
    model.setRowCount(len(controller.current_data))
    model.setColumnCount(8)  # Aumente o número de colunas para 8
    model.setHorizontalHeaderLabels(["Dias", "Contrato/Ata", "Processo", "Fornecedor", "N° de Série", "Objeto", "Valor Global", "Status"])  # Adicione "Status"

    # Função auxiliar para criar e centralizar itens
    def create_centered_item(text):
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item
    
    header = controller.view.table.horizontalHeader()

    # Define a largura mínima para todas as colunas
    header.setMinimumSectionSize(80)

    # Configuração específica para cada coluna
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Coluna "Dias"
    header.resizeSection(0, 80)  # Largura inicial da coluna "Dias"

    header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Coluna "Contrato/Ata"
    header.resizeSection(1, 110)  # Largura inicial da coluna "Contrato/Ata"

    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Coluna "Processo"
    header.resizeSection(2, 105)  # Largura inicial da Coluna "Processo"

    header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Coluna "Fornecedor"
        
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Coluna "N° de Série"
    header.resizeSection(4, 175) # Largura inicial da coluna "N° de Série"

    header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Coluna "Objeto"
    header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Coluna "valor_global"
    header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Coluna "Status"
    header.resizeSection(7, 180)  # Largura inicial da coluna "Status"

    for row_index, contrato in enumerate(controller.current_data):
        vigencia_fim_str = contrato.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - today).days
            except ValueError:
                dias_restantes = "Erro Data"
        else:
            dias_restantes = "Sem Data"

        # Cria e centraliza o item da coluna "Dias"
        dias_item = QStandardItem(str(dias_restantes))
        dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Definir cor e ícone com base no número de dias restantes
        if isinstance(dias_restantes, int):
            if dias_restantes < 0:
                # Contrato vencido
                dias_item.setForeground(Qt.GlobalColor.red)
                dias_item.setIcon(icon_manager.get_icon("delete"))
            elif dias_restantes <= 89:
                # Entre 0 e 89 dias - laranja com ícone de alerta
                dias_item.setForeground(QBrush(QColor("#FFA500")))  # Laranja
                dias_item.setIcon(icon_manager.get_icon("alert"))
            elif dias_restantes <= 179:
                # Entre 90 e 179 dias - amarelo com ícone de mensagem
                dias_item.setForeground(QBrush(QColor("#FFD700")))  # Amarelo
                dias_item.setIcon(icon_manager.get_icon("mensagem"))
            else:
                # 180+ dias - verde com ícone de aprovado
                dias_item.setForeground(QBrush(QColor("#32CD32")))  # Verde
                dias_item.setIcon(icon_manager.get_icon("aproved"))
            
            # Deixar o texto em negrito para todos os casos
            font = dias_item.font()
            font.setBold(True)
            dias_item.setFont(font)

        model.setItem(row_index, 0, dias_item)
        
        # Buscar status salvo para o contrato atual
        try:
            uasg_codigo = contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")
            contrato_id = contrato.get("id", "")
            status_file = Path(resource_path("status_glob")) / str(uasg_codigo) / f"{contrato_id}.json"
            
            status_text = "SEÇÃO CONTRATOS"  # Status padrão
            
            if status_file.exists():
                with status_file.open("r", encoding="utf-8") as file:
                    status_data = json.load(file)
                    status_text = status_data.get("status", "SEÇÃO CONTRATOS")
        except Exception as e:
            print(f"Erro ao carregar status para contrato {contrato_id}: {e}")
            status_text = "Erro"

        # Preenche as demais colunas com itens centralizados
        model.setItem(row_index, 1, create_centered_item(str(contrato.get("numero", ""))))
        model.setItem(row_index, 2, create_centered_item(str(contrato.get("licitacao_numero", ""))))
        model.setItem(row_index, 3, create_centered_item(contrato.get("fornecedor", {}).get("nome", "")))
        model.setItem(row_index, 4, create_centered_item(str(contrato.get("processo", ""))))
        model.setItem(row_index, 5, create_centered_item(str(contrato.get("objeto", "Não informado"))))
        model.setItem(row_index, 6, create_centered_item(str(contrato.get("valor_global", "Não informado"))))

        # Adiciona o status à coluna "Status" com formatação condicional
        status_item = create_centered_item(status_text)
        
        # Aplica cores diferentes dependendo do status
        if status_text == "SEÇÃO CONTRATOS":
            status_item.setForeground(Qt.GlobalColor.white)
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "ATA GERADA":
            status_item.setForeground(QColor(144, 238, 144))  # Verde claro menos saturado
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "EMPRESA":
            status_item.setForeground(QColor(230, 230, 150))  # Amarelo menos saturado
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "SIGDEM":
            status_item.setForeground(QColor(230, 180, 100))  # Laranja menos saturado
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "ASSINADO":
            status_item.setForeground(QColor(144, 238, 144))  # Verde claro
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "PUBLICADO":
            status_item.setForeground(QColor(135, 206, 250))  # Azul claro
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "ALERTA PRAZO":
            status_item.setForeground(QColor(255, 160, 160))  # Vermelho menos saturado
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "NOTA TÉCNICA":
            status_item.setForeground(QColor(230, 230, 150))  # Amarelo menos saturado
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "AGU":
            status_item.setForeground(QColor(135, 206, 250))  # Azul claro
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        elif status_text == "PRORROGADO":
            status_item.setForeground(QColor(144, 238, 144))  # Verde claro
            status_item.setFont(QFont("", -1, QFont.Weight.Bold))
        
        model.setItem(row_index, 7, status_item)

    # Notifica sem mostrar uma mensagem intrusiva
    print(f"✅ Tabela carregada com {len(data)} contratos.")

def update_status_column(controller):
    """Atualiza apenas a coluna de status da tabela sem recarregar todos os dados."""
    if not controller.current_data:
        return
        
    # Obtém o modelo base da tabela
    model = controller.view.table.model().sourceModel()
    today = date.today()
    
    # Atualiza as colunas de status e dias para cada linha
    for row_index, contrato in enumerate(controller.current_data):
        try:
            # Atualiza a coluna de dias
            vigencia_fim_str = contrato.get("vigencia_fim", "")
            if vigencia_fim_str:
                try:
                    vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                    dias_restantes = (vigencia_fim - today).days
                    
                    # Cria e centraliza o item da coluna "Dias"
                    dias_item = QStandardItem(str(dias_restantes))
                    dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Definir cor e ícone com base no número de dias restantes
                    if dias_restantes < 0:
                        # Contrato vencido
                        dias_item.setForeground(Qt.GlobalColor.red)
                        dias_item.setIcon(icon_manager.get_icon("delete"))
                    elif dias_restantes <= 89:
                        # Entre 0 e 89 dias - laranja com ícone de alerta
                        dias_item.setForeground(QBrush(QColor("#FFA500")))  # Laranja
                        dias_item.setIcon(icon_manager.get_icon("alert"))
                    elif dias_restantes <= 179:
                        # Entre 90 e 179 dias - amarelo com ícone de mensagem
                        dias_item.setForeground(QBrush(QColor("#FFD700")))  # Amarelo
                        dias_item.setIcon(icon_manager.get_icon("mensagem"))
                    else:
                        # 180+ dias - verde com ícone de aprovado
                        dias_item.setForeground(QBrush(QColor("#32CD32")))  # Verde
                        dias_item.setIcon(icon_manager.get_icon("aproved"))
                    
                    # Deixar o texto em negrito para todos os casos
                    font = dias_item.font()
                    font.setBold(True)
                    dias_item.setFont(font)
                    
                    # Atualiza a coluna de dias
                    model.setItem(row_index, 0, dias_item)
                except ValueError:
                    pass
            
            # Atualiza a coluna de status
            uasg_codigo = contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")
            contrato_id = contrato.get("id", "")
            
            if not uasg_codigo or not contrato_id:
                continue
                
            # Verifica o arquivo de status
            status_file = Path(resource_path("status_glob")) / str(uasg_codigo) / f"{contrato_id}.json"
            
            status_text = "SEÇÃO CONTRATOS"  # Status padrão
            
            if status_file.exists():
                with status_file.open("r", encoding="utf-8") as file:
                    status_data = json.load(file)
                    status_text = status_data.get("status", "SEÇÃO CONTRATOS")
            
            # Cria o item de status formatado
            def create_centered_item(text):
                item = QStandardItem(str(text))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item
            
            status_item = create_centered_item(status_text)
            
            # Aplica cores diferentes dependendo do status
            if status_text == "SEÇÃO CONTRATOS":
                status_item.setForeground(Qt.GlobalColor.white)
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "ATA GERADA":
                status_item.setForeground(QColor(144, 238, 144))  # Verde claro menos saturado
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "EMPRESA":
                status_item.setForeground(QColor(230, 230, 150))  # Amarelo menos saturado
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "SIGDEM":
                status_item.setForeground(QColor(230, 180, 100))  # Laranja menos saturado
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "ASSINADO":
                status_item.setForeground(QColor(144, 238, 144))  # Verde claro
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "PUBLICADO":
                status_item.setForeground(QColor(135, 206, 250))  # Azul claro
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "ALERTA PRAZO":
                status_item.setForeground(QColor(255, 160, 160))  # Vermelho menos saturado
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "NOTA TÉCNICA":
                status_item.setForeground(QColor(230, 230, 150))  # Amarelo menos saturado
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "AGU":
                status_item.setForeground(QColor(135, 206, 250))  # Azul claro
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            elif status_text == "PRORROGADO":
                status_item.setForeground(QColor(144, 238, 144))  # Verde claro
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            
            # Atualiza apenas a coluna de status
            model.setItem(row_index, 7, status_item)
            
        except Exception as e:
            print(f"Erro ao atualizar status do contrato: {e}")
            
    print("✅ Colunas de status e dias atualizadas.") 