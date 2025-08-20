# view/record_popup.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt

class RecordPopup(QDialog):
    """
    Uma janela popup que mostra uma lista de registros e desaparece
    quando o usuário clica em outro lugar.
    """
    def __init__(self, records, parent=None):
        super().__init__(parent)
        # Define a janela como um Popup, o que a faz se fechar automaticamente
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setMinimumSize(400, 150)
        self.setMaximumWidth(500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        list_widget = QListWidget()
        
        # Popula a lista com os registros ou mostra uma mensagem
        if records:
            for record in records:
                item = QListWidgetItem(record)
                # Torna os itens não selecionáveis (apenas para visualização)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                list_widget.addItem(item)
        else:
            list_widget.addItem("Nenhum registro encontrado para este contrato.")

        layout.addWidget(list_widget)

        # Herda o estilo da janela principal para manter a consistência visual
        if parent and parent.styleSheet():
            self.setStyleSheet(parent.styleSheet())
            list_widget.setStyleSheet("QListWidget { border: none; background-color: #2E2E2E; }")