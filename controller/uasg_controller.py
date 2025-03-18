import os
import sys
from view.main_window import MainWindow
from model.uasg_model import UASGModel
from utils.utils import refresh_uasg_menu

from view.details_dialog import DetailsDialog
from PyQt6.QtWidgets import QMessageBox, QMenu, QHeaderView, QTableView 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import  QStandardItem
from datetime import datetime, date

import time

class UASGController:
    def __init__(self, base_dir):
        self.model = UASGModel(base_dir)
        self.view = MainWindow(self)

        # Dados carregados
        self.loaded_uasgs = {}
        self.current_data = []
        self.filtered_data = []

        # Verifica se o diretório database existe
        if self.model.database_dir.exists():
            print(f"📁 Diretório 'database' encontrado: {self.model.database_dir}")
            self.loaded_uasgs = self.model.load_saved_uasgs()
            print(f"📂 UASGs carregadas: {list(self.loaded_uasgs.keys())}")
        else:
            print("⚠ Diretório 'database' não encontrado. Nenhum dado carregado.")

        # Carrega as UASGs salvas e atualiza o menu
        self.load_saved_uasgs()


    def run(self):
        """Executa a interface principal."""
        self.view.show()

    def load_saved_uasgs(self):
        """Carrega as UASGs salvas e atualiza o menu."""
        self.loaded_uasgs = self.model.load_saved_uasgs()
        refresh_uasg_menu(self)  # Atualiza o menu após carregar as UASGs

    def add_uasg_to_menu(self, uasg):
        """Adiciona uma UASG ao menu suspenso."""
        action = self.view.menu_button.menu().addAction(f"UASG {uasg}")
        action.triggered.connect(lambda: self.update_table(uasg)) # da juntar as coisa aqui pra nçao deixar o codigo grande sem necessidade


    def fetch_and_create_table(self):
        """Busca os dados da UASG e atualiza o banco de dados."""
        uasg = self.view.uasg_input.text().strip()
        if not uasg:
            self.view.label.setText("Por favor, insira um número UASG válido.")
            return

        try:
           # Inicializa dias_restantes com um valor padrão
            dias_restantes = 0
            # Se a UASG já estiver carregada, atualizar os dados
            if uasg in self.loaded_uasgs:
                added, removed = self.model.update_uasg_data(uasg)
                self.view.label.setText(f"UASG {uasg} atualizada! {added} contratos adicionados, {removed} removidos.")
                time.sleep(1)
                self.view.uasg_input.clear()  # Limpa o campo de entrada após a atualização
            else:
                # Se for nova, buscar e salvar
                data = self.model.fetch_uasg_data(uasg)
                if data is None:
                    self.view.label.setText(f"Erro ao buscar dados da UASG {uasg}.")
                    return

                self.model.save_uasg_data(uasg, data)  # Aqui o diretório database será criado, se necessário
                self.loaded_uasgs[uasg] = data
                self.add_uasg_to_menu(uasg)
                self.view.label.setText(f"UASG {uasg} carregada com sucesso!")
                time.sleep(1)
                self.view.uasg_input.clear()  # Limpa o campo de entrada após o carregamento

            self.update_table(uasg)
            self.view.tabs.setCurrentWidget(self.view.table_tab)

        except Exception as e:
            self.view.label.setText(f"Erro ao buscar UASG {uasg}: {str(e)}")

    def delete_uasg_data(self):
        """Deleta os dados da UASG informada."""
        uasg = self.view.uasg_input.text()
        if not uasg:
            QMessageBox.warning(self.view, "Erro", "Por favor, insira um número UASG válido para deletar.")
            return

        if uasg not in self.loaded_uasgs:
            QMessageBox.warning(self.view, "Erro", f"Nenhum dado encontrado para a UASG {uasg}.")
            return

        # Deletar os dados localmente
        self.model.delete_uasg_data(uasg)
        self.loaded_uasgs.pop(uasg, None)
        self.load_saved_uasgs()
        QMessageBox.information(self.view, "Sucesso", f"UASG {uasg} deletada com sucesso.")

    def update_table(self, uasg):
        """Atualiza a tabela com os dados da UASG selecionada."""
        if uasg in self.loaded_uasgs:
            self.current_data = self.loaded_uasgs[uasg]
            self.populate_table(self.current_data)
            print(f"✅ Tabela atualizada com os dados da UASG {uasg}.")
        else:
            print(f"⚠ UASG {uasg} não encontrada nos dados carregados.")
        self.load_saved_uasgs()

    def populate_table(self, data):
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

        # Atualiza self.current_data com os contratos ordenados
        self.current_data = [contrato for _, contrato in contratos_ordenados]

        self.view.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # Obtém o modelo base da tabela
        model = self.view.table.model().sourceModel()
        model.setRowCount(len(self.current_data))
        model.setColumnCount(8)
        model.setHorizontalHeaderLabels(["Dias", "Sigla OM", "Contrato/Ata", "Processo", "Fornecedor", "N° de Série", "Objeto", "valor_global"])

        # Função auxiliar para criar e centralizar itens
        def create_centered_item(text):
            item = QStandardItem(str(text))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            return item
        
        header = self.view.table.horizontalHeader()

        # Define a largura mínima para todas as colunas
        header.setMinimumSectionSize(80)

        # Configuração específica para cada coluna
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Coluna "Dias"
        header.resizeSection(0, 80)  # Largura inicial da coluna "Dias"

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Coluna "Sigla OM"
        header.resizeSection(1, 110)  # Largura inicial da coluna "Sigla OM"

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Coluna "Contrato/Ata"
        header.resizeSection(2, 110)  # Largura inicial da coluna "Contrato/Ata"

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Coluna "Processo"
        header.resizeSection(3, 105)  # Largura inicial da Coluna "Processo"

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Coluna "Fornecedor"
            
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # Coluna "N° de Série"
        header.resizeSection(5, 175) # Largura inicial da coluna "N° de Série"

        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Coluna "Objeto"
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Coluna "valor_global"

        for row_index, contrato in enumerate(self.current_data):
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

            # Definir cor do texto se o contrato já venceu
            if isinstance(dias_restantes, int) and dias_restantes < 0:
                dias_item.setForeground(Qt.GlobalColor.red)

            model.setItem(row_index, 0, dias_item)

            # Preenche as demais colunas com itens centralizados
            model.setItem(row_index, 1, create_centered_item(
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")))
            model.setItem(row_index, 2, create_centered_item(str(contrato.get("numero", ""))))
            model.setItem(row_index, 3, create_centered_item(str(contrato.get("licitacao_numero", ""))))
            model.setItem(row_index, 4, create_centered_item(contrato.get("fornecedor", {}).get("nome", "")))
            model.setItem(row_index, 5, create_centered_item(str(contrato.get("processo", ""))))
            model.setItem(row_index, 6, create_centered_item(str(contrato.get("objeto", "Não informado"))))
            model.setItem(row_index, 7, create_centered_item(str(contrato.get("valor_global", "Não informado"))))

        # Exibe uma mensagem de conclusão
        QMessageBox.information(self.view, "Concluido", f"A tabela foi carregada com sucesso!")

    def clear_table(self):
        """Limpa o conteúdo da tabela."""
        self.view.search_bar.clear()
        model = self.view.table.model()
        model.removeRows(0, model.rowCount())
        QMessageBox.information(self.view, "Limpeza", "A tabela foi limpa com sucesso!")

    def show_context_menu(self, position):
        """Exibe o menu de contexto ao clicar com o botão direito na tabela."""
        index = self.view.table.indexAt(position)
        if not index.isValid():
            return

        # Mapeia o índice filtrado para o índice do modelo base
        source_index = self.view.table.model().mapToSource(index)
        row = source_index.row()

        # Certifica-se de que a lista usada está correta
        data_source = self.current_data

        # Verifica se o índice é válido para evitar erro de "index out of range"
        if 0 <= row < len(data_source):
            contrato = data_source[row]
            menu = QMenu(self.view)
            details_action = menu.addAction("Ver Detalhes")
            details_action.triggered.connect(lambda: self.show_details_dialog(contrato))
            menu.exec(self.view.table.mapToGlobal(position))

    def show_details_dialog(self, contrato):
        """Exibe o diálogo de detalhes do contrato."""
        details_dialog = DetailsDialog(contrato, self.view)
        details_dialog.exec()