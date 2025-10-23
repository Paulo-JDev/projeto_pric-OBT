from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QListWidgetItem, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import json
import sqlite3 # Adicionado
from datetime import datetime
from utils.icon_loader import icon_manager
from Contratos.model.uasg_model import UASGModel # Para _get_db_connection se necessário, ou usar o model passado

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

def delete_registro(registro_list):
    """Remove os registros selecionados"""
    for i in range(registro_list.count() - 1, -1, -1):
        item = registro_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            registro_list.takeItem(i)

def save_status(parent, data, model: UASGModel, status_dropdown, registro_list, objeto_edit, portaria_edit, termo_aditivo_edit, radio_buttons):
    """Salva o status, registros e comentários no banco de dados SQLite."""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")

    if not id_contrato or not uasg:
        print("Erro: ID do contrato ou UASG não encontrado para salvar o status.")
        return None, None
    
    link_data = {
        "link_contrato": parent.link_contrato_le.text(),
        "link_ta": parent.link_ta_le.text(),
        "link_portaria": parent.link_portaria_le.text(),
        "link_pncp_espc": parent.link_pncp_espc_le.text(),
        "link_portal_marinha": parent.link_portal_marinha_le.text()

    }

    model.save_contract_links(id_contrato, link_data)

    radio_options_dict = {
        "id_contrato": id_contrato,
        "uasg": uasg,
        "status": status_dropdown.currentText(),
        "registros": [registro_list.item(i).text() for i in range(registro_list.count())],
        #"comments": [comment_list.item(i).text() for i in range(comment_list.count())] if comment_list else [],
        "objeto": objeto_edit.text() if objeto_edit is not None else "",
        "radio_options": {
            title: next(
                (option for option, button in radio_buttons[title].items() if button.isChecked()),
                "Não selecionado"
            ) for title in radio_buttons
        },
        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    radio_options_json = json.dumps(radio_options_dict.get("radio_options"))

    conn = model._get_db_connection() # Usa o método do modelo passado
    cursor = conn.cursor()

    try:
        # Salvar/Atualizar status_contratos
        cursor.execute('''
            INSERT OR REPLACE INTO status_contratos
            (contrato_id, uasg_code, status, objeto_editado, portaria_edit, termo_aditivo_edit,radio_options_json, data_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            id_contrato, uasg, status_dropdown.currentText(),
            objeto_edit.text() if objeto_edit is not None else "",
            portaria_edit.text() if portaria_edit is not None else "",
            termo_aditivo_edit.text() if termo_aditivo_edit is not None else "",
            radio_options_json,
            radio_options_dict.get("data_registro") # Adicionado o valor de data_registro
        ))

        # Salvar registros_status (deletar antigos e inserir novos)
        cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (id_contrato,))
        registros_texts = [registro_list.item(i).text() for i in range(registro_list.count())]
        for texto in registros_texts:
            cursor.execute("INSERT INTO registros_status (contrato_id, uasg_code, texto) VALUES (?, ?, ?)", (id_contrato, uasg, texto))

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

def load_status(data, model: UASGModel, status_dropdown, objeto_edit, portaria_edit, termo_aditivo_edit, radio_buttons, registro_list, parent_dialog):
    """Carrega os dados de status, registros e comentários do banco de dados SQLite."""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")

    if not id_contrato:
        print("ID do contrato não encontrado para carregar o status.")
        return

    conn = model._get_db_connection()
    cursor = conn.cursor()

    links = model.get_contract_links(id_contrato)
    if links:
        parent_dialog.link_contrato_le.setText(links.get("link_contrato", ""))
        parent_dialog.link_ta_le.setText(links.get("link_ta", ""))
        parent_dialog.link_portaria_le.setText(links.get("link_portaria", ""))
        parent_dialog.link_pncp_espc_le.setText(links.get("link_pncp_espc", ""))
        parent_dialog.link_portal_marinha_le.setText(links.get("link_portal_marinha", ""))

    try:
        # Carregar status_contratos
        cursor.execute("SELECT status, objeto_editado, portaria_edit, termo_aditivo_edit,radio_options_json FROM status_contratos WHERE contrato_id = ?", (id_contrato,))
        status_row = cursor.fetchone()

        if status_row:
            status_dropdown.setCurrentText(status_row['status'] or "")
            if objeto_edit is not None:
                objeto_edit.setText(status_row['objeto_editado'] or data.get("objeto", "Não informado")) # Fallback para objeto original
            
            if portaria_edit is not None:
                portaria_edit.setText(status_row['portaria_edit'] or "")

            if termo_aditivo_edit is not None:
                termo_aditivo_edit.setText(status_row['termo_aditivo_edit'] or "")

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
            registro_list.clear() # Limpa a lista antes de adicionar
            cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (id_contrato,))
            registros_encontrados = cursor.fetchall() # Busca todos
            print(f"[load_status] Encontrados {len(registros_encontrados)} registros para o contrato {id_contrato}") # Depuração
            for row in registros_encontrados:
                item = QListWidgetItem(row['texto'])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                registro_list.addItem(item)
            registro_list.clearSelection() # Remove qualquer seleção residual
        else:
            print("[load_status] Aviso: registro_list é None.")
        
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

def copy_registros(parent_view, registro_list):
    """Copia o texto de todos os registros com a checkbox marcada."""
    selected_texts = []
    for i in range(registro_list.count()):
        item = registro_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            selected_texts.append(item.text())
    
    if not selected_texts:
        QMessageBox.information(parent_view, "Nada a Copiar", "Nenhum registro foi selecionado.")
        return

    # Junta os textos com uma quebra de linha entre eles
    text_to_copy = "\n".join(selected_texts)
    clipboard = QApplication.clipboard()
    clipboard.setText(text_to_copy)
    
    QMessageBox.information(parent_view, "Copiado", "O(s) registro(s) selecionado(s) foi/foram copiado(s) para a área de transferência.")
