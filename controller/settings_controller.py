# controller/settings_controller.py
from view.settings_dialog import SettingsDialog

class SettingsController:
    def __init__(self, model, parent=None):
        self.model = model
        self.view = SettingsDialog(parent)
        self.view.close_button.clicked.connect(self.view.close)
        self.view.mode_button.clicked.connect(self._toggle_data_mode)
        self._load_initial_state()

    def show(self):
        self.view.exec()

    def _load_initial_state(self):
        self.current_mode = self.model.load_setting("data_mode", "Online")
        self._update_button_style()

    def _toggle_data_mode(self):
        self.current_mode = "Offline" if self.current_mode == "Online" else "Online"
        self.model.save_setting("data_mode", self.current_mode)
        self._update_button_style()

    def _update_button_style(self):
        if self.current_mode == "Online":
            self.view.mode_button.setText("Online")
            self.view.mode_button.setChecked(True)
            self.view.mode_button.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
        else:
            self.view.mode_button.setText("Offline")
            self.view.mode_button.setChecked(False)
            self.view.mode_button.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")