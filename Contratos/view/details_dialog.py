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

# ==================== IMPORTS PARA CONTRATOS NORMAIS ====================
from Contratos.view.abas_detalhes.general_tab import create_general_tab
from Contratos.view.abas_detalhes.pdfs_view import create_object_tab
from Contratos.view.abas_detalhes.status_tab import create_status_tab
from Contratos.view.abas_detalhes.extras_link import aba_extras_link
from Contratos.view.abas_detalhes.empenhos_tab import create_empenhos_tab
from Contratos.view.abas_detalhes.itens_tab import create_itens_tab
from Contratos.view.abas_detalhes.fiscal_tab import create_fiscal_tab
from Contratos.view.abas_detalhes.edit_object_dialog import EditObjectDialog
from Contratos.view.abas_detalhes.email_dialog import EmailDialog

# ==================== IMPORTS PARA CONTRATOS MANUAIS ====================
from Contratos.view.detalhes_manual.general_tab_manual import create_general_tab_manual
from Contratos.view.detalhes_manual.links_tab_manual import create_links_tab_manual

# Imports dos controllers
from Contratos.controller.itens_controller import ItensController
from Contratos.controller.empenhos_controller import EmpenhoController
from Contratos.controller.email_controller import EmailController
from integration.controller.trello_individual_controller import TrelloIndividualController
from integration.model.trello_model import TrelloModel
from Contratos.controller.detalhe_controller import (
    registro_def, delete_registro, save_status, load_status,
    show_success_message, copy_to_clipboard, copy_registros
)


class DetailsDialog(QDialog):
    """
    Dialog de detalhes do contrato com múltiplas abas.
    
    ✅ ATUALIZADO: Detecta se é contrato manual e carrega abas apropriadas
    
    Signals:
        data_saved: Emitido quando dados são salvos com sucesso
    """
    
    data_saved = pyqtSignal(dict)
    
    def __init__(self, data, model, parent=None):
        super().__init__(parent)
        
        # Configuração da janela
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(1100, 600)
        
        # Armazena dados e model
        self.data = data
        self.model = model
        
        # ==================== ✅ DETECTA SE É MANUAL ====================
        self.is_manual = data.get("manual", False)
        
        # Variáveis de controle
        self.pdf_path = None
        self.json_cache = {}
        
        # Dicionários para widgets dinâmicos
        self.radio_groups = {}
        self.radio_buttons = {}
        
        # Referências de widgets importantes
        self.objeto_edit = None
        self.portaria_edit = None
        self.termo_aditivo_edit = None
        self.status_dropdown = None
        self.registro_list = None
        self._trello_thread = None
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # ==================== CRIAR ABAS ====================
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        self._create_tabs()
        
        # ==================== BOTÕES DE AÇÃO ====================
        self._create_action_buttons()
        
        # ==================== CARREGA DADOS SALVOS ====================
        self.load_all_data()
    
    def _create_tabs(self):
        """
        Cria abas apropriadas baseado no tipo de contrato.
        
        ✅ MANUAL: Informações Gerais (editável) + Links (sem automáticos) + Fiscalização + Status
        ✅ NORMAL: Todas as abas (Empenhos, Itens, Extras incluídos)
        """
        if self.is_manual:
            # ==================== ABAS PARA CONTRATO MANUAL ====================
            self.tabs.addTab(create_general_tab_manual(self), "Informações Gerais")
            self.tabs.addTab(create_links_tab_manual(self), "LINKS do Contrato")
            self.tabs.addTab(create_fiscal_tab(self), "Fiscalização")
            self.tabs.addTab(create_status_tab(self), "Status")
        else:
            # ==================== ABAS PARA CONTRATO NORMAL ====================
            self.tabs.addTab(create_general_tab(self), "Informações Gerais")
            self.tabs.addTab(create_object_tab(self), "LINKS do Contrato")
            self.tabs.addTab(create_fiscal_tab(self), "Fiscalização")
            self.tabs.addTab(create_status_tab(self), "Status")
            self.tabs.addTab(create_empenhos_tab(self), "Empenhos")
            self.tabs.addTab(create_itens_tab(self), "Itens")
            self.tabs.addTab(aba_extras_link(self), "Extras")

        # ==================== CONEXÕES DE BOTÕES DA ABA STATUS ====================
       
        if hasattr(self, 'copy_registro_button'):
            # Conecta botão de copiar registros (criado em status_tab)
            self.copy_registro_button.clicked.connect(self.copy_registro_def)
        
        if hasattr(self, 'trello_button'):
            # Instancia o serviço de API e o Controller Individual
            self.trello_model = TrelloModel()
            self.trello_individual_ctrl = TrelloIndividualController(self.trello_model)
            
            # Conecta o clique ao método que gerencia o envio
            self.trello_button.clicked.connect(self.handle_trello_individual_sync)
        
        if not hasattr(self, 'trello_individual_ctrl'):
            self.trello_model = TrelloModel()
            self.trello_individual_ctrl = TrelloIndividualController(self.trello_model)
    
    def _create_action_buttons(self):
        """Cria os botões de ação (Salvar e Cancelar)"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Botão Salvar
        save_button = QPushButton("Salvar")
        save_button.setIcon(icon_manager.get_icon("concluido"))
        save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(save_button)

        # Botão Trello
        self.trello_button = QPushButton("CA-Trello")
        self.trello_button.setIcon(icon_manager.get_icon("trello"))  # Use ícone do Trello se tiver
        self.trello_button.setToolTip("Sincronizar este contrato com o Trello")
        self.trello_button.clicked.connect(self.handle_trello_individual_sync)
        self.trello_button.setObjectName("trello_button")
        button_layout.addWidget(self.trello_button)
        
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
        
        ✅ Funciona tanto para contratos manuais quanto normais
        """
        if not hasattr(self, 'status_dropdown') or self.status_dropdown is None:
            print("⚠️ Widgets de status não inicializados ainda")
            return
        
        # Chama load_status que carrega: status, links, registros, fiscalização
        load_status(
            self.data,
            self.model,
            self.status_dropdown,
            self.objeto_edit,
            self.portaria_edit,
            self.termo_aditivo_edit,
            self.radio_buttons,
            self.registro_list,
            self
        )
        
        print(f"✅ Dados carregados para o contrato {self.data.get('numero', 'N/A')}")
    
    def save_and_close(self):
        """
        Salva todos os dados e fecha o dialog.
        
        ✅ Para contratos manuais, também salva os campos editáveis
        """
        if not hasattr(self, 'status_dropdown') or self.status_dropdown is None:
            QMessageBox.warning(self, "Erro", "Widgets de status não inicializados")
            return
        
        # ==================== SALVA CAMPOS EDITÁVEIS (SE MANUAL) ====================
        if self.is_manual:
            self._save_manual_fields()
        
        # ==================== SALVA STATUS, LINKS, REGISTROS, FISCALIZAÇÃO ====================
        result = save_status(
            self,
            self.data,
            self.model,
            self.status_dropdown,
            self.registro_list,
            self.objeto_edit,
            self.portaria_edit,
            self.termo_aditivo_edit,
            self.radio_buttons
        )
        
        if result and result[0]:
            # Emite sinal com informações atualizadas
            details_info = {
                'status': self.status_dropdown.currentText(),
                'objeto': self.objeto_edit.text() if self.objeto_edit else ''
            }
            self.data_saved.emit(details_info)
            show_success_message(self)
            print(f"✅ Dados salvos para o contrato {self.data.get('numero', 'N/A')}")
    
    def _save_manual_fields(self):
        """
        Salva campos editáveis de contratos manuais no banco.
        """
        from Contratos.model.models import Contrato
        
        db = self.model._get_db_session()
        
        try:
            contrato_id = self.data.get('id')
            contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
            
            if not contrato:
                print(f"⚠️ Contrato {contrato_id} não encontrado no banco")
                return
            
            # ==================== ATUALIZA CAMPOS NO BANCO ====================
            if hasattr(self, 'manual_numero'):
                contrato.numero = self.manual_numero.text()
            if hasattr(self, 'manual_licitacao'):
                contrato.licitacao_numero = self.manual_licitacao.text()
            if hasattr(self, 'manual_nup'):
                contrato.processo = self.manual_nup.text()
            if hasattr(self, 'manual_valor'):
                # Remove formatação de moeda antes de salvar
                valor_texto = self.manual_valor.text().replace('R$', '').replace('.', '').replace(',', '.').strip()
                contrato.valor_global = valor_texto
            if hasattr(self, 'manual_cnpj'):
                contrato.fornecedor_cnpj = self.manual_cnpj.text()
            if hasattr(self, 'manual_empresa'):
                contrato.fornecedor_nome = self.manual_empresa.text()
            if hasattr(self, 'manual_vigencia_inicio'):
                # Converte QDateEdit para string
                data_inicio = self.manual_vigencia_inicio.date().toString("yyyy-MM-dd")
                contrato.vigencia_inicio = data_inicio
            if hasattr(self, 'manual_vigencia_fim'):
                # Converte QDateEdit para string
                data_fim = self.manual_vigencia_fim.date().toString("yyyy-MM-dd")
                contrato.vigencia_fim = data_fim
            if hasattr(self, 'manual_tipo'):
                contrato.tipo = self.manual_tipo.text()
            if hasattr(self, 'manual_modalidade'):
                contrato.modalidade = self.manual_modalidade.text()
            
            sigla_om = ""
            if hasattr(self, 'manual_sigla_om'):
                sigla_om = self.manual_sigla_om.text()
                contrato.contratante_orgao_unidade_gestora_nome_resumido = sigla_om
            
            orgao_responsavel = ""
            if hasattr(self, 'manual_orgao'):
                orgao_responsavel = self.manual_orgao.text()
                # Pode criar um campo adicional no model se necessário
                # Por enquanto, vamos incluir no raw_json
            
            # Atualiza objeto
            if self.objeto_edit:
                contrato.objeto = self.objeto_edit.text()
            
            self.data.update({
                "id": contrato.id,
                "numero": contrato.numero,
                "licitacao_numero": contrato.licitacao_numero,
                "processo": contrato.processo,
                "fornecedor": {
                    "nome": contrato.fornecedor_nome or "",
                    "cnpj_cpf_idgener": contrato.fornecedor_cnpj or ""
                },
                "objeto": contrato.objeto or "",
                "valor_global": contrato.valor_global or "",
                "vigencia_inicio": contrato.vigencia_inicio or "",
                "vigencia_fim": contrato.vigencia_fim or "",
                "tipo": contrato.tipo or "",
                "modalidade": contrato.modalidade or "",
                "contratante": {
                    "orgao": {
                        "unidade_gestora": {
                            "codigo": contrato.uasg_code,
                            "nome_resumido": sigla_om
                        }
                    },
                    "orgao_responsavel": orgao_responsavel
                },
                "manual": True,
                "sigla_om_resp": sigla_om,
                "orgao_responsavel": orgao_responsavel
            })
            
            # Atualiza raw_json
            import json
            contrato.raw_json = json.dumps(self.data)
            
            db.commit()
            print(f"✅ Campos editáveis do contrato manual {contrato_id} salvos")
            
        except Exception as e:
            print(f"❌ Erro ao salvar campos editáveis: {e}")
            db.rollback()
        finally:
            db.close()
    
    # ==================== MÉTODOS DE REGISTROS (STATUS) ====================
    
    def registro_def(self):
        """Abre dialog para adicionar um novo registro de status"""
        registro_def(self, self.registro_list, self.status_dropdown)
    
    def delete_registro(self):
        """Remove os registros selecionados"""
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
        """Atualiza o texto do campo Objeto"""
        if self.objeto_edit:
            self.objeto_edit.setText(new_text)
            print("✅ Objeto atualizado na interface")
    
    # ==================== MÉTODOS DE CLIPBOARD ====================
    
    def copy_to_clipboard(self, line_edit):
        """Copia texto de um QLineEdit para a área de transferência"""
        copy_to_clipboard(line_edit)
    
    def copy_text_edit_to_clipboard(self, text_edit):
        """Copia texto de um QTextEdit para a área de transferência"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text_edit.toPlainText())
        print("✅ Texto copiado para a área de transferência")

    def copy_to_clipboard_date(self, date_edit):
        """Copia data de um QDateEdit para a área de transferência"""
        clipboard = QApplication.clipboard()
        clipboard.setText(date_edit.date().toString("dd/MM/yyyy"))
        print("✅ Data copiada para a área de transferência")
    
    def open_link(self, url):
        """Abre um link no navegador padrão"""
        if url:
            import webbrowser
            webbrowser.open(url)
    
    # ==================== MÉTODOS DE RELATÓRIOS ====================
    
    def generate_empenho_report_to_excel(self):
        """Gera relatório de empenhos em Excel"""
        if not self.is_manual:  # Só funciona para contratos normais
            empenho_controller = EmpenhoController(self.model, self)
            empenho_controller.generate_report_to_excel(self.data)
    
    def generate_itens_report_to_excel(self):
        """Gera relatório de itens em Excel"""
        if not self.is_manual:  # Só funciona para contratos normais
            itens_controller = ItensController(self.model, self)
            itens_controller.generate_report_to_excel(self.data)
    
    # ==================== MÉTODO DE ENVIO DE E-MAIL ====================
    
    def open_email_dialog(self):
        """Abre dialog para enviar relatório por e-mail"""
        if not self.is_manual:  # Só funciona para contratos normais
            email_dialog = EmailDialog(self)
            
            while True:
                if not email_dialog.exec():
                    return
                
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

    # ==================== NOVO MÉTODO PARA SYNC INDIVIDUAL ====================

    def handle_trello_individual_sync(self):
        """Sincroniza este contrato individual com o Trello em background."""
        import logging

        # Valida se há dados do contrato
        if not self.data or not self.data.get("id"):
            QMessageBox.warning(self, "Aviso", "Salve o contrato antes de sincronizar com o Trello.")
            return

        # Verifica se já há uma sincronização em andamento
        if self._trello_thread is not None and self._trello_thread.isRunning():
            QMessageBox.information(self, "Aguarde", "Já existe uma sincronização em andamento.")
            return

        # Pega o status atual
        status_atual = self.status_dropdown.currentText() if hasattr(self, 'status_dropdown') else "SEÇÃO CONTRATOS"

        # Verifica se o status está mapeado
        if hasattr(self, 'trello_individual_ctrl'):
            list_id = self.trello_individual_ctrl.trello_model.config.get("mappings", {}).get(status_atual)
            if not list_id:
                QMessageBox.warning(
                    self, 
                    "Configuração Trello",
                    f"O status '{status_atual}' ainda não tem uma lista mapeada.\n"
                    "Abra a tela de configuração do Trello e informe o ID da lista."
                )
                return

        # Prepara dados do contrato
        contrato_para_trello = self.data.copy()
        if hasattr(self, 'objeto_edit') and self.objeto_edit:
            contrato_para_trello['objeto_editado'] = self.objeto_edit.text()

        # Log no terminal (aparece imediatamente)
        logging.info(f"🔄 Iniciando sincronização do contrato {self.data.get('numero', 'N/A')} com o Trello...")
        print(f"🔄 Iniciando sincronização do contrato {self.data.get('numero', 'N/A')} (status: {status_atual})")

        # Cria Worker para sincronização em background
        from integration.controller.trello_individual_controller import TrelloSyncWorker

        self._trello_thread = TrelloSyncWorker(
            self.trello_individual_ctrl, 
            contrato_para_trello, 
            status_atual
        )

        # Conecta o sinal de finalização
        self._trello_thread.finished.connect(self._on_trello_finished)

        # Feedback visual: desabilita botão e muda texto
        self.trello_button.setEnabled(False)
        self.trello_button.setText("Sincronizando...")

        # Inicia a thread
        self._trello_thread.start()

    def _on_trello_finished(self, success, message):
        """Callback chamado quando a sincronização termina."""
        import logging

        # Restaura o botão
        self.trello_button.setEnabled(True)
        self.trello_button.setText("CA-Trello")

        # Libera a referência da thread
        self._trello_thread = None

        # Mostra resultado
        if success:
            logging.info(f"✅ Sincronização concluída: {message}")
            print(f"✅ Sincronização concluída com sucesso!")

            # Extrai URL se disponível
            if isinstance(message, dict):
                short_url = message.get('shortUrl', '')
                card_name = message.get('name', '')
                QMessageBox.information(
                    self, 
                    "Trello - Sucesso", 
                    f"✅ Cartão sincronizado com sucesso!\n\n"
                    f"Nome: {card_name}\n"
                    f"URL: {short_url}"
                )
            else:
                QMessageBox.information(self, "Trello - Sucesso", f"✅ {message}")
        else:
            logging.error(f"❌ Erro na sincronização: {message}")
            print(f"❌ Erro na sincronização: {message}")
            QMessageBox.warning(
                self, 
                "Trello - Erro", 
                f"⚠️ Falha na sincronização:\n\n{message}"
            )
