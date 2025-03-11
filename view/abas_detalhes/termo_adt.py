from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
import json

def aba_termo_adt(self):
    """Cria a aba para exibir informações do Termo Aditivo."""
    termo_adt = QWidget()
    layout = QVBoxLayout(termo_adt)
    
    key_label = QLabel("Termo Aditivo:")
    termo_aditivo_info = self.data.get("links", "Nenhuma informação disponível.")
    #termo_aditivo_info = self.data.get("links", "Nenhuma informação disponível.")
    #termo_espefico = termo_aditivo_info.get("historico", "Nada informado")


    # Se for um dicionário, formatamos como JSON legível
    # if isinstance(termo_aditivo_info, dict):
    #     termo_aditivo_info = json.dumps(termo_aditivo_info, indent=4, ensure_ascii=False)
    if isinstance(termo_aditivo_info, dict):
        termo_especifico = termo_aditivo_info.get("historico", "Nenhuma informação disponível.")
    else:
        termo_especifico = termo_aditivo_info

    value_label = QLabel(termo_especifico)
    value_label.setWordWrap(True)

    layout.addWidget(key_label)
    layout.addWidget(value_label)

    return termo_adt
