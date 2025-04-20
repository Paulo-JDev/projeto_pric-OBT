from view.main_window import MainWindow
from model.uasg_model import UASGModel
from utils.utils import refresh_uasg_menu
from view.details_dialog import DetailsDialog
from controller.controller_table import populate_table, update_status_column
from utils.icon_loader import icon_manager

from PyQt6.QtWidgets import QMessageBox, QMenu
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
        details_dialog = DetailsDialog(contrato, self.view)
        
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
        msg_dialog = "Teste Paulo vitor"
        print(msg_dialog)

