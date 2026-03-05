# controller/main_controller.py

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer  # --- Adicionada a importação do QTimer ---

# Importa os componentes dos módulos específicos
from Contratos.controller.uasg_controller import UASGController
from atas.view.atas_view import AtasView
from atas.controller.atas_controller import AtasController
from atas.model.atas_model import AtasModel
from auto.controller.auto_controller import AutoController

# --- Importações Adicionadas ---
from view.info_dialog import InfoDialog
from backup.controller.backup_controller import BackupController
from view.help_dialog import HelpDialog
# --- Fim das Importações Adicionadas ---

class MainController:
    def __init__(self, view, base_dir):
        self.view = view
        self.base_dir = base_dir

        # Conecta apenas os botões da Home que são leves primeiro
        self.view.info_button.clicked.connect(self.show_info_dialog)
        self.view.backup_button.clicked.connect(self.show_backup_dialog)
        self.view.help_button.clicked.connect(self.show_help_dialog)

        # Deixa a barra lateral desativada por um milissegundo até carregar tudo
        self.view.nav_list.setEnabled(False)

        # ⏳ AGENDA O CARREGAMENTO PESADO PARA LOGO APÓS A TELA ABRIR (100 ms)
        QTimer.singleShot(150, self.load_heavy_modules)

    def load_heavy_modules(self):
        """Carrega os bancos de dados e views pesadas apenas após a interface renderizar."""
        
        # 1. Prepara e adiciona o módulo de Contratos
        self.contratos_controller = UASGController(self.base_dir, self.view)
        self.view.stacked_widget.addWidget(self.contratos_controller.view)

        # 2. Prepara e adiciona o módulo de Atas
        self.atas_model = AtasModel()
        self.atas_view = AtasView()
        self.atas_controller = AtasController(self.atas_model, self.atas_view)
        self.view.stacked_widget.addWidget(self.atas_view)

        # 3. Agora que contratos_controller existe, conecta o botão de Automação
        self.view.automation_button.clicked.connect(self.show_automation_dialog)

        # 4. Conecta o menu de navegação à função de troca de tela e reativa a barra
        self.view.nav_list.currentRowChanged.connect(self.switch_module)
        self.view.nav_list.setCurrentRow(0)
        self.view.nav_list.setEnabled(True)

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

    def show_automation_dialog(self):
        """Abre a janela do módulo de Automações."""
        self.auto_controller = AutoController(self.view, self.base_dir, self.contratos_controller)
        self.auto_controller.show()

    def show_help_dialog(self):
        dialog = HelpDialog(self.view)
        dialog.exec()
