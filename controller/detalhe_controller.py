from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QListWidgetItem, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import json
import sqlite3 # Adicionado
from pathlib import Path
from datetime import datetime
from utils.icon_loader import icon_manager
from model.uasg_model import UASGModel # Para _get_db_connection se necessário, ou usar o model passado

SUCCESS_MSG_TIMEOUT_MS = 300

def registro_def(parent, registro_list, status_dropdown):
    """Abre uma mini janela para adicionar um comentário com data, hora e status selecionado."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Adicionar Registro")
    layout = QVBoxLayout()
    
    text_edit = QTextEdit()
    layout.addWidget(text_edit)
    
    add_button = QPushButton("Fechar e Adicionar Registro")
    add_button.setIcon(icon_manager.get_icon("registrar_status"))
    layout.addWidget(add_button)
    
    dialog.setLayout(layout)
    
    def add_registro():
        comment_text = text_edit.toPlainText().strip()
        if comment_text:
            timestamp = datetime.now().strftime("%d/%m/%Y")  # Formato da data
            status = status_dropdown.currentText()
            full_comment = f"{timestamp} - {comment_text} - {status}"
            item = QListWidgetItem(full_comment)
            item.setCheckState(Qt.CheckState.Unchecked)
            registro_list.addItem(item)  # Adiciona à lista de registros
            print(f"✅ Registro adicionado: {full_comment}")
        dialog.accept()
    
    add_button.clicked.connect(add_registro)
    dialog.exec()

def add_comment(parent, comment_list):
    """Abre uma mini janela para adicionar um comentário."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Adicionar Comentário")
    layout = QVBoxLayout()
    
    text_edit = QTextEdit()
    layout.addWidget(text_edit)
    
    add_button = QPushButton("Fechar e Adicionar Comentário")
    add_button.setIcon(icon_manager.get_icon("comments"))
    layout.addWidget(add_button)
    
    dialog.setLayout(layout)
    
    def add_comment_func():
        comment_text = text_edit.toPlainText().strip()
        if comment_text:
            full_comment = f"{comment_text}"
            item = QListWidgetItem(full_comment)
            item.setCheckState(Qt.CheckState.Unchecked)
            comment_list.addItem(item)  # Adiciona à lista de comentários
            print(f"✅ Comentário adicionado: {full_comment}")
        dialog.accept()
    
    add_button.clicked.connect(add_comment_func)
    dialog.exec()

def delete_comment(comment_list):
    """Remove os comentários selecionados"""
    for i in range(comment_list.count() - 1, -1, -1):
        item = comment_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            comment_list.takeItem(i)

def delete_registro(registro_list):
    """Remove os registros selecionados"""
    for i in range(registro_list.count() - 1, -1, -1):
        item = registro_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            registro_list.takeItem(i)

def save_status(parent, data, model: UASGModel, status_dropdown, registro_list, comment_list, objeto_edit, radio_buttons):
    """Salva o status, registros e comentários no banco de dados SQLite."""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")

    if not id_contrato or not uasg:
        print("Erro: ID do contrato ou UASG não encontrado para salvar o status.")
        return None, None

    radio_options_dict = {
        "id_contrato": id_contrato,
        "uasg": uasg,
        "status": status_dropdown.currentText(),
        "registros": [registro_list.item(i).text() for i in range(registro_list.count())],
        "comments": [comment_list.item(i).text() for i in range(comment_list.count())],
        "objeto": objeto_edit.text() if objeto_edit is not None else "",
        "radio_options": {
            title: next(
                (option for option, button in radio_buttons[title].items() if button.isChecked()),
                "Não selecionado"
            ) for title in radio_buttons
        }
    }
    radio_options_json = json.dumps(radio_options_dict.get("radio_options"))

    conn = model._get_db_connection() # Usa o método do modelo passado
    cursor = conn.cursor()

    try:
        # Salvar/Atualizar status_contratos
        cursor.execute('''
            INSERT OR REPLACE INTO status_contratos 
            (contrato_id, uasg_code, status, objeto_editado, radio_options_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            id_contrato, uasg, status_dropdown.currentText(),
            objeto_edit.text() if objeto_edit is not None else "",
            radio_options_json
        ))

        # Salvar registros_status (deletar antigos e inserir novos)
        cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (id_contrato,))
        registros_texts = [registro_list.item(i).text() for i in range(registro_list.count())]
        for texto in registros_texts:
            cursor.execute("INSERT INTO registros_status (contrato_id, uasg_code, texto) VALUES (?, ?, ?)", (id_contrato, uasg, texto))

        # Salvar comentarios_status (deletar antigos e inserir novos)
        cursor.execute("DELETE FROM comentarios_status WHERE contrato_id = ?", (id_contrato,))
        comentarios_texts = [comment_list.item(i).text() for i in range(comment_list.count())]
        for texto in comentarios_texts:
            cursor.execute("INSERT INTO comentarios_status (contrato_id, uasg_code, texto) VALUES (?, ?, ?)", (id_contrato, uasg, texto))

        conn.commit()
        print(f"Status, registros e comentários para o contrato {id_contrato} (UASG: {uasg}) salvos no banco de dados.")
    except sqlite3.Error as e:
        print(f"Erro ao salvar status no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return id_contrato, uasg

def show_success_message(parent):
    """Mostra uma mensagem de sucesso que se fecha automaticamente"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle("Concluído")
    msg_box.setText("Dados salvos com sucesso!")
    msg_box.open()
    
    # Fechar a mensagem automaticamente depois de 300ms
    QTimer.singleShot(SUCCESS_MSG_TIMEOUT_MS, msg_box.close)

def load_status(data, model: UASGModel, status_dropdown, objeto_edit, radio_buttons, registro_list, comment_list):
    """Carrega os dados de status, registros e comentários do banco de dados SQLite."""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")

    if not id_contrato:
        print("ID do contrato não encontrado para carregar o status.")
        return

    conn = model._get_db_connection()
    cursor = conn.cursor()

    try:
        # Carregar status_contratos
        cursor.execute("SELECT status, objeto_editado, radio_options_json FROM status_contratos WHERE contrato_id = ?", (id_contrato,))
        status_row = cursor.fetchone()

        if status_row:
            status_dropdown.setCurrentText(status_row['status'] or "")
            if objeto_edit is not None:
                objeto_edit.setText(status_row['objeto_editado'] or data.get("objeto", "Não informado")) # Fallback para objeto original
            
            if status_row['radio_options_json']:
                try:
                    radio_options = json.loads(status_row['radio_options_json'])
                    for title, selected_value in radio_options.items():
                        if title in radio_buttons and selected_value in radio_buttons[title]:
                            radio_buttons[title][selected_value].setChecked(True)
                except json.JSONDecodeError:
                    print(f"Erro ao decodificar radio_options_json para contrato {id_contrato}")
        else:
            # Se não houver status salvo, usar o objeto original
            if objeto_edit is not None:
                objeto_edit.setText(data.get("objeto", "Não informado"))

        # Carregar registros_status
        if registro_list is not None:
            registro_list.clear()
            cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (id_contrato,))
            for row in cursor.fetchall():
                item = QListWidgetItem(row['texto'])
                item.setCheckState(Qt.CheckState.Unchecked)
                registro_list.addItem(item)
            registro_list.clearSelection()

        # Carregar comentarios_status
        if comment_list is not None:
            comment_list.clear()
            cursor.execute("SELECT texto FROM comentarios_status WHERE contrato_id = ?", (id_contrato,))
            for row in cursor.fetchall():
                item = QListWidgetItem(row['texto'])
                item.setCheckState(Qt.CheckState.Unchecked)
                comment_list.addItem(item)
            comment_list.clearSelection()
        
        if status_row:
            print(f"Status, registros e comentários para o contrato {id_contrato} carregados do banco de dados.")
        else:
            print(f"Nenhum status salvo encontrado para o contrato {id_contrato} no banco de dados. Usando valores padrão/originais.")

    except sqlite3.Error as e:
        print(f"Erro ao carregar status do banco de dados para contrato {id_contrato}: {e}")
    except Exception as e:
        print(f"Erro inesperado ao carregar status para contrato {id_contrato}, UASG {uasg}: {e}")
    finally:
        conn.close()

def copy_to_clipboard(line_edit):
    """Copia o texto do campo para a área de transferência"""
    clipboard = QApplication.clipboard()
    clipboard.setText(line_edit.text())
