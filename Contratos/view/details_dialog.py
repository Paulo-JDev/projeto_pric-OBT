import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTabWidget, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager

from Contratos.view.abas_detalhes.general_tab import create_general_tab
from Contratos.view.abas_detalhes.pdfs_view import create_object_tab
from Contratos.view.abas_detalhes.status_tab import create_status_tab
from Contratos.view.abas_detalhes.extras_link import aba_extras_link
from Contratos.view.abas_detalhes.empenhos_tab import create_empenhos_tab
from Contratos.view.abas_detalhes.itens_tab import create_itens_tab

from Contratos.view.abas_detalhes.edit_object_dialog import EditObjectDialog
from Contratos.view.abas_detalhes.email_dialog import EmailDialog
from Contratos.controller.itens_controller import ItensController

from Contratos.controller.empenhos_controller import EmpenhoController
from Contratos.controller.email_controller import EmailController
from Contratos.controller.detalhe_controller import *

class DetailsDialog(QDialog):
    # Sinal que será emitido quando o botão de salvar for pressionado
    data_saved = pyqtSignal(dict)

    def __init__(self, data, model, parent=None): # Adicionado 'model'
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(1100, 600)
        self.pdf_path = None

        self.load_styles()
        self.model = model # Armazena a instância do UASGModel

        self.data = data
        self.main_layout = QVBoxLayout(self)

        self.json_cache = {}
        self.radio_groups = {}  
        self.radio_buttons = {}  

        self.objeto_edit = None
        self.portaria_edit = None
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
        self.tabs.addTab(create_empenhos_tab(self), "Empenhos")
        self.tabs.addTab(create_itens_tab(self), "Itens")
        self.tabs.addTab(aba_extras_link(self), "Extras")
        

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
        load_status(self.data, self.model, self.status_dropdown, self.objeto_edit, self.portaria_edit, self.radio_buttons, self.registro_list, self.comment_list)

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
        save_status(self, self.data, self.model, self.status_dropdown, self.registro_list, self.comment_list, self.objeto_edit, self.portaria_edit, self.radio_buttons)
        
        details_info = {
            'status': self.status_dropdown.currentText(),
            'objeto': self.objeto_edit.text()
        }
        
        self.data_saved.emit(details_info)
        show_success_message(self)
    
    def open_object_editor(self):
        """Abre a janela de edição para o campo Objeto."""
        editor_dialog = EditObjectDialog(self.objeto_edit.text(), self)
        # Conecta o sinal 'text_saved' do diálogo a um método para atualizar o campo
        editor_dialog.text_saved.connect(self.update_object_text)
        editor_dialog.exec()

    def update_object_text(self, new_text):
        """Atualiza o texto do QLineEdit 'objeto_edit'."""
        self.objeto_edit.setText(new_text)
        print("✅ Objeto atualizado na interface.")

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

    def generate_empenho_report_to_excel(self):
        """ Instancia o EmpenhoController e delega a ele a criação do relatório. """
        empenho_controller = EmpenhoController(self.model, self)
        empenho_controller.generate_report_to_excel(self.data)

    def generate_itens_report_to_excel(self):
        itens_controller = ItensController(self.model, self)
        itens_controller.generate_report_to_excel(self.data)

    def open_email_dialog(self):
        """ Abre e gerencia a janela de envio de e-mail, permitindo correções
        sem fechar a janela desnecessariamente. """
        email_dialog = EmailDialog(self)
        while True:
            if not email_dialog.exec():
                # O usuário clicou em "Cancelar" na janela de e-mail, então encerramos o processo.
                return

            # Se chegou aqui, o usuário clicou em "Enviar". Agora validamos os dados.
            email_data = email_dialog.get_data()
            recipient = email_data['recipient_email']
            file_path = email_data['file_path']

            if not recipient or not file_path:
                QMessageBox.warning(self, "Dados Incompletos", "Por favor, preencha o e-mail e selecione um arquivo.")
                continue

            # Se os dados são válidos, mostramos a confirmação final.
            contrato_numero = self.data.get('numero', 'N/A')
            
            reply = QMessageBox.question(
                self,
                "Confirmar Envio",
                f"O e-mail será enviado com as informações do contrato <b>{contrato_numero}</b>.\n\n"
                "Verifique se a planilha e o contrato selecionado estão corretos antes de continuar.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )

            if reply != QMessageBox.StandardButton.Yes:
                continue
            
            # Se todas as validações e confirmações passaram, enviamos o e-mail.
            licitacao_numero = self.data.get('licitacao_numero', 'N/A')
            nome_resumido = self.data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "N/A")

            subject = f"Relatório de Empenhos do Contrato {contrato_numero}"
            body = (f"Segue em anexo o relatório de execução de empenhos para o contrato nº {contrato_numero} "
                    f"referente ao Processo nº {licitacao_numero} do órgão {nome_resumido}.")
            
            email_controller = EmailController(self)
            success, message = email_controller.send_email(recipient, subject, body, file_path)

            if success:
                QMessageBox.information(self, "Sucesso", message)
            else:
                QMessageBox.critical(self, "Falha no Envio", message)

            break
