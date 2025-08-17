from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtWidgets import QMessageBox
from view.settings_dialog import SettingsDialog
from model.offline_db_model import OfflineDBController

class SettingsController(QObject):
    mode_changed = pyqtSignal(str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = SettingsDialog(parent)

        self.offline_db_model = OfflineDBController(parent_view=self.view)

        self.view.close_button.clicked.connect(self.view.close)
        self.view.mode_button.clicked.connect(self._toggle_data_mode)
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
        
        reply = QMessageBox.question(self.view, "Confirmação", 
            f"Isso buscará todos os dados da UASG {uasg} pela internet e os salvará localmente. "
            f"O processo pode demorar vários minutos e irá sobrescrever os dados existentes para esta UASG.\n\nDeseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.offline_db_model.process_and_save_all_data(uasg)
            QMessageBox.information(self.view, "Concluído", f"A base de dados para a UASG {uasg} foi criada/atualizada com sucesso.")

    def run_delete_offline_db(self):
        """Inicia o processo de exclusão de uma UASG do banco de dados offline."""
        uasg = self.view.offline_uasg_input.text().strip()
        if not uasg.isdigit():
            QMessageBox.warning(self.view, "Entrada Inválida", "Por favor, insira um número de UASG válido.")
            return

        reply = QMessageBox.question(self.view, "Confirmação de Exclusão", 
            f"Tem certeza que deseja apagar TODOS os dados da UASG {uasg} do banco de dados offline?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.offline_db_model.delete_uasg_from_db(uasg)
            QMessageBox.information(self.view, "Concluído", f"Os dados da UASG {uasg} foram removidos.")