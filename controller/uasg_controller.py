from view.main_window import MainWindow
from model.uasg_model import UASGModel
from utils.utils import refresh_uasg_menu
from view.details_dialog import DetailsDialog
from controller.controller_table import populate_table, update_status_column
from utils.icon_loader import icon_manager

from PyQt6.QtWidgets import QMessageBox, QMenu, QFileDialog
import requests
import sqlite3
import json
import csv
import os # Adicionado para os.path.expanduser

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
        action = self.view.menu_button.menu().addAction(f"UASG {uasg}", lambda: self.update_table(uasg))


    def fetch_and_create_table(self):
        """Busca os dados da UASG e atualiza o banco de dados."""
        uasg = self.view.uasg_input.text().strip()

        # Verificação se a UASG está vazia ou contém caracteres não numéricos
        if not uasg or not uasg.isdigit():
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número UASG válido.")
            return

        try:
            # Se a UASG já estiver carregada, atualizar os dados
            # Vamos mudar a lógica aqui: se a UASG já existe, apenas carregamos da memória/DB
            # A atualização explícita pode ser uma outra função/botão.
            if uasg in self.loaded_uasgs and self.loaded_uasgs[uasg]: # Verifica se há dados carregados
                self.view.label.setText(f"UASG {uasg} já carregada. Exibindo dados locais.")
                self.view.uasg_input.clear()
                # Não chama update_uasg_data aqui, apenas carrega o que já tem.
                # A função update_table(uasg) já vai pegar os dados de self.loaded_uasgs
                # que foram carregados do DB no __init__ ou após um save.
            else:
                # Se for nova, buscar e salvar
                data = self.model.fetch_uasg_data(uasg)
                if data is None:
                    QMessageBox.critical(self.view, "Erro de API", f"Erro ao buscar dados da UASG {uasg}.")
                    return

                self.model.save_uasg_data(uasg, data)
                self.loaded_uasgs[uasg] = data
                self.add_uasg_to_menu(uasg)
                self.view.label.setText(f"UASG {uasg} carregada e salva com sucesso!")
                # time.sleep(1) # Considere remover ou usar QStatusBar
                self.view.uasg_input.clear()

            # Garante que os dados mais recentes (do DB ou da API) estejam em self.loaded_uasgs
            # antes de chamar update_table
            self.loaded_uasgs = self.model.load_saved_uasgs()

            self.update_table(uasg)
            self.view.tabs.setCurrentWidget(self.view.table_tab)
        except requests.exceptions.RequestException as e: # Exceção mais específica
            QMessageBox.critical(self.view, "Erro de Rede", f"Erro de rede ao buscar UASG {uasg}: {str(e)}")
        except Exception as e: # Genérico para outros erros
            QMessageBox.critical(self.view, "Erro Inesperado", f"Erro inesperado ao processar UASG {uasg}: {str(e)}")

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
            # Recarrega os dados do arquivo JSON para garantir que estão atualizados
            self.loaded_uasgs = self.model.load_saved_uasgs()
            
            # Atualiza os dados atuais com os dados recarregados
            if uasg in self.loaded_uasgs:
                self.current_data = self.loaded_uasgs[uasg]
                
                # Obter o nome resumido da UASG para mostrar no label
                nome_resumido = ""
                if self.current_data and len(self.current_data) > 0:
                    contrato = self.current_data[0]
                    nome_resumido = contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
                
                # Atualiza o label na interface
                self.view.uasg_info_label.setText(f"UASG: {uasg} - {nome_resumido}")
                
                # Popula a tabela com os dados usando a função do módulo controller_table
                populate_table(self, self.current_data)
                print(f"✅ Tabela atualizada com os dados da UASG {uasg}.")
            else:
                # Limpa o label se não houver dados
                self.view.uasg_info_label.setText(f"UASG: -")
                print(f"⚠ UASG {uasg} não encontrada nos dados recarregados.")
        else:
            # Limpa o label se a UASG não for encontrada
            self.view.uasg_info_label.setText(f"UASG: -")
            print(f"⚠ UASG {uasg} não encontrada nos dados carregados.")
        self.load_saved_uasgs()

    def clear_table(self):
        """Limpa o conteúdo da tabela."""
        self.view.search_bar.clear()
        model = self.view.table.model()
        model.removeRows(0, model.rowCount())
        
        # Limpa o rótulo da UASG
        self.view.uasg_info_label.setText("UASG: -")
        
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
            # Adiciona o ícone "init" à ação "Ver Detalhes"
            details_action = menu.addAction(icon_manager.get_icon("init"), "Ver Detalhes")
            details_action.triggered.connect(lambda: self.show_details_dialog(contrato))
            menu.exec(self.view.table.mapToGlobal(position))

    def show_details_dialog(self, contrato):
        """Exibe o diálogo de detalhes do contrato."""
        details_dialog = DetailsDialog(contrato, self.model, self.view) # Passa self.model
        
        # Conectar o sinal data_saved ao método que atualiza a tabela
        details_dialog.data_saved.connect(self.update_table_from_details)
        
        details_dialog.exec()

    def update_table_from_details(self):
        """Atualiza a tabela quando os dados são salvos na DetailsDialog."""
        # Identifica a UASG atual e o contrato selecionado
        uasg_atual = None
        row_atual = -1
        
        # Obter índice da linha selecionada
        selected_indexes = self.view.table.selectionModel().selectedIndexes()
        if selected_indexes:
            # Mapeia a seleção para o modelo base
            source_index = self.view.table.model().mapToSource(selected_indexes[0])
            row_atual = source_index.row()
        
        # Atualizar apenas a coluna de status (método mais rápido)
        update_status_column(self)
        
        # Restaurar a seleção se existia antes
        if row_atual >= 0 and row_atual < len(self.current_data):
            new_index = self.view.table.model().sourceModel().index(row_atual, 0)
            proxy_index = self.view.table.model().mapFromSource(new_index)
            self.view.table.selectRow(proxy_index.row())
        
        return
    
    def show_msg_dialog(self):
        """Exibe o diálogo de mensagens."""
        # Implementação futura do diálogo de mensagens
        QMessageBox.information(self.view, "Mensagens", "Funcionalidade de mensagens ainda não implementada.")
        # msg_dialog = "Teste Paulo vitor"
        # print(msg_dialog)

    def export_status_data(self):
        """Exporta todos os dados de status para um arquivo JSON."""
        all_status_data = self.model.get_all_status_data()
        if not all_status_data:
            QMessageBox.information(self.view, "Exportar Status", "Não há dados de status para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Salvar Dados de Status",
            "", # Diretório inicial
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_status_data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self.view, "Exportar Status", f"Dados de status exportados com sucesso para:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.view, "Erro ao Exportar", f"Não foi possível salvar o arquivo: {e}")

    def import_status_data(self):
        """Importa dados de status de um arquivo JSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Abrir Dados de Status",
            "", # Diretório inicial
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data_to_import = json.load(f)
                
                self.model.import_statuses(data_to_import)
                QMessageBox.information(self.view, "Importar Status", "Dados de status importados com sucesso!\nA tabela será atualizada.")
                self.load_saved_uasgs() # Recarrega UASGs e atualiza o menu
                # Força a atualização da tabela visível, se houver alguma UASG carregada
                current_uasg_text = self.view.uasg_info_label.text()
                if "UASG: " in current_uasg_text and current_uasg_text.split(" ")[1] != "-":
                    uasg_code = current_uasg_text.split(" ")[1]
                    self.update_table(uasg_code) # Atualiza a tabela com a UASG atual

            except json.JSONDecodeError:
                QMessageBox.critical(self.view, "Erro de Importação", "Arquivo JSON inválido ou corrompido.")
            except Exception as e:
                QMessageBox.critical(self.view, "Erro ao Importar", f"Não foi possível importar os dados: {e}")

    def export_table_to_csv(self):
        if not self.current_data:
            QMessageBox.information(self.view, "Exportar Tabela", "Não há dados na tabela para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Salvar Tabela como CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                # Obter cabeçalhos do modelo da tabela
                model = self.view.table.model().sourceModel() # Usar o sourceModel se houver proxy
                headers = [model.horizontalHeaderItem(i).text() for i in range(model.columnCount())]
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';') # Usar ; como delimitador é comum no Brasil
                    writer.writerow(headers)
                    
                    # Iterar sobre as linhas visíveis (ou self.current_data se não houver filtro complexo)
                    # Para este exemplo, vamos usar self.current_data e mapear para as colunas
                    # Isso precisa ser ajustado conforme a estrutura exata dos seus dados e colunas
                    for row_data_dict in self.current_data:
                        # Mapear os dados do dicionário para a ordem das colunas
                        # Esta parte é um exemplo e precisa ser adaptada
                        row_to_write = [
                            # Exemplo para as primeiras colunas, você precisará mapear todas
                            self._calculate_dias_restantes(row_data_dict.get("vigencia_fim", "")), # Para "Dias"
                            row_data_dict.get("numero", ""),
                            row_data_dict.get("licitacao_numero", ""),
                            row_data_dict.get("fornecedor", {}).get("nome", ""),
                            row_data_dict.get("processo", ""),
                            row_data_dict.get("objeto", "Não informado"),
                            row_data_dict.get("valor_global", "Não informado"),
                            self._get_status_for_contrato(row_data_dict.get("id", "")) # Para "Status"
                        ]
                        writer.writerow(row_to_write)
                        
                QMessageBox.information(self.view, "Exportar Tabela", f"Tabela exportada com sucesso para:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.view, "Erro ao Exportar", f"Não foi possível salvar o arquivo CSV: {e}")

    # Funções auxiliares que você precisaria (ou adaptar das existentes em controller_table.py)
    def _calculate_dias_restantes(self, vigencia_fim_str):
        from datetime import date, datetime # Mover imports para o topo do arquivo
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                return (vigencia_fim - date.today()).days
            except ValueError:
                return "Erro Data"
        return "Sem Data"

    def _get_status_for_contrato(self, contrato_id):
        # Lógica similar à de controller_table.py para buscar o status do DB
        if contrato_id and self.model:
            try:
                conn = self.model._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT status FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
                status_row = cursor.fetchone()
                conn.close()
                if status_row and status_row['status']:
                    return status_row['status']
            except sqlite3.Error:
                return "Erro DB"
        return "SEÇÃO CONTRATOS"

    def set_pdf_download_folder(self):
        """Permite ao usuário definir a pasta de download para PDFs."""
        current_path = self.model.load_setting("pdf_download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
        
        folder_path = QFileDialog.getExistingDirectory(
            self.view,
            "Selecionar Pasta para Salvar PDFs",
            current_path
        )
        if folder_path:
            self.model.save_setting("pdf_download_path", folder_path)
            QMessageBox.information(self.view, "Pasta Definida", f"Os PDFs serão salvos em:\n{folder_path}")