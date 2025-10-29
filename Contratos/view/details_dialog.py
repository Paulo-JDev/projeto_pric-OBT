# Contratos/view/details_dialog.py

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTabWidget, 
    QHBoxLayout, QMessageBox, QApplication
)
from PyQt6.QtCore import pyqtSignal

# Imports de utilitários
from Contratos.model.uasg_model import resource_path
from utils.icon_loader import icon_manager

# Imports das abas
from Contratos.view.abas_detalhes.general_tab import create_general_tab
from Contratos.view.abas_detalhes.pdfs_view import create_object_tab
from Contratos.view.abas_detalhes.status_tab import create_status_tab
from Contratos.view.abas_detalhes.extras_link import aba_extras_link
from Contratos.view.abas_detalhes.empenhos_tab import create_empenhos_tab
from Contratos.view.abas_detalhes.itens_tab import create_itens_tab
from Contratos.view.abas_detalhes.fiscal_tab import create_fiscal_tab
from Contratos.view.abas_detalhes.edit_object_dialog import EditObjectDialog
from Contratos.view.abas_detalhes.email_dialog import EmailDialog

# Imports dos controllers
from Contratos.controller.itens_controller import ItensController
from Contratos.controller.empenhos_controller import EmpenhoController
from Contratos.controller.email_controller import EmailController
from Contratos.controller.detalhe_controller import (
    registro_def, delete_registro, save_status, load_status,
    show_success_message, copy_to_clipboard, copy_registros
)


class DetailsDialog(QDialog):
    # Sinal que será emitido quando o botão de salvar for pressionado
    data_saved = pyqtSignal(dict)
    
    def __init__(self, data, model, parent=None):
        super().__init__(parent)
        
        # Configuração da janela
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(1100, 600)
        
        # Armazena dados e model
        self.data = data
        self.model = model
        
        # Variáveis de controle
        self.pdf_path = None
        self.json_cache = {}
        
        # Dicionários para widgets dinâmicos
        self.radio_groups = {}
        self.radio_buttons = {}
        
        # Referências de widgets importantes (inicializadas pelas abas)
        self.objeto_edit = None
        self.portaria_edit = None
        self.termo_aditivo_edit = None
        self.status_dropdown = None
        self.registro_list = None
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # ==================== CRIAR ABAS ====================
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Adiciona todas as abas
        self.create_tabs()
        
        # ==================== BOTÕES DE AÇÃO ====================
        self.create_action_buttons()
        
        # ==================== CARREGA DADOS SALVOS ====================
        # Chama após todas as abas serem criadas
        self.load_all_data()
    
    def create_tabs(self):
        """Cria todas as abas do dialog"""
        self.tabs.addTab(create_general_tab(self), "Informações Gerais")
        self.tabs.addTab(create_object_tab(self), "LINKS do Contrato")
        self.tabs.addTab(create_fiscal_tab(self), "Fiscalização")  # ✅ NOVA ABA
        self.tabs.addTab(create_status_tab(self), "Status")
        self.tabs.addTab(create_empenhos_tab(self), "Empenhos")
        self.tabs.addTab(create_itens_tab(self), "Itens")
        self.tabs.addTab(aba_extras_link(self), "Extras")
        
        # Conecta botão de copiar registros (criado em status_tab)
        if hasattr(self, 'copy_registro_button'):
            self.copy_registro_button.clicked.connect(self.copy_registro_def)
    
    def create_action_buttons(self):
        """Cria os botões de ação (Salvar e Cancelar)"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Botão Salvar
        save_button = QPushButton("Salvar")
        save_button.setIcon(icon_manager.get_icon("concluido"))
        save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(save_button)
        
        # Botão Cancelar
        cancel_button = QPushButton("Cancelar")
        cancel_button.setIcon(icon_manager.get_icon("close"))
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        self.main_layout.addLayout(button_layout)
    
    # ==================== MÉTODOS DE CARGA/SALVAMENTO ====================
    
    def load_all_data(self):
        """
        Carrega todos os dados salvos do banco de dados.
        
        ✅ Inclui automaticamente: status, links, registros e fiscalização
        """
        # Verifica se os widgets necessários foram inicializados
        if not hasattr(self, 'status_dropdown') or self.status_dropdown is None:
            print("⚠️ Widgets de status não inicializados ainda")
            return
        
        # Chama load_status que agora também carrega fiscalização
        load_status(
            self.data,
            self.model,
            self.status_dropdown,
            self.objeto_edit,
            self.portaria_edit,
            self.termo_aditivo_edit,
            self.radio_buttons,
            self.registro_list,
            self  # parent_dialog
        )
        
        print(f"✅ Dados carregados para o contrato {self.data.get('numero', 'N/A')}")
    
    def save_and_close(self):
        """
        Salva todos os dados e fecha o dialog.
        
        ✅ Inclui automaticamente: status, links, registros e fiscalização
        """
        # Verifica se os widgets necessários existem
        if not hasattr(self, 'status_dropdown') or self.status_dropdown is None:
            QMessageBox.warning(self, "Erro", "Widgets de status não inicializados")
            return
        
        # Chama save_status que agora também salva fiscalização
        result = save_status(
            self,  # parent
            self.data,
            self.model,
            self.status_dropdown,
            self.registro_list,
            self.objeto_edit,
            self.portaria_edit,
            self.termo_aditivo_edit,
            self.radio_buttons
        )
        
        if result and result[0]:  # Se salvou com sucesso
            # Emite sinal com informações atualizadas
            details_info = {
                'status': self.status_dropdown.currentText(),
                'objeto': self.objeto_edit.text() if self.objeto_edit else ''
            }
            self.data_saved.emit(details_info)
            
            # Mostra mensagem de sucesso
            show_success_message(self)
            
            print(f"✅ Dados salvos para o contrato {self.data.get('numero', 'N/A')}")
    
    # ==================== MÉTODOS DE REGISTROS (STATUS) ====================
    
    def registro_def(self):
        """Abre dialog para adicionar um novo registro de status"""
        registro_def(self, self.registro_list, self.status_dropdown)
    
    def delete_registro(self):
        """Remove os registros selecionados (com checkbox marcado)"""
        delete_registro(self.registro_list)
    
    def copy_registro_def(self):
        """Copia os registros selecionados para a área de transferência"""
        copy_registros(self, self.registro_list)
    
    # ==================== MÉTODOS DE EDIÇÃO ====================
    
    def open_object_editor(self):
        """Abre dialog para editar o campo Objeto em múltiplas linhas"""
        current_text = self.objeto_edit.text() if self.objeto_edit else ""
        editor_dialog = EditObjectDialog(current_text, self)
        editor_dialog.text_saved.connect(self.update_object_text)
        editor_dialog.exec()
    
    def update_object_text(self, new_text):
        """
        Atualiza o texto do campo Objeto.
        
        Args:
            new_text (str): Novo texto do objeto
        """
        if self.objeto_edit:
            self.objeto_edit.setText(new_text)
            print("✅ Objeto atualizado na interface")
    
    # ==================== MÉTODOS DE CLIPBOARD ====================
    
    def copy_to_clipboard(self, line_edit):
        """
        Copia texto de um QLineEdit para a área de transferência.
        
        Args:
            line_edit (QLineEdit): Widget contendo o texto
        """
        copy_to_clipboard(line_edit)
    
    def copy_text_edit_to_clipboard(self, text_edit):
        """
        Copia texto de um QTextEdit para a área de transferência.
        
        Args:
            text_edit (QTextEdit): Widget contendo o texto
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(text_edit.toPlainText())
        print("✅ Texto copiado para a área de transferência")
    
    # ==================== MÉTODOS DE RELATÓRIOS ====================
    
    def generate_empenho_report_to_excel(self):
        """Gera relatório de empenhos em Excel"""
        empenho_controller = EmpenhoController(self.model, self)
        empenho_controller.generate_report_to_excel(self.data)
    
    def generate_itens_report_to_excel(self):
        """Gera relatório de itens em Excel"""
        itens_controller = ItensController(self.model, self)
        itens_controller.generate_report_to_excel(self.data)
    
    # ==================== MÉTODO DE ENVIO DE E-MAIL ====================
    
    def open_email_dialog(self):
        """
        Abre dialog para enviar relatório por e-mail.
        
        Permite correções sem fechar a janela desnecessariamente.
        """
        email_dialog = EmailDialog(self)
        
        while True:
            # Abre o dialog e aguarda resposta
            if not email_dialog.exec():
                # Usuário cancelou
                return
            
            # Valida dados inseridos
            email_data = email_dialog.get_data()
            recipient = email_data.get('recipient_email', '').strip()
            file_path = email_data.get('file_path', '').strip()
            
            if not recipient or not file_path:
                QMessageBox.warning(
                    self,
                    "Dados Incompletos",
                    "Por favor, preencha o e-mail e selecione um arquivo."
                )
                continue
            
            # Confirmação final
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
            
            # Prepara e envia e-mail
            licitacao_numero = self.data.get('licitacao_numero', 'N/A')
            nome_resumido = self.data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "N/A")
            
            subject = f"Relatório de Empenhos do Contrato {contrato_numero}"
            body = (
                f"Segue em anexo o relatório de execução de empenhos para o contrato nº {contrato_numero} "
                f"referente ao Processo nº {licitacao_numero} do órgão {nome_resumido}."
            )
            
            email_controller = EmailController(self)
            success, message = email_controller.send_email(recipient, subject, body, file_path)
            
            if success:
                QMessageBox.information(self, "Sucesso", message)
            else:
                QMessageBox.critical(self, "Falha no Envio", message)
            
            break
