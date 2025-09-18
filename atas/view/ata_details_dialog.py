# atas/view/ata_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QTabWidget, QWidget,
                             QDateEdit, QListWidget, QListWidgetItem, QInputDialog,
                             QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from utils.icon_loader import icon_manager
from datetime import datetime

class AtaDetailsDialog(QDialog):
    ata_updated = pyqtSignal()

    def __init__(self, ata_data, parent=None):
        super().__init__(parent)
        self.ata_data = ata_data
        self.setWindowTitle(f"Detalhes da Ata: {ata_data.contrato_ata_parecer}")
        self.setMinimumSize(800, 500)
        self.setWindowIcon(icon_manager.get_icon("edit"))

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_general_tab()
        self.create_registros_tab()

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("Salvar Alterações")
        save_button.setIcon(icon_manager.get_icon("save"))
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)

        close_button = QPushButton("Fechar")
        close_button.setIcon(icon_manager.get_icon("close"))
        close_button.clicked.connect(self.reject)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)
        self.load_data()

    def create_general_tab(self):
        general_tab = QWidget()
        layout = QFormLayout(general_tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.setor_le = QLineEdit()
        self.empresa_le = QLineEdit()
        self.objeto_le = QLineEdit()
        self.portaria_le = QLineEdit()
        
        self.celebracao_de = QDateEdit(calendarPopup=True)
        self.celebracao_de.setDisplayFormat("dd/MM/yyyy")
        self.termino_de = QDateEdit(calendarPopup=True)
        self.termino_de.setDisplayFormat("dd/MM/yyyy")
        
        layout.addRow(QLabel("<b>Setor:</b>"), self.setor_le)
        layout.addRow(QLabel("<b>Empresa:</b>"), self.empresa_le)
        layout.addRow(QLabel("<b>Objeto:</b>"), self.objeto_le)
        layout.addRow(QLabel("<b>Portaria de Fiscalização:</b>"), self.portaria_le)
        layout.addRow(QLabel("<b>Data de Celebração:</b>"), self.celebracao_de)
        layout.addRow(QLabel("<b>Data de Término:</b>"), self.termino_de)

        self.tabs.addTab(general_tab, "Informações Gerais")

    def create_registros_tab(self):
        registros_tab = QWidget()
        layout = QVBoxLayout(registros_tab)
        
        self.registro_list = QListWidget()
        layout.addWidget(self.registro_list)
        
        button_layout = QHBoxLayout()
        add_button = QPushButton("Adicionar Registro")
        add_button.setIcon(icon_manager.get_icon("add_comment"))
        add_button.clicked.connect(self.add_registro)
        button_layout.addWidget(add_button)
        
        delete_button = QPushButton("Excluir Selecionado")
        delete_button.setIcon(icon_manager.get_icon("delete"))
        delete_button.clicked.connect(self.delete_registro)
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        self.tabs.addTab(registros_tab, "Registros")

    def load_data(self):
        """Carrega os dados da ata nos campos da interface."""
        self.setor_le.setText(self.ata_data.setor or "")
        self.empresa_le.setText(self.ata_data.empresa or "")
        self.objeto_le.setText(self.ata_data.objeto or "")
        self.portaria_le.setText(self.ata_data.portaria_fiscalizacao or "")
        
        if self.ata_data.celebracao:
            self.celebracao_de.setDate(QDate.fromString(self.ata_data.celebracao, "yyyy-MM-dd"))
        if self.ata_data.termino:
            self.termino_de.setDate(QDate.fromString(self.ata_data.termino, "yyyy-MM-dd"))
            
        self.registro_list.clear()
        self.registro_list.addItems(self.ata_data.registros)

    def get_updated_data(self):
        return {
            'setor': self.setor_le.text(),
            'empresa': self.empresa_le.text(),
            'objeto': self.objeto_le.text(),
            'portaria_fiscalizacao': self.portaria_le.text(),
            'celebracao': self.celebracao_de.date().toString("yyyy-MM-dd"),
            'termino': self.termino_de.date().toString("yyyy-MM-dd")
        }

    def add_registro(self):
        """Abre uma janela de diálogo personalizada para adicionar um novo registro."""
        # Criação da janela de diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Registro")
        dialog.setMinimumSize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        layout.addWidget(text_edit)
        
        add_button = QPushButton("Fechar e Adicionar Registro")
        add_button.setIcon(icon_manager.get_icon("registrar_status"))
        layout.addWidget(add_button)

        def accept_and_add():
            text = text_edit.toPlainText().strip()
            if text:
                # Formata a data (sem hora) e o texto do comentário (sem status)
                timestamp = datetime.now().strftime("%d/%m/%Y")
                item_text = f"[{timestamp}] - {text}"
                
                self.registro_list.addItem(QListWidgetItem(item_text))
                dialog.accept() # Fecha a janela
            else:
                dialog.accept() # Fecha mesmo se estiver vazio

        add_button.clicked.connect(accept_and_add)
        dialog.exec()

    def delete_registro(self):
        for item in self.registro_list.selectedItems():
            self.registro_list.takeItem(self.registro_list.row(item))

    # (dentro da classe AtaDetailsDialog, no ficheiro atas/view/ata_details_dialog.py)

    def save_changes(self):
        """Emite o sinal para que o controller salve os dados e exibe uma mensagem."""
        self.ata_updated.emit()
        # A janela não fecha mais aqui, permitindo múltiplos salvamentos
        QMessageBox.information(self, "Sucesso", "Alterações salvas com sucesso!")
