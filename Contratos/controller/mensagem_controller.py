# controller/mensagem_controller.py

import os
from PyQt6.QtWidgets import QApplication, QPushButton, QMessageBox
from Contratos.view.mensagem_view import MensagemDialog
from Contratos.model.uasg_model import resource_path
from Contratos.model.uasg_model import UASGModel
from datetime import datetime
import locale

class MensagemController:
    def __init__(self, contract_data, model: UASGModel, parent=None):
        self.contract_data = contract_data
        self.model = model
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
        """Preenche a lista de variáveis com os dados do contrato e as novas variáveis dinâmicas."""
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except locale.Error:
            print("Aviso: Locale 'pt_BR.UTF-8' não encontrado. Usando o padrão do sistema.")

        self.view.variables_list.clear()
        
        hoje = datetime.now()
        
        # --- LÓGICA REPETIDA PARA CONSISTÊNCIA ---
        objeto_editado_db = ""
        conn = self.model._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT objeto_editado FROM status_contratos WHERE contrato_id = ?", (self.contract_data.get('id'),))
            result = cursor.fetchone()
            if result and result['objeto_editado']:
                objeto_editado_db = result['objeto_editado']
        finally:
            conn.close()
            
        objeto_completo_original = self.contract_data.get('objeto', '')
        objeto_editado_final = objeto_editado_db if objeto_editado_db else objeto_completo_original
        
        vigencia_fim_str = self.contract_data.get('vigencia_fim')
        vigencia_fim_formatada = "N/A"
        if vigencia_fim_str:
            try:
                dt_obj = datetime.strptime(vigencia_fim_str, "%Y-%m-%d")
                vigencia_fim_formatada = dt_obj.strftime("%d%b%Y").upper()
            except ValueError:
                vigencia_fim_formatada = "Data Inválida"

        all_data = {
            **self.contract_data, 
            **self.contract_data.get('fornecedor', {}),
            'objeto_completo': objeto_completo_original,
            'objeto_editado': objeto_editado_final,
            'dia_hoje': hoje.strftime("%d"),
            'mes_hoje': hoje.strftime("%b").upper(),
            'vigencia_fim_formatada': vigencia_fim_formatada
        }
        
        # REMOVIDA A LÓGICA QUE RENOMEAVA 'objeto' PARA 'objeto_editado'
        for key, value in all_data.items():
            if isinstance(value, (str, int, float)) and value:
                # Oculta o 'objeto' original para não confundir, já que temos as duas novas variáveis
                if key != 'objeto':
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
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        except locale.Error:
            pass # Ignora o erro se o locale não estiver disponível

        current_text = self.view.template_text_edit.toPlainText()
        
        # --- LÓGICA DE CRIAÇÃO DE VARIÁVEIS ADICIONADA AQUI ---
        hoje = datetime.now()
        objeto_editado_db = ""
        # Precisamos de uma instância do model para acessar o DB
        conn = self.model._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT objeto_editado FROM status_contratos WHERE contrato_id = ?", (self.contract_data.get('id'),))
            result = cursor.fetchone()
            if result and result['objeto_editado']:
                objeto_editado_db = result['objeto_editado']
        finally:
            conn.close()

        # O objeto completo sempre virá do dado original do contrato
        objeto_completo_original = self.contract_data.get('objeto', '')
        # Se não houver objeto editado no DB, use o original como fallback
        objeto_editado_final = objeto_editado_db if objeto_editado_db else objeto_completo_original
        
        vigencia_fim_str = self.contract_data.get('vigencia_fim')
        vigencia_fim_formatada = "N/A"
        if vigencia_fim_str:
            try:
                dt_obj = datetime.strptime(vigencia_fim_str, "%Y-%m-%d")
                vigencia_fim_formatada = dt_obj.strftime("%d%b%Y").upper()
            except ValueError:
                vigencia_fim_formatada = "Data Inválida"

        # ALTERADO: Dicionário de dados agora tem as duas versões do objeto
        all_data = {
            **self.contract_data, 
            **self.contract_data.get('fornecedor', {}),
            'objeto_completo': objeto_completo_original,
            'objeto_editado': objeto_editado_final,
            'dia_hoje': hoje.strftime("%d"),
            'mes_hoje': hoje.strftime("%b").upper(),
            'vigencia_fim_formatada': vigencia_fim_formatada
        }
        
        # --- LÓGICA DE SUBSTITUIÇÃO SIMPLIFICADA E CORRIGIDA ---
        message = current_text
        for key, value in all_data.items():
            # A verificação 'isinstance' previne erros com valores nulos ou de outros tipos
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