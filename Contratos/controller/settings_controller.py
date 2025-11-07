# Contratos/controller/settings_controller.py

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from Contratos.view.settings_dialog import SettingsDialog
from Contratos.model.offline_db_model import OfflineDBController
from pathlib import Path
import shutil


class SettingsController(QObject):
    mode_changed = pyqtSignal(str)
    database_updated = pyqtSignal()
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = SettingsDialog(parent)
        self.offline_db_model = OfflineDBController(parent_view=self.view)
        
        # Conecta os botões
        self.view.close_button.clicked.connect(self.view.close)
        self.view.mode_button.clicked.connect(self._toggle_data_mode)
        self.view.change_db_path_button.clicked.connect(self._change_db_path)  # ✅ ATUALIZADO
        self.view.create_db_button.clicked.connect(self.run_create_offline_db)
        self.view.delete_db_button.clicked.connect(self.run_delete_offline_db)
        
        self._load_initial_state()
    
    def show(self):
        """Exibe a janela."""
        self.view.exec()
    
    def _load_initial_state(self):
        """Lê o modo salvo, ajusta o botão e emite o sinal inicial."""
        self.current_mode = self.model.load_setting("data_mode", "Online")
        self._update_button_style()
        self.mode_changed.emit(self.current_mode)
        
        # ==================== ✅ CARREGA O CAMINHO ATUAL DO BANCO ====================
        current_db_path = self.model.get_current_db_path()
        self.view.db_path_label.setText(f"Caminho Atual: {current_db_path}")
    
    def _change_db_path(self):
        """
        ✅ SISTEMA REFINADO: Permite ao usuário alterar o local do banco de dados.
        
        Igual ao módulo de Atas, com opções de:
        - Usar banco existente
        - Copiar banco atual
        - Criar banco vazio
        """
        # Pega o caminho atual
        current_db_path = self.model.get_current_db_path()
        
        # Abre diálogo para escolher nova pasta
        new_folder = QFileDialog.getExistingDirectory(
            self.view,
            "Selecione a pasta para o banco de dados",
            str(current_db_path.parent)
        )
        
        if not new_folder:
            return
        
        new_folder = Path(new_folder)
        new_db_path = new_folder / "gerenciador_uasg.db"
        
        # ==================== VERIFICA SE JÁ EXISTE DB NO NOVO LOCAL ====================
        if new_db_path.exists():
            reply = QMessageBox.question(
                self.view,
                "Banco de Dados Existente",
                f"Já existe um banco de dados em:\n{new_db_path}\n\n"
                "Deseja usar este banco existente?\n\n"
                "• SIM: Usar o banco existente\n"
                "• NÃO: Copiar o banco atual para lá (substituindo)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.No:
                # Copia o banco atual para o novo local
                try:
                    shutil.copy2(current_db_path, new_db_path)
                    QMessageBox.information(
                        self.view, 
                        "Banco Copiado", 
                        f"Banco de dados copiado para:\n{new_db_path}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self.view, 
                        "Erro ao Copiar", 
                        f"Não foi possível copiar o banco:\n{e}"
                    )
                    return
        else:
            # ==================== BANCO NÃO EXISTE NO NOVO LOCAL ====================
            reply = QMessageBox.question(
                self.view,
                "Configurar Novo Local",
                f"O que deseja fazer?\n\n"
                f"• SIM: Copiar o banco atual para {new_folder}\n"
                f"• NÃO: Criar um banco vazio no novo local",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                # Copia o banco atual
                try:
                    shutil.copy2(current_db_path, new_db_path)
                except Exception as e:
                    QMessageBox.critical(
                        self.view, 
                        "Erro ao Copiar", 
                        f"Não foi possível copiar o banco:\n{e}"
                    )
                    return
        
        # ==================== ATUALIZA O CAMINHO NO MODELO ====================
        success = self.model.change_database_path(str(new_folder))
        
        if success:
            # Atualiza o label na interface
            self.view.db_path_label.setText(f"Caminho Atual: {new_db_path}")
            
            QMessageBox.information(
                self.view,
                "Sucesso",
                f"Banco de dados alterado para:\n{new_db_path}\n\n"
                "A configuração foi salva e será mantida nas próximas execuções.\n\n"
                "⚠️ Recomenda-se reiniciar a aplicação para garantir que todas as mudanças tenham efeito."
            )
            
            # Emite sinal para atualizar a interface principal
            self.database_updated.emit()
        else:
            QMessageBox.critical(
                self.view,
                "Erro",
                "Não foi possível alterar o local do banco de dados."
            )
    
    def _toggle_data_mode(self):
        """Alterna entre os modos Online e Offline e emite o sinal."""
        if self.current_mode == "Online":
            self.current_mode = "Offline"
        else:
            self.current_mode = "Online"
        
        self.model.save_setting("data_mode", self.current_mode)
        self._update_button_style()
        self.mode_changed.emit(self.current_mode)
    
    def _update_button_style(self):
        """Atualiza o texto e a cor do botão com base no modo."""
        if self.current_mode == "Online":
            self.view.mode_button.setText("Online")
            self.view.mode_button.setChecked(True)
            self.view.mode_button.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
        else:
            self.view.mode_button.setText("Offline")
            self.view.mode_button.setChecked(False)
            self.view.mode_button.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")
    
    def run_create_offline_db(self):
        """Inicia o processo de criação/atualização do banco de dados offline."""
        uasg = self.view.offline_uasg_input.text().strip()
        
        if not uasg.isdigit():
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número de UASG válido.")
            return
        
        reply = QMessageBox.question(
            self.view, 
            "Confirmação", 
            f"Deseja criar/atualizar o banco de dados offline para a UASG {uasg}?\n\n"
            "Isso pode levar alguns minutos dependendo da quantidade de contratos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.offline_db_model.process_and_save_all_data(uasg)
            QMessageBox.information(self.view, "Concluído", f"Banco de dados offline para UASG {uasg} criado/atualizado com sucesso.")
            self.database_updated.emit()
    
    def run_delete_offline_db(self):
        """Inicia o processo de exclusão de uma UASG do banco de dados offline."""
        uasg = self.view.offline_uasg_input.text().strip()
        
        if not uasg.isdigit():
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número de UASG válido.")
            return
        
        reply = QMessageBox.question(
            self.view, 
            "Confirmação de Exclusão", 
            f"Tem certeza que deseja apagar TODOS os dados da UASG {uasg} do banco de dados offline?\n\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.offline_db_model.delete_uasg_from_db(uasg)
            QMessageBox.information(self.view, "Concluído", f"Os dados da UASG {uasg} foram removidos.")
            self.database_updated.emit()
