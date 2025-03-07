from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

def create_object_tab(self):
    """Cria a aba para exibir o Objeto"""
    object_tab = QWidget()
    layout = QVBoxLayout(object_tab)

    key_label = QLabel("<b>Objeto:</b>")
    value_label = QLabel(self.objeto_edit.text())  # Pega do campo editável
    value_label.setWordWrap(True)

    layout.addWidget(key_label)
    layout.addWidget(value_label)

    return object_tab