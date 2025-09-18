# atas/view/add_ata_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.icon_loader import icon_manager

class AddAtaDialog(QDialog):
    ata_added = pyqtSignal(dict)  # Sinal para notificar quando uma ata for adicionada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Nova Ata")
        self.setFixedSize(450, 350)
        self.setWindowIcon(icon_manager.get_icon("plus"))
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da janela de adicionar ata."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("Nova Ata Administrativa")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #8AB4F7; margin-bottom: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Formulário
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(15)
        
        # Campos obrigatórios com estilo
        label_style = "font-weight: bold; color: #333;"
        input_style = "padding: 8px; border: 2px solid #ddd; border-radius: 5px; font-size: 12px;"
        
        # Número
        numero_label = QLabel("Número*:")
        numero_label.setStyleSheet(label_style)
        self.numero_edit = QLineEdit()
        self.numero_edit.setPlaceholderText("Ex: 001")
        self.numero_edit.setStyleSheet(input_style)
        form_layout.addRow(numero_label, self.numero_edit)
        
        # Ano
        ano_label = QLabel("Ano*:")
        ano_label.setStyleSheet(label_style)
        self.ano_edit = QLineEdit()
        self.ano_edit.setPlaceholderText("Ex: 2024")
        self.ano_edit.setStyleSheet(input_style)
        form_layout.addRow(ano_label, self.ano_edit)
        
        # Empresa
        empresa_label = QLabel("Empresa*:")
        empresa_label.setStyleSheet(label_style)
        self.empresa_edit = QLineEdit()
        self.empresa_edit.setPlaceholderText("Nome da empresa contratada")
        self.empresa_edit.setStyleSheet(input_style)
        form_layout.addRow(empresa_label, self.empresa_edit)
        
        # Campos opcionais
        optional_style = "font-weight: bold; color: #666;"
        
        # Objeto
        objeto_label = QLabel("Objeto:")
        objeto_label.setStyleSheet(optional_style)
        self.objeto_edit = QLineEdit()
        self.objeto_edit.setPlaceholderText("Descrição do objeto (opcional)")
        self.objeto_edit.setStyleSheet(input_style)
        form_layout.addRow(objeto_label, self.objeto_edit)
        
        # Contrato/Ata/Parecer
        contrato_label = QLabel("Contrato/Ata/Parecer:")
        contrato_label.setStyleSheet(optional_style)
        self.contrato_edit = QLineEdit()
        self.contrato_edit.setPlaceholderText("Número do contrato/parecer (opcional)")
        self.contrato_edit.setStyleSheet(input_style)
        form_layout.addRow(contrato_label, self.contrato_edit)
        
        layout.addLayout(form_layout)
        
        # Nota informativa
        info_label = QLabel("* Campos obrigatórios\n\n"
                          "💡 Dica: Após adicionar, clique com o botão direito na ata\n"
                          "para ver e editar mais detalhes como datas e observações.")
        info_label.setStyleSheet(
            "font-size: 11px; "
            "color: #666; "
            "background-color: #f0f8ff; "
            "padding: 10px; "
            "border-radius: 5px; "
            "border: 1px solid #ddd;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setIcon(icon_manager.get_icon("delete"))
        self.cancel_button.setStyleSheet(
            "QPushButton { "
            "background-color: #f44336; "
            "color: white; "
            "font-weight: bold; "
            "padding: 10px 20px; "
            "border: none; "
            "border-radius: 5px; "
            "} "
            "QPushButton:hover { background-color: #d32f2f; }"
        )
        self.cancel_button.clicked.connect(self.reject)
        
        self.add_button = QPushButton("Adicionar Ata")
        self.add_button.setIcon(icon_manager.get_icon("aproved"))
        self.add_button.setStyleSheet(
            "QPushButton { "
            "background-color: #4CAF50; "
            "color: white; "
            "font-weight: bold; "
            "padding: 10px 20px; "
            "border: none; "
            "border-radius: 5px; "
            "} "
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.add_button.clicked.connect(self.add_ata)
        self.add_button.setDefault(True)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        
        layout.addLayout(buttons_layout)
        
        # Foco inicial no campo número
        self.numero_edit.setFocus()
        
    def add_ata(self):
        """Valida e adiciona a nova ata."""
        # Validação dos campos obrigatórios
        numero = self.numero_edit.text().strip()
        ano = self.ano_edit.text().strip()
        empresa = self.empresa_edit.text().strip()
        
        if not numero:
            QMessageBox.warning(self, "Campo Obrigatório", 
                              "O campo 'Número' é obrigatório!")
            self.numero_edit.setFocus()
            return
            
        if not ano:
            QMessageBox.warning(self, "Campo Obrigatório", 
                              "O campo 'Ano' é obrigatório!")
            self.ano_edit.setFocus()
            return
            
        if not ano.isdigit() or len(ano) != 4:
            QMessageBox.warning(self, "Ano Inválido", 
                              "O ano deve conter exatamente 4 dígitos!")
            self.ano_edit.setFocus()
            return
            
        if not empresa:
            QMessageBox.warning(self, "Campo Obrigatório", 
                              "O campo 'Empresa' é obrigatório!")
            self.empresa_edit.setFocus()
            return
        
        # Cria o dicionário com os dados da nova ata
        nova_ata = {
            'numero': numero,
            'ano': int(ano),
            'empresa': empresa,
            'objeto': self.objeto_edit.text().strip() or "Não informado",
            'contrato_ata_parecer': self.contrato_edit.text().strip() or "Não informado",
            'termino': None,  # Será definido posteriormente via detalhes
            'inicio': None,
            'observacoes': ""
        }
        
        # Emite o sinal com os dados da nova ata
        self.ata_added.emit(nova_ata)
        self.accept()
        
    def keyPressEvent(self, event):
        """Permite usar Enter para adicionar e Esc para cancelar."""
        from PyQt6.QtCore import Qt
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.add_ata()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)