from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt

def aba_termo_adt(self):
    termo_adt = QWidget()
    layout = QVBoxLayout(termo_adt)

    key_label = QLabel("Termo Aditivo:")
    termo_aditivo_info = self.data.get("links", {})

    combo = QComboBox()
    if isinstance(termo_aditivo_info, dict):
        combo.addItems(termo_aditivo_info.keys())

    value_label = QLabel()
    value_label.setOpenExternalLinks(True)  # Habilita clique nos links
    value_label.setWordWrap(True)
    value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)  # Permite interação

    def update_value():
        chave_selecionada = combo.currentText()
        url = termo_aditivo_info.get(chave_selecionada, "Nenhuma informação disponível.")
        
        if url.startswith("http"):  # Verifica se é um link válido
            link_html = f'<a href="{url}">{url}</a>'
        else:
            link_html = url  # Caso não seja um link, exibe o texto normal
        
        value_label.setText(link_html)

    combo.currentIndexChanged.connect(update_value)

    layout.addWidget(key_label)
    layout.addWidget(combo)
    layout.addWidget(value_label)

    update_value()  # Exibir o primeiro link ao carregar

    return termo_adt
