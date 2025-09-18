# atas/view/ata_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QLabel, QPushButton, QHBoxLayout)
from utils.icon_loader import icon_manager

class AtaDetailsDialog(QDialog):
    """
    Uma janela para exibir os detalhes completos de uma Ata de Registro de Preços.
    """
    def __init__(self, ata_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes da Ata")
        self.setMinimumSize(600, 400)

        # Layout principal
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Adiciona os campos com os dados da ata
        self.numero_le = QLineEdit(str(ata_data.numero))
        self.ano_le = QLineEdit(str(ata_data.ano))
        self.empresa_le = QLineEdit(str(ata_data.empresa))
        self.objeto_le = QLineEdit(str(ata_data.objeto))
        self.parecer_le = QLineEdit(str(ata_data.contrato_ata_parecer))
        self.inicio_le = QLineEdit(str(ata_data.inicio or "N/A"))
        self.termino_le = QLineEdit(str(ata_data.termino or "N/A"))
        self.obs_le = QLineEdit(str(ata_data.observacoes or "Nenhuma"))
        
        # Torna todos os campos somente leitura
        for field in [self.numero_le, self.ano_le, self.empresa_le, self.objeto_le, 
                      self.parecer_le, self.inicio_le, self.termino_le, self.obs_le]:
            field.setReadOnly(True)

        # Adiciona os widgets ao layout de formulário
        form_layout.addRow(QLabel("<b>Número/Ano:</b>"), self.numero_le)
        form_layout.addRow(QLabel("<b>Empresa:</b>"), self.empresa_le)
        form_layout.addRow(QLabel("<b>Objeto:</b>"), self.objeto_le)
        form_layout.addRow(QLabel("<b>Contrato/Ata/Parecer:</b>"), self.parecer_le)
        form_layout.addRow(QLabel("<b>Data de Celebração:</b>"), self.inicio_le)
        form_layout.addRow(QLabel("<b>Data de Término:</b>"), self.termino_le)
        form_layout.addRow(QLabel("<b>Observações:</b>"), self.obs_le)
        
        main_layout.addLayout(form_layout)

        # Botão para fechar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Fechar")
        close_button.setIcon(icon_manager.get_icon("close"))
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)