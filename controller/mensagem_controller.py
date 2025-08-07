# controller/mensagem_controller.py

import os
from PyQt6.QtWidgets import QApplication, QPushButton, QMessageBox
from view.mensagem_view import MensagemDialog
from model.uasg_model import resource_path

class MensagemController:
    def __init__(self, contract_data, parent=None):
        self.contract_data = contract_data
        self.templates = self._load_templates()
        self.current_template_path = None
        
        self.view = MensagemDialog(parent)
        
        self._populate_variables_list()
        self._create_template_buttons()
        
        # Conecta os sinais
        self.view.save_template_button.clicked.connect(self._save_current_template)
        self.view.copy_button.clicked.connect(self._copy_message_to_clipboard)
        
        # --- NOVA CONEXÃO ---
        # Atualiza a pré-visualização toda vez que o texto do editor mudar
        self.view.template_text_edit.textChanged.connect(self._update_preview)

    def show(self):
        """Exibe a janela de diálogo."""
        self.view.exec()

    def _load_templates(self):
        """Carrega os nomes e caminhos dos arquivos de template .txt."""
        templates = {}
        template_dir = resource_path("utils/msg/contratos")
        if os.path.isdir(template_dir):
            for filename in os.listdir(template_dir):
                if filename.endswith(".txt"):
                    name = os.path.splitext(filename)[0].replace('_', ' ').title()
                    templates[name] = os.path.join(template_dir, filename)
        return templates

    def _populate_variables_list(self):
        """Preenche a lista de variáveis com os dados do contrato."""
        # ... (código inalterado)
        self.view.variables_list.clear()
        all_data = {**self.contract_data, **self.contract_data.get('fornecedor', {})}
        for key, value in all_data.items():
            if isinstance(value, (str, int, float)) and value:
                self.view.variables_list.addItem(f"{{{{{key}}}}} : {value}")

    def _create_template_buttons(self):
        """Cria um botão para cada template encontrado."""
        for template_name, template_path in self.templates.items():
            button = QPushButton(template_name)
            button.clicked.connect(lambda checked, path=template_path: self._apply_template(path))
            self.view.template_buttons_layout.addWidget(button)

    def _apply_template(self, template_path):
        """Lê um arquivo de template, o exibe e atualiza a pré-visualização."""
        try:
            self.current_template_path = template_path
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            self.view.template_text_edit.setPlainText(template_content)
            # A pré-visualização será atualizada automaticamente pelo sinal textChanged
            
            template_name = os.path.basename(template_path)
            display_name = os.path.splitext(template_name)[0].replace('_', ' ').title()
            self.view.current_template_label.setText(f"'{display_name}'")

        except Exception as e:
            self.view.template_text_edit.setPlainText(f"Erro ao carregar o template:\n{e}")
            self.current_template_path = None
            self.view.current_template_label.setText("Erro ao carregar")

    # --- NOVA FUNÇÃO DE ATUALIZAÇÃO ---
    def _update_preview(self):
        """Aplica as variáveis ao texto do editor e exibe na pré-visualização."""
        current_text = self.view.template_text_edit.toPlainText()
        
        # Substitui as variáveis
        message = current_text
        all_data = {**self.contract_data, **self.contract_data.get('fornecedor', {})}
        for key, value in all_data.items():
             if isinstance(value, (str, int, float)):
                message = message.replace(f"{{{{{key}}}}}", str(value))
        
        self.view.preview_text_edit.setPlainText(message)

    def _save_current_template(self):
        """Salva o conteúdo atual do editor de texto."""
        # ... (código inalterado)
        if not self.current_template_path:
            QMessageBox.warning(self.view, "Nenhum Modelo", "Carregue um modelo antes de salvar.")
            return
        try:
            current_text = self.view.template_text_edit.toPlainText()
            with open(self.current_template_path, 'w', encoding='utf-8') as f:
                f.write(current_text)
            QMessageBox.information(self.view, "Sucesso", "Modelo salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Não foi possível salvar o modelo:\n{e}")

    def _copy_message_to_clipboard(self):
        """Copia a MENSAGEM PRONTA (da pré-visualização) para a área de transferência."""
        clipboard = QApplication.clipboard()
        # Copia o texto da PRÉ-VISUALIZAÇÃO, que já tem as variáveis aplicadas
        clipboard.setText(self.view.preview_text_edit.toPlainText())
        self.view.close()