import os
import sys
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton,
    QTabWidget, QTextEdit, QListWidgetItem, QApplication
)
from PyQt6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from model.uasg_model import resource_path

from view.abas_detalhes.general_tab import create_general_tab
from view.abas_detalhes.object_tab import create_object_tab
from view.abas_detalhes.status_tab import create_status_tab
from view.abas_detalhes.termo_adt import aba_termo_adt

class DetailsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Contrato")
        self.setFixedSize(800, 650)
        self.pdf_path = None

        self.load_styles()

        self.data = data
        self.main_layout = QVBoxLayout(self)

        self.radio_groups = {}  # Adicione esta linha
        self.radio_buttons = {}  # Adicione esta linha (se ainda não estiver presente)

        # Criar o TabWidget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Criar abas
        self.tabs.addTab(create_general_tab(self), "Informações Gerais")
        self.tabs.addTab(create_object_tab(self), "PDF do contrato")
        self.tabs.addTab(create_status_tab(self), "Status")
        self.tabs.addTab(aba_termo_adt(self), "Termo Aditivo")

        # Botão de salvar
        close_button = QPushButton("Salvar")
        close_button.clicked.connect(self.close_and_save)
        self.main_layout.addWidget(close_button)

        # Carregar dados salvos
        self.load_status()

    def registro_def(self):
        """Abre uma mini janela para adicionar um comentário com data, hora e status selecionado."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Registro")
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        add_button = QPushButton("Fechar e Adicionar Comentário")
        layout.addWidget(add_button)
        
        dialog.setLayout(layout)
        
        def add_comment():
            comment_text = text_edit.toPlainText().strip()
            if comment_text:
                timestamp = datetime.now().strftime("%d/%m/%Y")  # Formato da data
                status = self.status_dropdown.currentText()
                full_comment = f"{timestamp} - {comment_text} - {status}"
                item = QListWidgetItem(full_comment)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.comment_list.addItem(item)
                print(f"✅ Comentário adicionado: {full_comment}")
            dialog.accept()
        
        add_button.clicked.connect(add_comment)
        dialog.exec()

    def add_comment(self):
        """Adiciona um comentário na lista"""
        comment_text = self.comment_box.toPlainText().strip()
        if comment_text:
            item = QListWidgetItem(comment_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.comment_list.addItem(item)
            self.comment_box.clear()
            self.comment_list.clearSelection()
    
    def delete_comment(self):
        """Remove os comentários selecionados"""
        for i in range(self.comment_list.count() - 1, -1, -1):
            item = self.comment_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.comment_list.takeItem(i)
    
    def close_and_save(self):
        """Salva o status e os comentários ao fechar a janela"""
        self.save_status(id_contrato=self.data.get("id", ""), uasg=self.data.get("contratante", {}).get("orgao_origem", {}).get("unidade_gestora_origem", {}).get("codigo", ""))
    
    def save_status(self, id_contrato, uasg):
        """Salva o status, comentários e opções dos radio buttons em um arquivo separado para cada contrato dentro da UASG"""
        base_dir = Path(resource_path("status_glob"))  # Usa resource_path para garantir o caminho correto
        base_dir.mkdir(exist_ok=True)
        
        uasg_dir = base_dir / str(uasg)
        uasg_dir.mkdir(exist_ok=True)
        
        status_file = uasg_dir / f"{id_contrato}.json"
        
        status_data = {
            "id_contrato": id_contrato,
            "uasg": uasg,
            "status": self.status_dropdown.currentText(),
            "comments": [self.comment_list.item(i).text() for i in range(self.comment_list.count())],
            "objeto": self.objeto_edit.text(),
            "radio_options": {
                title: next(
                    (option for option, button in self.radio_buttons[title].items() if button.isChecked()),
                    "Não selecionado"
                ) for title in self.radio_buttons
            }
        }
        
        with status_file.open("w", encoding="utf-8") as file:
            json.dump(status_data, file, ensure_ascii=False, indent=4)
        
        print(f"Status salvo em {status_file}")
    
    def load_status(self):
        """Carrega os dados salvos no JSON"""
        uasg = self.data.get("contratante", {}).get("orgao_origem", {}).get("unidade_gestora_origem", {}).get("codigo", "")
        id_contrato = self.data.get("id", "")
        
        status_file = Path(resource_path("status_glob")) / str(uasg) / f"{id_contrato}.json"  # Usa resource_path
        
        if status_file.exists():
            with status_file.open("r", encoding="utf-8") as file:
                status_data = json.load(file)
                
                self.status_dropdown.setCurrentText(status_data.get("status", ""))
                self.objeto_edit.setText(status_data.get("objeto", "Não informado"))
                
                for title, selected_value in status_data.get("radio_options", {}).items():
                    if selected_value in self.radio_buttons.get(title, {}):
                        self.radio_buttons[title][selected_value].setChecked(True)
                
                self.comment_list.clear()
                for comment in status_data.get("comments", []):
                    item = QListWidgetItem(comment)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.comment_list.addItem(item)
                
                self.comment_list.clearSelection()
            
            print(f"Status carregado de {status_file}")
        else:
            print("Nenhum status salvo encontrado.")

    def copy_to_clipboard(self, line_edit):
        """Copia o texto do campo para a área de transferência"""
        clipboard = QApplication.clipboard()
        clipboard.setText(line_edit.text())

    def load_styles(self):
        """Carrega os estilos do arquivo style.qss"""
        style_path = resource_path("style.qss")  # Usa resource_path para garantir o caminho correto

        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠ Arquivo {style_path} não encontrado. Estilos não foram aplicados.")
