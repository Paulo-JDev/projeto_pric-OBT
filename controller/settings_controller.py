# controller/settings_controller.py
from PyQt6.QtCore import pyqtSignal, QObject
from view.settings_dialog import SettingsDialog

class SettingsController(QObject):
    mode_changed = pyqtSignal(str)

    def __init__(self, model, parent=None):
        # --- CORREÇÃO AQUI ---
        # Adicione esta linha para inicializar o QObject
        super().__init__(parent)
        
        self.model = model
        self.view = SettingsDialog(parent)

        self.view.close_button.clicked.connect(self.view.close)
        self.view.mode_button.clicked.connect(self._toggle_data_mode)
        
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