# view/edit_object_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from utils.icon_loader import icon_manager

class EditObjectDialog(QDialog):
    # Sinal que emitirá o texto salvo
    text_saved = pyqtSignal(str)

    def __init__(self, current_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Objeto do Contrato")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(parent.styleSheet()) # Herda o estilo da janela pai

        main_layout = QVBoxLayout(self)

        # Área de texto que permite múltiplas linhas
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(current_text)
        main_layout.addWidget(self.text_edit)

        # Layout para os botões
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Empurra os botões para a direita

        # Botão de Salvar
        self.save_button = QPushButton("Salvar e Fechar")
        self.save_button.setIcon(icon_manager.get_icon("concluido"))
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
        
        # Botão de Cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setIcon(icon_manager.get_icon("close"))
        self.cancel_button.clicked.connect(self.reject) # .reject() é o padrão para fechar um QDialog sem sucesso
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def save_and_close(self):
        """Emite o sinal com o texto atual e fecha a janela."""
        edited_text = self.text_edit.toPlainText()
        self.text_saved.emit(edited_text)
        self.accept() # .accept() fecha o QDialog indicando sucesso