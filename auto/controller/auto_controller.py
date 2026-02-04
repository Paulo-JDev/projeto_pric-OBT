# auto/controller/auto_controller.py

import os
import pathlib
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from auto.model.auto_model import AutoModel
from auto.view.auto_dialog import AutoDialog
from Contratos.model.database import init_database

from integration.controller.trello_controller import TrelloController
from integration.model.trello_model import TrelloModel

class AutoController:
    def __init__(self, parent_view, base_dir, contratos_controller):
        self.model = AutoModel(base_dir)
        self.view = AutoDialog(parent_view)
        self.contratos_controller = contratos_controller
        self.base_dir = base_dir
        
    def show(self):
        # 1. Instanciamos o Model do Trello
        trello_model = TrelloModel()
        
        # 2. Instanciamos o Controller do Trello PASSANDO a aba que está dentro da view
        # e o controlador de contratos
        self.trello_integration = TrelloController(
            self.view.trello_tab, 
            trello_model, 
            self.contratos_controller
        )
        
        # 3. Conecta o botão de banco de dados (que pertence a este AutoController)
        self.view.btn_start_db_auto.clicked.connect(self.run_database_automation)
        
        # 4. Exibe a janela
        self.view.exec()

    def run_database_automation(self):
        # 1. Selecionar o novo arquivo .db
        new_db, _ = QFileDialog.getOpenFileName(
            self.view, "Selecione o NOVO Banco de Dados baixado", "", "SQLite Files (*.db)"
        )
        if not new_db: return

        self.view.set_loading_state(True)
        self.view.clear_log()

        try:
            # --- PASSO 1: Preparação ---
            self.view.log("Criando ambiente temporário...")
            temp_path = self.model.create_temp_folder()
            status_file = os.path.join(temp_path, "status_auto.json")
            manual_file = os.path.join(temp_path, "manual_auto.json")

            # --- PASSO 2: Exportação Preventiva ---
            self.view.log("Exportando Status e Contratos Manuais atuais...")
            self.contratos_controller.export_status_to_path(status_file)
            self.contratos_controller.export_manual_contracts_to_path(manual_file)

            # --- PASSO 3: Backup de Segurança ---
            self.view.log("Gerando backup de segurança do sistema...")
            # Aqui você pode instanciar o BackupModel e chamar perform_backup
            from backup.model.backup_model import BackupModel
            bkp_model = BackupModel()
            dest_bkp = bkp_model.get_backup_location()
            if dest_bkp:
                bkp_model.perform_backup(dest_bkp, True, True)
                self.view.log(f"Backup local salvo em: {dest_bkp}")

            # --- PASSO 4: Troca da Base ---
            self.view.log("Encerrando conexões com o banco de dados...")
            
            # 1. Comando crucial para liberar o arquivo no SQLAlchemy
            from Contratos.model.database import engine
            if engine:
                engine.dispose() 
            
            self.view.log("Substituindo arquivo de Banco de Dados...")
            current_db_path = os.path.join(self.base_dir, "database", "gerenciador_uasg.db")
            
            # Tentativa de substituição com tratamento de erro específico para arquivo travado
            try:
                self.model.replace_database(new_db, current_db_path)
            except PermissionError:
                self.view.log("❌ ERRO: O arquivo ainda está travado pelo sistema.")
                QMessageBox.critical(self.view, "Erro de Permissão", 
                    "Não foi possível substituir o banco. O arquivo 'gerenciador_uasg.db' está sendo usado por outro processo.\n\n"
                    "Tente fechar o programa e abrir novamente, ou verifique se o Gerenciador de Tarefas tem algum processo Python pendente.")
                return

            # --- PASSO 5: Reinicialização e Restauração ---
            self.view.log("Conectando à nova base e restaurando dados preservados...")
            init_database(pathlib.Path(current_db_path)) # Reinicia SQLAlchemy
            
            # Importa de volta os dados que salvamos no Passo 2
            self.contratos_controller.import_manual_contracts_from_path(manual_file)
            self.contratos_controller.import_status_from_path(status_file)

            # --- PASSO 6: Limpeza e Atualização ---
            self.view.log("Limpando arquivos temporários...")
            self.model.clean_temp_folder()
            
            # Atualiza a interface principal para mostrar os novos dados
            self.contratos_controller._on_database_updated()
            
            self.view.log("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
            QMessageBox.information(self.view, "Automação", "Banco de dados atualizado com sucesso e todos os dados foram preservados.")

        except Exception as e:
            self.view.log(f"❌ ERRO CRÍTICO: {str(e)}")
            QMessageBox.critical(self.view, "Falha na Automação", f"Ocorreu um erro inesperado:\n{e}")
        finally:
            self.view.set_loading_state(False)