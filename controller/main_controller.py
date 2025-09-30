# controller/main_controller.py

from PyQt6.QtWidgets import QApplication

# Importa os componentes dos módulos específicos
from Contratos.controller.uasg_controller import UASGController
from atas.view.atas_view import AtasView
from atas.controller.atas_controller import AtasController
from atas.model.atas_model import AtasModel

class MainController:
    def __init__(self, view, base_dir):
        self.view = view
        self.base_dir = base_dir

        # 1. Prepara e adiciona o módulo de Contratos
        self.contratos_controller = UASGController(self.base_dir, self.view)
        self.view.stacked_widget.addWidget(self.contratos_controller.view)

        # 2. Prepara e adiciona o módulo de Atas (placeholder)
        self.atas_model = AtasModel()
        self.atas_view = AtasView()
        self.atas_controller = AtasController(self.atas_model, self.atas_view)
        self.view.stacked_widget.addWidget(self.atas_view)

        # 3. Conecta o menu de navegação à função de troca de tela
        self.view.nav_list.currentRowChanged.connect(self.switch_module)
        self.view.nav_list.setCurrentRow(0)

    def switch_module(self, index):
        # O índice do stacked_widget é o índice da lista + 1 (pois o 0 é a tela de boas-vindas)
        self.view.stacked_widget.setCurrentIndex(index)
        
    def run(self):
        self.view.show()