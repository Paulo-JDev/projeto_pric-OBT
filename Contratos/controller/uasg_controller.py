import os
from Contratos.view.main_window import MainWindow
from Contratos.model.uasg_model import UASGModel
from utils.utils import refresh_uasg_menu
from utils.icon_loader import icon_manager

from Contratos.view.details_dialog import DetailsDialog
from Contratos.view.menus.status_options_dialog import StatusOptionsDialog
from Contratos.view.record_popup import RecordPopup

from Contratos.controller.controller_table import populate_table, update_row_from_details
from Contratos.controller.mensagem_controller import MensagemController
from Contratos.controller.settings_controller import SettingsController
from Contratos.controller.manual_contract_controller import ManualContractController
from Contratos.controller.exp_imp_table_controller import ExpImpTableController

from PyQt6.QtWidgets import QMessageBox, QMenu, QFileDialog, QApplication, QHeaderView
from PyQt6.QtGui import QStandardItem, QFont, QColor, QBrush
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
import requests
import sqlite3
import json
from datetime import datetime
import re
import shutil

class UASGController:
    def __init__(self, base_dir, parent_view=None): 
        from .dashboard_controller import DashboardController

        self.model = UASGModel(base_dir)

        # --- CHAMADA DA LIMPEZA AUTOMÁTICA ---
        self.model.archive_and_delete_expired_contracts()
        
        # 1. Define dados iniciais (Single Source of Truth)
        self.current_data = [] 
        self.loaded_uasgs = {}
        
        # 2. Define placeholder para evitar AttributeError na View
        self.table_controller = None
        
        # 3. Cria a View (que vai tentar conectar os botões)
        self.view = MainWindow(self) 
        
        # 4. Inicializa controllers filhos (passando self)
        self.dashboard_controller = DashboardController(self.model, self.view)
        self.manual_contract_ctrl = ManualContractController(self.model, self.view)
        
        # 5. Inicializa o controller de tabelas real
        self.table_controller = ExpImpTableController(self)
        
        self.view.settings_button.clicked.connect(self.show_settings_dialog)
        self.view.table.doubleClicked.connect(self._open_details_from_double_click)

        initial_mode = self.model.load_setting("data_mode", "Online")
        self.view.update_status_icon(initial_mode)
        self.view.update_clear_button_icon(initial_mode)

        if self.model.database_dir.exists():
            self.loaded_uasgs = self.model.load_saved_uasgs()
            print(f"📂 UASGs do módulo Contratos carregadas: {list(self.loaded_uasgs.keys())}")
        else:
            print("⚠ Diretório 'database' não encontrado. Nenhum dado de Contratos carregado.")

        self.load_saved_uasgs()
        self.populate_previsualization_table()

    # ==================== SINGLE SOURCE OF TRUTH ====================
    def get_current_data(self):
        """Retorna a referência atual dos dados exibidos."""
        return self.current_data

    def get_loaded_uasgs(self):
        """Retorna o dicionário de todas as UASGs carregadas."""
        return self.loaded_uasgs
    
    def _open_details_from_double_click(self, index):
        if not index.isValid():
            return

        # A tabela usa proxy model (por causa da busca)
        proxy_model = self.view.table.model()
        source_index = proxy_model.mapToSource(index)
        row = source_index.row()

        if 0 <= row < len(self.current_data):
            contrato = self.current_data[row]
            self.show_details_dialog(contrato.copy())

    # ==================== WRAPPER PARA A VIEW ====================
    def open_table_options(self):
        """A View chama este método, garantindo que o controller exista."""
        if self.table_controller:
            self.table_controller.open_table_options_window()
        else:
            QMessageBox.warning(self.view, "Erro", "Controlador de tabela não inicializado.")

    # ==================== LÓGICA GERAL ====================
    def open_status_options_window(self):
        dialog = StatusOptionsDialog(self.view)
        dialog.btn_export_status.clicked.connect(self.export_status_data)
        dialog.btn_import_status.clicked.connect(self.import_status_data)
        dialog.exec()

    def load_saved_uasgs(self):
        """Carrega as UASGs salvas e atualiza o menu."""
        self.loaded_uasgs = self.model.load_saved_uasgs()
        refresh_uasg_menu(self)  # Atualiza o menu após carregar as UASGs

    def add_uasg_to_menu(self, uasg):
        """Adiciona uma UASG ao menu suspenso."""
        action = self.view.menu_button.menu().addAction(f"UASG {uasg}", lambda: self.update_table(uasg))

    def open_status_options_window(self):
        """Abre a mini janela com opções de Status."""
        dialog = StatusOptionsDialog(self.view)
        dialog.btn_export_status.clicked.connect(self.export_status_data)
        dialog.btn_import_status.clicked.connect(self.import_status_data)
        dialog.exec()

    def fetch_and_create_table(self):
        """Busca os dados da UASG e atualiza o banco de dados."""
        uasg = self.view.uasg_input.text().strip()

        # Verificação se a UASG está vazia ou contém caracteres não numéricos
        if not uasg or not uasg.isdigit():
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número UASG válido.")
            return

        try:
            if uasg in self.loaded_uasgs and self.loaded_uasgs[uasg]: # Verifica se há dados carregados
                QMessageBox.information(self.view, "Sucesso", f"UASG {uasg} carregada e salva com sucesso!")
                self.view.uasg_input.clear()
            else:
                # Se for nova, buscar e salvar
                data = self.model.fetch_uasg_data(uasg)
                if data is None:
                    QMessageBox.critical(self.view, "Erro de API", f"Erro ao buscar dados da UASG {uasg}.")
                    return

                self.model.save_uasg_data(uasg, data)
                self.loaded_uasgs[uasg] = data
                self.add_uasg_to_menu(uasg)
                #QMessageBox.information(self.view, "Sucesso", f"UASG {uasg} carregada e salva com sucesso!")
                self.view.tabs.setCurrentWidget(self.view.table_tab)
                self.populate_previsualization_table()
                
                # time.sleep(1) # Considere remover ou usar QStatusBar
                self.view.uasg_input.clear()

            self.loaded_uasgs = self.model.load_saved_uasgs()

            self.update_table(uasg)
            self.view.tabs.setCurrentWidget(self.view.table_tab)
        except requests.exceptions.RequestException as e: # Exceção mais específica
            QMessageBox.critical(self.view, "Erro de Rede", f"Erro de rede ao buscar UASG {uasg}: {str(e)}")
        except Exception as e: # Genérico para outros erros
            QMessageBox.critical(self.view, "Erro Inesperado", f"Erro inesperado ao processar UASG {uasg}: {str(e)}")

    def delete_uasg_data(self):
        """Deleta os dados da UASG informada e limpa a tabela se ela estiver em uso."""
        uasg_para_deletar = self.view.uasg_input.text().strip()
        if not uasg_para_deletar:
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número UASG para deletar.")
            return

        if uasg_para_deletar not in self.loaded_uasgs:
            QMessageBox.warning(self.view, "Erro", f"Nenhum dado encontrado para a UASG {uasg_para_deletar}.")
            return

        info_label_text = self.view.uasg_info_label.text()
        
        # Extrai o código da UASG que está sendo exibida na tabela
        uasg_sendo_exibida = ""
        if "UASG: " in info_label_text:
            # Pega a parte depois de "UASG: " e antes do primeiro espaço
            partes = info_label_text.split(" ")
            if len(partes) > 1:
                uasg_sendo_exibida = partes[1]

        # Compara a UASG a ser deletada com a que está na tela
        if uasg_para_deletar == uasg_sendo_exibida:
            self.view.search_bar.clear()
            model = self.view.table.model()
            model.removeRows(0, model.rowCount())
            self.view.uasg_info_label.setText("UASG: -")
            print(f"Limpando a tabela, pois a UASG {uasg_para_deletar} está sendo visualizada.")
            
        
        # Procede com a deleção dos dados do banco de dados
        self.model.delete_uasg_data(uasg_para_deletar)
        self.loaded_uasgs.pop(uasg_para_deletar, None)
        
        # Atualiza o menu de UASGs e limpa o campo de input
        self.load_saved_uasgs()
        self.view.uasg_input.clear()
        
        QMessageBox.information(self.view, "Sucesso", f"UASG {uasg_para_deletar} deletada com sucesso.")

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
                self.dashboard_controller.update_dashboard(self.current_data)
                print(f"✅ Tabela atualizada com os dados da UASG {uasg}.")
            else:
                # Limpa o label se não houver dados
                self.view.uasg_info_label.setText(f"UASG: -")
                print(f"⚠ UASG {uasg} não encontrada nos dados recarregados(especifico).")
        else:
            # Limpa o label se a UASG não for encontrada
            self.view.uasg_info_label.setText(f"UASG: -")
            print(f"⚠ UASG {uasg} não encontrada nos dados carregados(geral).")
        self.load_saved_uasgs()

    def clear_table(self):
        # Verifica se há dados carregados
        if not self.current_data or len(self.current_data) == 0:
            QMessageBox.warning(
                self.view,
                "Nenhuma UASG Carregada",
                "Não há contratos carregados no momento.\n\n"
                "Por favor, busque uma UASG antes de atualizar a tabela."
            )
            return
        
        # Pega o código da UASG do primeiro contrato carregado
        primeiro_contrato = self.current_data[0]
        uasg_code = primeiro_contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo")
        
        if not uasg_code:
            QMessageBox.warning(
                self.view,
                "UASG Não Identificada",
                "Não foi possível identificar a UASG dos contratos carregados."
            )
            return
        
        try:
            print(f"🔄 Recarregando tabela da UASG {uasg_code}...")
            
            # ==================== ✅ USA O MÉTODO update_table ====================
            self.update_table(uasg_code)
            
            # Mensagem de sucesso
            QMessageBox.information(
                self.view, 
                "Atualização Concluída", 
                f"Tabela da UASG {uasg_code} recarregada com sucesso!\n\n"
                f"Total de contratos: {len(self.current_data)}"
            )
            
            print(f"✅ Tabela recarregada: {len(self.current_data)} contratos")
            
        except Exception as e:
            QMessageBox.critical(
                self.view,
                "Erro ao Atualizar",
                f"Erro ao recarregar a tabela:\n{str(e)}"
            )
            print(f"❌ Erro ao recarregar tabela: {e}")

    def show_context_menu(self, position):
        """
        ✅ ATUALIZADO: Exibe o menu de contexto ao clicar com o botão direito na tabela.
        Adiciona a opção de excluir apenas para contratos manuais, seguindo o modelo existente.
        """
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
            menu = QMenu(self.view) # O parent do menu é a view principal

            # Adiciona o ícone "init" à ação "Ver Detalhes"
            details_action = menu.addAction(icon_manager.get_icon("init"), "Ver Detalhes") # ✅ Usei "detalhes" para o ícone, se "init" for um ícone válido, pode manter.
            details_action.triggered.connect(lambda: self.show_details_dialog(contrato.copy())) # ✅ Usando .copy() para segurança

            # ==================== ✅ ADICIONA OPÇÃO DE EXCLUIR SE FOR MANUAL ====================
            is_manual = contrato.get("manual", False)
            if is_manual:
                menu.addSeparator() # Adiciona um separador para organizar
                
                delete_action = menu.addAction(icon_manager.get_icon("delete"), "Excluir Contrato Manual")
                delete_action.triggered.connect(lambda: self._delete_manual_contract(contrato.copy(), row)) # ✅ Usando .copy() para segurança
            
            # Exibe o menu na posição do cursor
            menu.exec(self.view.table.viewport().mapToGlobal(position))
            # Não adicionamos deleteLater() ou WA_DeleteOnClose aqui,
            # confiando no comportamento padrão do QMenu.exec() e no gerenciamento de memória do Qt.

    def _delete_manual_contract(self, contrato_data, row):
        """
        ✅ NOVO MÉTODO: Exclui um contrato manual do banco de dados.
        Simplificado e focado na funcionalidade principal.
        """
        from Contratos.model.models import Contrato, StatusContrato, RegistroStatus, LinksContrato, Fiscalizacao
        
        contrato_id = contrato_data.get("id")
        contrato_numero = contrato_data.get("numero", "N/A")
        uasg_code = contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo")
        
        # ==================== CONFIRMAÇÃO ====================
        reply = QMessageBox.question(
            self.view, # Usando self.view como parent para a QMessageBox
            "Confirmar Exclusão",
            f"⚠️ Tem certeza que deseja excluir o contrato manual?\n\n"
            f"Número: {contrato_numero}\n"
            f"ID: {contrato_id}\n"
            f"UASG: {uasg_code}\n\n"
            f"❌ Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # ==================== EXCLUSÃO DO BANCO ====================
        db = self.model._get_db_session()
        
        try:
            # 1. Busca o contrato no banco
            contrato_db = db.query(Contrato).filter(Contrato.id == contrato_id).first()
            
            if not contrato_db:
                QMessageBox.warning(self.view, "Contrato Não Encontrado", f"O contrato {contrato_id} não foi encontrado no banco de dados.")
                return
            
            # 2. Deleta registros relacionados (garantindo a integridade)
            db.query(StatusContrato).filter(StatusContrato.contrato_id == contrato_id).delete(synchronize_session=False)
            db.query(RegistroStatus).filter(RegistroStatus.contrato_id == contrato_id).delete(synchronize_session=False)
            db.query(LinksContrato).filter(LinksContrato.contrato_id == contrato_id).delete(synchronize_session=False)
            db.query(Fiscalizacao).filter(Fiscalizacao.contrato_id == contrato_id).delete(synchronize_session=False)
            
            # 3. Deleta o contrato principal
            db.delete(contrato_db)
            db.commit()
            
            print(f"✅ Contrato manual {contrato_id} excluído com sucesso")
            
            # ==================== ATUALIZA A INTERFACE ====================
            # Remove da lista de dados atuais
            if row < len(self.current_data):
                self.current_data.pop(row)
            
            # Remove da tabela (usando o modelo da tabela)
            model = self.view.table.model()
            if model:
                model.removeRow(row)
            
            # Atualiza o dashboard (se houver um dashboard_controller)
            if hasattr(self, 'dashboard_controller'):
                self.dashboard_controller.update_dashboard(self.current_data)
            
            QMessageBox.information(
                self.view,
                "Exclusão Concluída",
                f"✅ Contrato manual {contrato_numero} excluído com sucesso!"
            )
            
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self.view, "Erro ao Excluir", f"❌ Erro ao excluir o contrato manual:\n\n{str(e)}")
            print(f"❌ Erro ao excluir contrato manual: {e}")
        finally:
            db.close()

    def show_details_dialog(self, contrato):
        """Exibe o diálogo de detalhes do contrato."""
        details_dialog = DetailsDialog(contrato, self.model, self.view) # Passa self.model
        details_dialog.data_saved.connect(self.update_table_from_details)
        details_dialog.exec()

    def update_table_from_details(self, details_info):
        """Atualiza a tabela quando os dados são salvos na DetailsDialog."""
        update_row_from_details(self, details_info)
        self.populate_previsualization_table()
    
    # =========================================== Método para abrir a janela de mensagens =================================================
    def show_msg_dialog(self):
        """
        Abre a janela de geração de mensagens para o contrato selecionado.
        """
        # Pega o índice da linha selecionada na tabela
        selected_indexes = self.view.table.selectionModel().selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self.view, "Nenhum Contrato Selecionado", "Por favor, selecione um contrato na tabela antes de clicar em Mensagens.")
            return

        # Pega o índice real da fonte de dados
        source_index = self.view.table.model().mapToSource(selected_indexes[0])
        selected_row = source_index.row()
        
        # Pega os dados do contrato selecionado
        contract_data = self.current_data[selected_row]
        
        # Cria e exibe a nova janela de mensagens
        mensagem_controller = MensagemController(contract_data, self.model, parent=self.view)
        mensagem_controller.show()

    # =========================================== Método para abrir a janela de configurações =================================================
    def show_settings_dialog(self):
        """Abre a janela de configurações e conecta o sinal de mudança de modo."""
        settings_controller = SettingsController(self.model, self.view)
        settings_controller.mode_changed.connect(self.view.update_status_icon)
        settings_controller.mode_changed.connect(self.view.update_clear_button_icon)
        settings_controller.database_updated.connect(self.load_saved_uasgs)
        settings_controller.database_updated.connect(self._on_database_updated)
        settings_controller.show()

    # =========================================== Método para exportar e importar dados de status =================================================
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
                self.populate_previsualization_table()
            except json.JSONDecodeError:
                QMessageBox.critical(self.view, "Erro de Importação", "Arquivo JSON inválido ou corrompido.")
            except Exception as e:
                QMessageBox.critical(self.view, "Erro ao Importar", f"Não foi possível importar os dados: {e}")

    # ==================== MÉTODOS PARA AUTOMAÇÃO (SILENCIOSOS) ====================

    def export_status_to_path(self, file_path):
        """Exporta status para um caminho específico sem abrir diálogo."""
        all_status_data = self.model.get_all_status_data()
        if all_status_data:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_status_data, f, ensure_ascii=False, indent=4)
            return True
        return False

    def import_status_from_path(self, file_path):
        """Importa status de um caminho específico sem abrir diálogo."""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.model.import_statuses(data)
            self.load_saved_uasgs()
            self.populate_previsualization_table()
            return True
        return False

    def export_manual_contracts_to_path(self, file_path):
        """Chama o ManualContractController para exportar contratos manuais para um path."""
        # Supondo que seu ManualContractController tenha ou precise desta lógica:
        return self.manual_contract_ctrl.export_to_path(file_path)

    def import_manual_contracts_from_path(self, file_path):
        """Chama o ManualContractController para importar contratos manuais de um path."""
        return self.manual_contract_ctrl.import_from_path(file_path)

# =========================================== Método para exportar a tabela para um arquivo Excel =================================================
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

    '''def set_pdf_download_folder(self):
        """Permite ao usuário definir a pasta de download para PDFs."""
        current_path = self.model.load_setting("pdf_download_path", os.path.join(os.path.expanduser("~"), "Downloads"))
        
        folder_path = QFileDialog.getExistingDirectory(
            self.view,
            "Selecionar Pasta para Salvar PDFs",
            current_path
        )
        if folder_path:
            self.model.save_setting("pdf_download_path", folder_path)
            QMessageBox.information(self.view, "Pasta Definida", f"Os PDFs serão salvos em:\n{folder_path}")'''
    
    # ======================================== Funções da Tabela-de-Pré-Visualização ==============================================================
    def populate_previsualization_table(self):
        """Busca os contratos com status diferente de 'SEÇÃO CONTRATOS' e popula a tabela de pré-visualização."""
        data = self.model.get_contracts_with_status_not_default()
        self.view.populate_preview_table(data)

    def show_records_popup(self, index):
        """Busca os registros de um contrato e os exibe em uma janela popup."""
        if not index.isValid():
            return

        proxy_model = self.view.preview_table.model()
        source_index = proxy_model.mapToSource(index)
        
        first_item = proxy_model.sourceModel().item(source_index.row(), 0)
        contrato_id = first_item.data(Qt.ItemDataRole.UserRole) if first_item else None

        if not contrato_id:
            print(f"Aviso: Não foi possível obter o ID do contrato para a linha {source_index.row()}.")
            return

        registros = []
        try:
            conn = self.model._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (contrato_id,))
            registros = [row['texto'] for row in cursor.fetchall()]
            conn.close()
        except sqlite3.Error as e:
            print(f"Erro ao buscar registros do DB: {e}")
            registros = ["Erro ao buscar registros."]

        # Passa o contrato_id para o popup e conecta o sinal ao novo método
        popup = RecordPopup(registros, contrato_id, self.view)
        popup.details_requested.connect(self.open_details_by_id)
        
        popup.move(self.view.cursor().pos())
        popup.exec()

    def open_details_by_id(self, contrato_id):
        """
        Encontra um contrato pelo seu ID em todas as UASGs carregadas
        e abre a janela de detalhes para ele.
        """
        contract_data_found = None
        # Procura o contrato em todos os dados carregados na aplicação
        for uasg_code, contracts_list in self.loaded_uasgs.items():
            for contract in contracts_list:
                # Compara o ID como string para garantir a correspondência
                if str(contract.get('id')) == contrato_id:
                    contract_data_found = contract
                    break
            if contract_data_found:
                break

        if contract_data_found:
            self.show_details_dialog(contract_data_found)
        else:
            QMessageBox.warning(self.view, "Erro", f"Não foi possível encontrar os dados completos para o contrato ID: {contrato_id}")

# ====================== Contratos Manuais ==========================
    def open_manual_contract_window(self):
            """Abre a janela de contratos manuais"""
            self.manual_contract_ctrl.open_manual_contract_window()

# ====================== Banco de Dados (settings) ==========================

    def _on_database_updated(self):
        """
        ✅ NOVO MÉTODO: Chamado quando o banco de dados é alterado nas configurações.
        
        Recarrega os dados e atualiza a interface automaticamente.
        """
        print("🔄 Banco de dados alterado, recarregando dados...")
        
        # 1. Recarrega as UASGs salvas do novo banco
        self.loaded_uasgs = self.model.load_saved_uasgs()
        
        # 2. Atualiza o menu de UASGs
        self.load_saved_uasgs()
        
        # 3. Atualiza a tabela de pré-visualização
        self.populate_previsualization_table()
        
        # 4. Se houver dados carregados na tabela principal, atualiza
        if self.current_data and len(self.current_data) > 0:
            primeiro_contrato = self.current_data[0]
            uasg_code = primeiro_contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo")
            
            if uasg_code:
                # Verifica se a UASG ainda existe no novo banco
                if uasg_code in self.loaded_uasgs:
                    print(f"✅ Atualizando tabela da UASG {uasg_code}")
                    self.update_table(uasg_code)
                else:
                    # Se a UASG não existe mais, limpa a tabela
                    print(f"⚠️ UASG {uasg_code} não encontrada no novo banco, limpando tabela")
                    model = self.view.table.model()
                    if model:
                        model.removeRows(0, model.rowCount())
                    self.view.uasg_info_label.setText("UASG: -")
                    self.current_data = []
                    self.dashboard_controller.clear_dashboard()
        
        print("✅ Dados recarregados com sucesso!")
