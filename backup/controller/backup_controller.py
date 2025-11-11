import os
import subprocess
import sys
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from pathlib import Path
from backup.model.backup_model import BackupModel
from backup.view.backup_dialog import BackupDialog


class BackupController:
    """
    Controlador para a janela de Backup.
    """
    def __init__(self, parent_view=None):
        self.model = BackupModel()
        self.view = BackupDialog(parent_view)
        self.parent_view = parent_view # Guardar referência da janela principal
        
        # Carregar o caminho de backup salvo
        self.load_saved_path()
        
        # Conectar os sinais (botões) aos métodos (slots)
        self_signals = self.view
        self_signals.select_path_button.clicked.connect(self.select_backup_path)
        self_signals.btn_disparar_backup.clicked.connect(self.run_backup)
        self_signals.btn_abrir_local.clicked.connect(self.open_backup_path)

    def show(self):
        """Exibe a janela de diálogo."""
        self.view.exec()

    def load_saved_path(self):
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

    def select_backup_path(self):
        """Abre um diálogo para o usuário selecionar uma pasta de backup."""
        current_path = self.model.get_backup_location() or str(Path.home())
        
        path = QFileDialog.getExistingDirectory(
            self.view,
            "Selecione a Pasta de Destino do Backup",
            current_path
        )
        
        if path:
            self.model.save_backup_location(path)
            self.load_saved_path() # Atualiza o label

    def run_backup(self):
        """Valida e executa o processo de backup."""
        dest_path = self.model.get_backup_location()
        if not dest_path or not os.path.exists(dest_path):
            QMessageBox.warning(self.view, "Local Inválido",
                                "Por favor, selecione uma pasta de destino válida primeiro.")
            return

        backup_contratos = self.view.check_contratos.isChecked()
        backup_atas = self.view.check_atas.isChecked()

        if not backup_contratos and not backup_atas:
            QMessageBox.warning(self.view, "Nada a Fazer",
                                "Selecione pelo menos um módulo (Contratos ou Atas) para fazer backup.")
            return

        try:
            self.view.btn_disparar_backup.setEnabled(False)
            self.view.btn_disparar_backup.setText("Copiando...")
            QApplication.processEvents() # Atualiza a UI

            success, message = self.model.perform_backup(dest_path, backup_contratos, backup_atas)
            
            if success:
                QMessageBox.information(self.view, "Sucesso", message)
            else:
                QMessageBox.warning(self.view, "Aviso", message)

        except Exception as e:
            QMessageBox.critical(self.view, "Erro Inesperado",
                                 f"Ocorreu um erro inesperado:\n{e}")
        finally:
            self.view.btn_disparar_backup.setEnabled(True)
            self.view.btn_disparar_backup.setText("Disparar Backup")

    def open_backup_path(self):
        """Abre a pasta de backup no explorador de arquivos do usuário."""
        path = self.model.get_backup_location()
        if path and os.path.exists(path):
            try:
                # Método multiplataforma para abrir um explorador de arquivos
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
