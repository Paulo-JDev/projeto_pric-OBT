# view/record_popup.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class RecordPopup(QDialog):
    """
    Uma janela popup que mostra uma lista de registros, com quebra de linha
    e um botão para ver mais detalhes.
    """
    # Sinal que será emitido com o ID do contrato quando o botão for clicado
    details_requested = pyqtSignal(str)

    def __init__(self, records, contrato_id, parent=None):
        super().__init__(parent)
        self.contrato_id = contrato_id  # Armazena o ID para usar depois

        # Configurações da janela
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setMinimumSize(450, 200) # Aumentei a altura para caber o botão
        self.setMaximumWidth(550)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        list_widget = QListWidget()
        # 1° -> HABILITA A QUEBRA DE LINHA AUTOMÁTICA
        list_widget.setWordWrap(True)
        
        if records:
            for record in records:
                item = QListWidgetItem(record)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                list_widget.addItem(item)
        else:
            list_widget.addItem("Nenhum registro encontrado para este contrato.")

        main_layout.addWidget(list_widget)

        # 2° -> CRIA O BOTÃO "MAIS INFORMAÇÕES"
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Empurra o botão para a direita
        
        details_button = QPushButton("Mais informações")
        details_button.clicked.connect(self.request_details) # Conecta ao método
        button_layout.addWidget(details_button)

        main_layout.addLayout(button_layout)

        # Aplica o estilo da janela principal para manter a consistência
        if parent and parent.styleSheet():
            self.setStyleSheet(parent.styleSheet())
            list_widget.setStyleSheet("QListWidget { border: none; background-color: #2E2E2E; }")
            details_button.setStyleSheet("QPushButton { min-width: 120px; }")

    def request_details(self):
        """ Emite o sinal com o ID do contrato e fecha o popup. """
        self.details_requested.emit(self.contrato_id)
        self.close()
