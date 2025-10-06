# controller/mensagem_controller.py

import os
from PyQt6.QtWidgets import (QApplication, QPushButton, QMessageBox, 
                             QInputDialog, QDialog, QVBoxLayout, QTextEdit, QListWidgetItem)
from PyQt6.QtCore import Qt # Certifique-se de que Qt está importado

from Contratos.view.mensagem_view import MensagemDialog
from Contratos.model.uasg_model import UASGModel,resource_path
from Contratos.model.models import RegistroMensagem

from datetime import datetime
import locale
import sqlite3

class MensagemController:
    def __init__(self, contract_data, model: UASGModel, parent=None):
        self.contract_data = contract_data
        self.model = model
        self.templates = self._load_templates()
        self.current_template_path = None
        
        self.view = MensagemDialog(parent)
        
        self._populate_variables_list()
        self._create_template_buttons()

        self._load_comments()
        
        # Conecta os sinais
        self.view.save_template_button.clicked.connect(self._save_current_template)
        self.view.copy_button.clicked.connect(self._copy_message_to_clipboard)
        self.view.template_text_edit.textChanged.connect(self._update_preview)

        self.view.add_comment_button.clicked.connect(self._add_comment)
        self.view.delete_comment_button.clicked.connect(self._delete_comment)
        self.view.save_comments_button.clicked.connect(self._save_comments)
        self.view.copy_comment_button.clicked.connect(self._copy_selected_comments)

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

    # ============================== Registro de Comentários =============================
    def _load_comments(self):
        """Carrega os comentários salvos no banco de dados para a lista usando SQLAlchemy."""
        self.view.comment_list.clear()
        contrato_id = self.contract_data.get('id')
        if not contrato_id:
            return

        # Pega a sessão do SQLAlchemy a partir do modelo
        db_session = self.model._get_db_session()
        try:
            # Busca os registros usando a query do ORM
            registros = db_session.query(RegistroMensagem).filter(RegistroMensagem.contrato_id == contrato_id).all()
            
            for reg in registros:
                item = QListWidgetItem(reg.texto)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.view.comment_list.addItem(item)
                
        except Exception as e:
            print(f"Erro ao carregar comentários com SQLAlchemy: {e}")
        finally:
            db_session.close() # Sempre fecha a sessão

    def _add_comment(self):
        """Abre uma janela customizada para adicionar um novo comentário."""
        # Substituímos o QInputDialog.getText por um QDialog customizado
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Adicionar Comentário")
        # Definimos um tamanho similar ao das outras janelas de registro
        dialog.setMinimumSize(500, 300) 

        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("Digite seu comentário ou registro aqui...")
        layout.addWidget(text_edit)
        
        add_button = QPushButton("Adicionar e Fechar")
        layout.addWidget(add_button)
        
        # Função para adicionar o texto à lista e fechar a janela
        def add_and_close():
            text = text_edit.toPlainText().strip()
            if text:
                timestamp = datetime.now().strftime("%d/%m/%Y")
                full_comment = f"[{timestamp}] - {text}"
                item = QListWidgetItem(full_comment)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.view.comment_list.addItem(item)
            dialog.accept()

        add_button.clicked.connect(add_and_close)
        dialog.exec()

    def _delete_comment(self):
        """Exclui os comentários que estão com a checkbox marcada."""
        # Itera de trás para frente para evitar problemas de índice ao remover itens
        for i in range(self.view.comment_list.count() - 1, -1, -1):
            item = self.view.comment_list.item(i)
            # Verifica se a checkbox está marcada
            if item.checkState() == Qt.CheckState.Checked:
                self.view.comment_list.takeItem(i)
    
    # --- NOVO MÉTODO PARA COPIAR ---
    def _copy_selected_comments(self):
        """Copia o texto de todos os comentários com a checkbox marcada."""
        selected_texts = []
        for i in range(self.view.comment_list.count()):
            item = self.view.comment_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_texts.append(item.text())
        
        if not selected_texts:
            QMessageBox.information(self.view, "Nada a Copiar", "Nenhum comentário foi selecionado.")
            return

        # Junta os textos com uma quebra de linha entre eles
        text_to_copy = "\n".join(selected_texts)
        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)
        
        QMessageBox.information(self.view, "Copiado", "O(s) comentário(s) selecionado(s) foi/foram copiado(s) para a área de transferência.")
            
    def _save_comments(self):
        """Salva os comentários da lista no banco de dados usando a sessão SQLAlchemy."""
        contrato_id = self.contract_data.get('id')
        if not contrato_id:
            QMessageBox.warning(self.view, "Erro", "ID do contrato não encontrado.")
            return

        # Pega a sessão do SQLAlchemy a partir do modelo
        db_session = self.model._get_db_session()
        try:
            # Estratégia "Apaga e Recria" com SQLAlchemy
            # 1. Deleta todos os registros existentes para este contrato
            db_session.query(RegistroMensagem).filter(RegistroMensagem.contrato_id == contrato_id).delete(synchronize_session=False)

            # 2. Pega os textos da interface
            comments_texts = [self.view.comment_list.item(i).text() for i in range(self.view.comment_list.count())]
            
            # 3. Adiciona os novos registros à sessão
            for texto in comments_texts:
                novo_registro = RegistroMensagem(contrato_id=contrato_id, texto=texto)
                db_session.add(novo_registro)
            
            # 4. Confirma a transação (salva tudo no banco de dados)
            db_session.commit()
            
            QMessageBox.information(self.view, "Sucesso", "Comentários salvos com sucesso!")

        except Exception as e:
            QMessageBox.critical(self.view, "Erro de Banco de Dados", f"Não foi possível salvar os comentários:\n{e}")
            db_session.rollback() # Desfaz as alterações em caso de erro
        finally:
            db_session.close() # Sempre fecha a sessão