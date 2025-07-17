import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTabWidget, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from model.uasg_model import resource_path
from utils.icon_loader import icon_manager

from view.abas_detalhes.general_tab import create_general_tab
from view.abas_detalhes.object_tab import create_object_tab
from view.abas_detalhes.status_tab import create_status_tab
from view.abas_detalhes.termo_adt import aba_termo_adt
from controller.detalhe_controller import *

class DetailsDialog(QDialog):
    # Sinal que será emitido quando o botão de salvar for pressionado
    data_saved = pyqtSignal()

    def __init__(self, data, model, parent=None): # Adicionado 'model'
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(1100, 600)
        self.pdf_path = None

        self.load_styles()
        self.model = model # Armazena a instância do UASGModel

        self.data = data
        self.main_layout = QVBoxLayout(self)

        self.radio_groups = {}  # Adicione esta linha
        self.radio_buttons = {}  # Adicione esta linha (se ainda não estiver presente)

        self.objeto_edit = None
        self.status_dropdown = None
        self.comment_list = None
        self.registro_list = None

        # Criar o TabWidget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Criar abas
        self.tabs.addTab(create_general_tab(self), "Informações Gerais")
        self.tabs.addTab(create_object_tab(self), "PDF do contrato")
        self.tabs.addTab(create_status_tab(self), "Status")
        self.tabs.addTab(aba_termo_adt(self), "Termo Aditivo")

        # Layout dos botões de salvar e cancelar
        button_layout = QHBoxLayout()
        
        # Botão de salvar
        save_button = QPushButton("Salvar")
        save_button.setIcon(icon_manager.get_icon("concluido"))
        save_button.clicked.connect(self.func_save)
        button_layout.addWidget(save_button)
        
        # Botão de cancelar
        cancel_button = QPushButton("Cancelar")
        cancel_button.setIcon(icon_manager.get_icon("close"))
        cancel_button.clicked.connect(self.close)  # Fecha a janela sem salvar
        button_layout.addWidget(cancel_button)
        
        self.main_layout.addLayout(button_layout)

        # Carregar dados salvos
        load_status(self.data, self.model, self.status_dropdown, self.objeto_edit, self.radio_buttons, self.registro_list, self.comment_list)

    def registro_def(self):
        """Abre uma mini janela para adicionar um comentário com data, hora e status selecionado."""
        registro_def(self, self.registro_list, self.status_dropdown)

    def add_comment(self):
        """Abre uma mini janela para adicionar um comentário."""
        add_comment(self, self.comment_list)
    
    def delete_comment(self):
        """Remove os comentários selecionados"""
        delete_comment(self.comment_list)
    
    def delete_registro(self):
        """Remove os registros selecionados"""
        delete_registro(self.registro_list)
    
    def func_save(self):
        """Salva o status e os comentários ao fechar a janela"""
        # Salvar os dados primeiro
        save_status(self, self.data, self.model, self.status_dropdown, self.registro_list, self.comment_list, self.objeto_edit, self.radio_buttons)
        
        # Emitir o sinal ANTES de mostrar a mensagem para atualizar a tabela imediatamente
        self.data_saved.emit()
        
        # Mostrar mensagem de sucesso
        show_success_message(self)

    def copy_to_clipboard(self, line_edit):
        """Copia o texto do campo para a área de transferência"""
        copy_to_clipboard(line_edit)

    def load_styles(self):
        """Carrega os estilos do arquivo style.qss"""
        style_path = resource_path("style.qss")  # Usa resource_path para garantir o caminho correto

        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠ Arquivo {style_path} não encontrado. Estilos não foram aplicados.")
