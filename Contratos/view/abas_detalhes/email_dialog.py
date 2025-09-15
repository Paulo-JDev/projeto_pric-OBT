from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class EmailDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enviar Relatório por E-mail")
        self.setMinimumWidth(450)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self.selected_file_path = ""

        main_layout = QVBoxLayout(self)
        
        # Campo para o e-mail do destinatário
        email_label = QLabel("E-mail do Destinatário:")
        self.recipient_email_input = QLineEdit()
        self.recipient_email_input.setPlaceholderText("exemplo@email.com")
        main_layout.addWidget(email_label)
        main_layout.addWidget(self.recipient_email_input)

        # Seção para selecionar o arquivo
        file_layout = QHBoxLayout()
        self.select_file_button = QPushButton("Selecionar Planilha")
        self.select_file_button.setIcon(icon_manager.get_icon("open-folder"))
        self.select_file_button.clicked.connect(self._select_file)
        file_layout.addWidget(self.select_file_button)
        
        self.selected_file_label = QLabel("Escolha a planilha referente ao contrato")
        self.selected_file_label.setStyleSheet("font-style: italic; color: #aaa;")
        file_layout.addWidget(self.selected_file_label)
        file_layout.addStretch()
        main_layout.addLayout(file_layout)

        main_layout.addStretch()

        # Botões de Enviar e Cancelar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.send_button = QPushButton("Enviar E-mail")
        self.send_button.setIcon(icon_manager.get_icon("icon_send"))
        self.send_button.clicked.connect(self.accept) # Fecha a janela indicando sucesso
        button_layout.addWidget(self.send_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject) # Fecha a janela indicando cancelamento
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def _select_file(self):
        """Abre uma janela para o usuário selecionar um arquivo de planilha."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Planilha",
            "",
            "Planilhas (*.xlsx *.xls *.ods);;Todos os Arquivos (*)"
        )
        if file_path:
            self.selected_file_path = file_path
            # Mostra apenas o nome do arquivo, e não o caminho completo
            file_name = file_path.split('/')[-1]
            self.selected_file_label.setText(file_name)
            self.selected_file_label.setStyleSheet("") # Remove o estilo itálico

    def get_data(self):
        """Retorna os dados inseridos pelo usuário."""
        return {
            "recipient_email": self.recipient_email_input.text(),
            "file_path": self.selected_file_path
        }