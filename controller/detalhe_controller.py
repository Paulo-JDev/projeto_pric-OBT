from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QListWidgetItem, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import json
from pathlib import Path
from datetime import datetime
from model.uasg_model import resource_path
from utils.icon_loader import icon_manager

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

def save_status(parent, data, status_dropdown, registro_list, comment_list, objeto_edit, radio_buttons):
    """Salva o status e os comentários em um arquivo JSON"""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")
    
    base_dir = Path(resource_path("status_glob"))  # Usa resource_path para garantir o caminho correto
    base_dir.mkdir(exist_ok=True)
    
    uasg_dir = base_dir / str(uasg)
    uasg_dir.mkdir(exist_ok=True)
    
    status_file = uasg_dir / f"{id_contrato}.json"
    
    status_data = {
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
    
    with status_file.open("w", encoding="utf-8") as file:
        json.dump(status_data, file, ensure_ascii=False, indent=4)
    
    print(f"Status salvo em {status_file}")
    
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

def load_status(data, status_dropdown, objeto_edit, radio_buttons, registro_list, comment_list):
    """Carrega os dados salvos no JSON"""
    try:
        uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")
        id_contrato = data.get("id", "")
        
        status_file = Path(resource_path("status_glob")) / str(uasg) / f"{id_contrato}.json"
        
        if status_file.exists():
            with status_file.open("r", encoding="utf-8") as file:
                status_data = json.load(file)
                
                status_dropdown.setCurrentText(status_data.get("status", ""))
                
                # Verifica se objeto_edit existe antes de acessá-lo
                if objeto_edit is not None:
                    objeto_edit.setText(status_data.get("objeto", "Não informado"))
                
            for title, selected_value in status_data.get("radio_options", {}).items():
                if title in radio_buttons and selected_value in radio_buttons[title]:
                    radio_buttons[title][selected_value].setChecked(True)
            
            # Carrega os registros se registro_list existir
            if registro_list is not None:
                registro_list.clear()
                for registro in status_data.get("registros", []):
                    item = QListWidgetItem(registro)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    registro_list.addItem(item)
            
            # Carrega os comentários
            if comment_list is not None:
                comment_list.clear()
                for comment in status_data.get("comments", []):
                    item = QListWidgetItem(comment)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    comment_list.addItem(item)
                
                comment_list.clearSelection()
            
            # Limpa seleção de registros, se existir
            if registro_list is not None:
                registro_list.clearSelection()
        
        print(f"Status carregado de {status_file}")
    except FileNotFoundError:
        print(f"Arquivo de status não encontrado: {status_file}") # Não é necessariamente um erro se o arquivo ainda não foi criado
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON do arquivo {status_file}: {e}")
    except Exception as e:
        print(f"Erro inesperado ao carregar status de {status_file} para contrato {id_contrato}, UASG {uasg}: {e}")

def copy_to_clipboard(line_edit):
    """Copia o texto do campo para a área de transferência"""
    clipboard = QApplication.clipboard()
    clipboard.setText(line_edit.text())
