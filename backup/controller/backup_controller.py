import os
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QApplication, QLineEdit
from backup.model.backup_model import BackupModel
from backup.view.backup_dialog import BackupDialog
from utils.icon_loader import icon_manager # Importar para o ícone de e-mail

class BackupController:
    """
    Controlador para a janela de Backup (Local e Online).
    """
    def __init__(self, parent_view=None):
        self.model = BackupModel()
        self.view = BackupDialog(parent_view)
        self.parent_view = parent_view
        
        # Carregar os caminhos salvos (local e email)
        self._load_initial_data()
        
        # Conectar os sinais (botões) aos métodos (slots)
        
        # Aba Local
        self.view.select_path_button.clicked.connect(self.select_backup_path)
        self.view.btn_disparar_backup.clicked.connect(self.run_local_backup)
        self.view.btn_abrir_local.clicked.connect(self.open_backup_path)

        # Aba Online
        self.view.btn_definir_email.clicked.connect(self.define_backup_email)
        self.view.btn_disparar_backup_online.clicked.connect(self.run_online_backup)

    def show(self):
        """Exibe a janela de diálogo."""
        self.view.exec()

    def _load_initial_data(self):
        """Carrega e exibe os locais salvos para backup local e online."""
        self._load_saved_local_path()
        self._load_saved_email()

    def _load_saved_local_path(self):
        """Carrega e exibe o local de backup salvo no config.json."""
        path = self.model.get_backup_location()
        if path and os.path.exists(path):
            self.view.path_label.setText(path)
            self.view.path_label.setStyleSheet("color: #8AB4F7;") # Cor do tema
            self.view.btn_abrir_local.setEnabled(True)
        else:
            self.view.path_label.setText("Nenhum local selecionado.")
            self.view.path_label.setStyleSheet("color: #aaa; font-style: italic;")
            self.view.btn_abrir_local.setEnabled(False)

    def _load_saved_email(self):
        """Carrega e exibe o e-mail de backup salvo."""
        email = self.model.get_backup_email()
        if email:
            self.view.email_label.setText(email)
            self.view.email_label.setStyleSheet("color: #8AB4F7;")
        else:
            self.view.email_label.setText("Nenhum e-mail de destino definido.")
            self.view.email_label.setStyleSheet("color: #aaa; font-style: italic;")

    def select_backup_path(self):
        """Abre um diálogo para o usuário selecionar uma pasta de backup local."""
        current_path = self.model.get_backup_location() or str(Path.home())
        
        path = QFileDialog.getExistingDirectory(
            self.view, "Selecione a Pasta de Destino do Backup", current_path
        )
        
        if path:
            self.model.save_backup_location(path)
            self._load_saved_local_path() # Atualiza o label

    def define_backup_email(self):
        """Abre um QInputDialog para o usuário definir o e-mail de destino."""
        current_email = self.model.get_backup_email()
        
        new_email, ok = QInputDialog.getText(
            self.view,
            "Definir E-mail de Backup",
            "Digite o e-mail de destino para o backup online:",
            QLineEdit.EchoMode.Normal,
            current_email
        )
        
        if ok and new_email:
            # Uma verificação simples de e-mail (pode ser melhorada)
            if "@" in new_email and "." in new_email:
                self.model.save_backup_email(new_email)
                self._load_saved_email()
            else:
                QMessageBox.warning(self.view, "E-mail Inválido",
                                    f"O endereço '{new_email}' não parece ser um e-mail válido.")

    def run_local_backup(self):
        """Valida e executa o processo de backup LOCAL."""
        dest_path = self.model.get_backup_location()
        if not dest_path or not os.path.exists(dest_path):
            QMessageBox.warning(self.view, "Local Inválido",
                                "Por favor, selecione uma pasta de destino válida primeiro.")
            return

        # Lê os checkboxes globais
        backup_contratos = self.view.check_contratos.isChecked()
        backup_atas = self.view.check_atas.isChecked()

        if not backup_contratos and not backup_atas:
            QMessageBox.warning(self.view, "Nada a Fazer",
                                "Selecione pelo menos um módulo (Contratos ou Atas) para fazer backup.")
            return

        try:
            self.view.btn_disparar_backup.setEnabled(False)
            self.view.btn_disparar_backup.setText("Copiando...")
            QApplication.processEvents()

            success, message = self.model.perform_backup(dest_path, backup_contratos, backup_atas)
            
            if success:
                QMessageBox.information(self.view, "Sucesso", message)
            else:
                QMessageBox.warning(self.view, "Aviso", message)

        except Exception as e:
            QMessageBox.critical(self.view, "Erro Inesperado", f"Ocorreu um erro:\n{e}")
        finally:
            self.view.btn_disparar_backup.setEnabled(True)
            self.view.btn_disparar_backup.setText("Disparar Backup Local")

    def run_online_backup(self):
        """Valida e executa o processo de backup ONLINE (E-mail)."""
        email_dest = self.model.get_backup_email()
        if not email_dest:
            QMessageBox.warning(self.view, "E-mail Não Definido",
                                "Por favor, defina um e-mail de destino primeiro.")
            return
            
        # Lê os checkboxes globais
        backup_contratos = self.view.check_contratos.isChecked()
        backup_atas = self.view.check_atas.isChecked()

        if not backup_contratos and not backup_atas:
            QMessageBox.warning(self.view, "Nada a Fazer",
                                "Selecione pelo menos um módulo (Contratos ou Atas) para fazer backup.")
            return

        # Confirmação
        reply = QMessageBox.question(
            self.view,
            "Confirmar Envio",
            f"Você está prestes a enviar o backup para:\n\n{email_dest}\n\n"
            "Isso pode levar alguns segundos. Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return

        try:
            self.view.btn_disparar_backup_online.setEnabled(False)
            self.view.btn_disparar_backup_online.setText("Enviando...")
            QApplication.processEvents()

            success, message = self.model.perform_online_backup(email_dest, backup_contratos, backup_atas)
            
            if success:
                QMessageBox.information(self.view, "Sucesso", message)
            else:
                QMessageBox.critical(self.view, "Falha no Envio", message)

        except Exception as e:
            QMessageBox.critical(self.view, "Erro Inesperado", f"Ocorreu um erro:\n{e}")
        finally:
            self.view.btn_disparar_backup_online.setEnabled(True)
            self.view.btn_disparar_backup_online.setText("Disparar Backup Online")

    def open_backup_path(self):
        """Abre a pasta de backup local no explorador de arquivos."""
        path = self.model.get_backup_location()
        if path and os.path.exists(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin": # macOS
                    subprocess.Popen(["open", path])
                else: # Linux
                    subprocess.Popen(["xdg-open", path])
            except Exception as e:
                QMessageBox.critical(self.view, "Erro", f"Não foi possível abrir a pasta:\n{e}")
        else:
            QMessageBox.warning(self.view, "Local Inválido",
                                "O local de backup não está definido ou não existe mais.")
