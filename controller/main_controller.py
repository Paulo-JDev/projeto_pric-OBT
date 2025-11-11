# controller/main_controller.py

from PyQt6.QtWidgets import QApplication

# Importa os componentes dos módulos específicos
from Contratos.controller.uasg_controller import UASGController
from atas.view.atas_view import AtasView
from atas.controller.atas_controller import AtasController
from atas.model.atas_model import AtasModel

# --- Importações Adicionadas ---
from view.info_dialog import InfoDialog
from backup.controller.backup_controller import BackupController
# --- Fim das Importações Adicionadas ---

class MainController:
    def __init__(self, view, base_dir):
        self.view = view
        self.base_dir = base_dir

        # 1. Prepara e adiciona o módulo de Contratos
        self.contratos_controller = UASGController(self.base_dir, self.view)
        self.view.stacked_widget.addWidget(self.contratos_controller.view)

        # 2. Prepara e adiciona o módulo de Atas
        self.atas_model = AtasModel()
        self.atas_view = AtasView()
        self.atas_controller = AtasController(self.atas_model, self.atas_view)
        self.view.stacked_widget.addWidget(self.atas_view)

        # 3. Conecta o menu de navegação à função de troca de tela
        self.view.nav_list.currentRowChanged.connect(self.switch_module)
        self.view.nav_list.setCurrentRow(0)

        # --- Conexões dos novos botões da tela Home ---
        self.view.info_button.clicked.connect(self.show_info_dialog)
        self.view.backup_button.clicked.connect(self.show_backup_dialog)
        # --- Fim das novas conexões ---

    def switch_module(self, index):
        # O índice do stacked_widget é o índice da lista (pois o 0 agora é o menu Home)
        self.view.stacked_widget.setCurrentIndex(index)
        
    def run(self):
        self.view.show()

    # --- Novos métodos para os botões ---
    def show_info_dialog(self):
        """Abre a janela de Informações do Projeto."""
        dialog = InfoDialog(self.view)
        dialog.exec()

    def show_backup_dialog(self):
        """Abre a janela do módulo de Backup."""
        # O controlador de backup gerencia sua própria view
        self.backup_controller = BackupController(self.view)
        self.backup_controller.show()
