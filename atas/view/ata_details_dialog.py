# atas/view/ata_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QTabWidget, QWidget,
                             QDateEdit, QListWidget, QListWidgetItem, QInputDialog,
                             QMessageBox, QTextEdit, QComboBox, QFrame)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from utils.icon_loader import icon_manager
from datetime import datetime
from Contratos.view.abas_detalhes.pdfs_view import create_link_input_row, open_link_in_browser

class AtaDetailsDialog(QDialog):
    ata_updated = pyqtSignal()

    def __init__(self, ata_data, parent=None):
        super().__init__(parent)
        self.ata_data = ata_data
        self.setWindowTitle(f"ATA: {ata_data.empresa} ({ata_data.contrato_ata_parecer})")
        self.setMinimumSize(800, 500)
        self.setWindowIcon(icon_manager.get_icon("edit"))

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_general_tab()
        self.create_links_tab()
        self.create_status_tab()

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
        """Cria a aba de Informações Gerais com os novos campos editáveis."""
        general_tab = QWidget()
        layout = QFormLayout(general_tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Campos de texto editáveis
        self.numero_le = QLineEdit()
        self.ano_le = QLineEdit()
        self.modalidade_le = QLineEdit()
        self.empresa_le = QLineEdit()
        self.objeto_le = QLineEdit()
        self.termo_aditivo_le = QLineEdit()
        self.portaria_le = QLineEdit()

        # Campos de data
        self.celebracao_de = QDateEdit(calendarPopup=True)
        self.celebracao_de.setDisplayFormat("dd/MM/yyyy")
        self.termino_de = QDateEdit(calendarPopup=True)
        self.termino_de.setDisplayFormat("dd/MM/yyyy")

        # Adiciona os campos ao layout
        layout.addRow(QLabel("<b>Número:</b>"), self.numero_le)
        layout.addRow(QLabel("<b>Ano:</b>"), self.ano_le)
        layout.addRow(QLabel("<b>Modalidade:</b>"), self.modalidade_le)
        layout.addRow(QLabel("<b>Empresa:</b>"), self.empresa_le)
        layout.addRow(QLabel("<b>Objeto:</b>"), self.objeto_le)
        layout.addRow(QLabel("<b>Termo Aditivo:</b>"), self.termo_aditivo_le)
        layout.addRow(QLabel("<b>Portaria de Fiscalização:</b>"), self.portaria_le)
        layout.addRow(QLabel("<b>Data de Celebração:</b>"), self.celebracao_de)
        layout.addRow(QLabel("<b>Data de Término:</b>"), self.termino_de)

        self.tabs.addTab(general_tab, "Informações Gerais")

    def create_status_tab(self):
        """Cria a aba 'Status' que agora contém o dropdown e os registros."""
        status_tab = QWidget()
        main_layout = QVBoxLayout(status_tab)

        # Dropdown de Status
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        status_label = QLabel("Status:")
        status_layout.addWidget(status_label)

        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems([
            "SEÇÃO ATAS", "EMPRESA", "SIGDEM", "ASSINADO", "PUBLICADO", "PORTARIA",
            "ALERTA PRAZO", "ATA GERADA", "NOTA TÉCNICA", "AGU", "PRORROGADO"
        ])
        self.status_dropdown.setFixedWidth(220)
        status_layout.addWidget(self.status_dropdown)
        main_layout.addLayout(status_layout)

        # Frame com a lista de registros
        registros_frame = QFrame()
        registros_frame.setFrameShape(QFrame.Shape.StyledPanel)
        registros_list_layout = QVBoxLayout(registros_frame)

        self.registro_list = QListWidget()
        self.registro_list.setWordWrap(True)
        registros_list_layout.addWidget(self.registro_list)
        main_layout.addWidget(registros_frame)

        # Botões de registro
        registro_buttons_layout = QHBoxLayout()
        add_button = QPushButton("Adicionar Registro")
        add_button.setIcon(icon_manager.get_icon("add_comment"))
        add_button.clicked.connect(self.add_registro)
        registro_buttons_layout.addWidget(add_button)

        delete_button = QPushButton("Excluir Selecionado")
        delete_button.setIcon(icon_manager.get_icon("delete"))
        delete_button.clicked.connect(self.delete_registro)
        registro_buttons_layout.addWidget(delete_button)

        main_layout.addLayout(registro_buttons_layout)
        self.tabs.addTab(status_tab, "Status")

    def create_links_tab(self):
        """Cria a aba para inserir os links."""
        links_tab = QWidget()
        layout = QFormLayout(links_tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.serie_ata_link_le = QLineEdit()
        self.portaria_link_le = QLineEdit()
        self.ta_link_le = QLineEdit()

        self.serie_ata_link_le, hbox_ata = create_link_input_row(self, "Link Série Ata:", "Cole aqui o link da Série da Ata (opcional)")
        self.portaria_link_le, hbox_portaria_ata = create_link_input_row(self, "Link Portaria:", "Cole aqui o link da Portaria (opcional)")
        self.ta_link_le, hox_ta_ata = create_link_input_row(self, "Link Termo Aditivo:", "Cole aqui o link do Termo Aditivo (opcional)")

        layout.addRow(QLabel("<b>Link Série Ata:</b>"), hbox_ata)
        layout.addRow(QLabel("<b>Link Portaria:</b>"), hbox_portaria_ata)
        layout.addRow(QLabel("<b>Link Termo Aditivo:</b>"), hox_ta_ata)

        self.tabs.addTab(links_tab, "Links Atas")

    def load_data(self):
        """Carrega os dados da ata nos campos da interface."""
        self.numero_le.setText(self.ata_data.numero or "")
        self.ano_le.setText(self.ata_data.ano or "")
        self.modalidade_le.setText(self.ata_data.modalidade or "")
        self.empresa_le.setText(self.ata_data.empresa or "")
        self.objeto_le.setText(self.ata_data.objeto or "")
        self.termo_aditivo_le.setText(self.ata_data.termo_aditivo or "")
        self.portaria_le.setText(self.ata_data.portaria_fiscalizacao or "")

        # Links
        self.serie_ata_link_le.setText(self.ata_data.serie_ata_link or "")
        self.portaria_link_le.setText(self.ata_data.portaria_link or "")
        self.ta_link_le.setText(self.ata_data.ta_link or "")

        if self.ata_data.celebracao:
            self.celebracao_de.setDate(QDate.fromString(self.ata_data.celebracao, "yyyy-MM-dd"))
        if self.ata_data.termino:
            self.termino_de.setDate(QDate.fromString(self.ata_data.termino, "yyyy-MM-dd"))

        # Registros
        self.registro_list.clear()
        for record_text in self.ata_data.registros:
            item = QListWidgetItem(record_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.registro_list.addItem(item)
        #self.registro_list.addItems(self.ata_data.registros)

        # Status
        self.status_dropdown.setCurrentText(self.ata_data.status)

    def get_updated_data(self):
        """Retorna um dicionário com os dados atualizados da interface."""
        return {
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'modalidade': self.modalidade_le.text(),
            'empresa': self.empresa_le.text(),
            'objeto': self.objeto_le.text(),
            'termo_aditivo': self.termo_aditivo_le.text(),
            'portaria_fiscalizacao': self.portaria_le.text(),
            'celebracao': self.celebracao_de.date().toString("yyyy-MM-dd"),
            'termino': self.termino_de.date().toString("yyyy-MM-dd"),
            'status': self.status_dropdown.currentText(),
            'serie_ata_link': self.serie_ata_link_le.text(),
            'portaria_link': self.portaria_link_le.text(),
            'ta_link': self.ta_link_le.text()
        }

    def add_registro(self):
        """Abre uma janela de diálogo para adicionar um novo registro."""
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
                timestamp = datetime.now().strftime("%d/%m/%Y")
                item_text = f"[{timestamp}] - {text}"

                # --- ALTERAÇÃO AQUI: Cria o item com checkbox ---
                item = QListWidgetItem(item_text)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.registro_list.addItem(item)
                # --- FIM DA ALTERAÇÃO ---
            dialog.accept()

        add_button.clicked.connect(accept_and_add)
        dialog.exec()

    def delete_registro(self):
        for i in range(self.registro_list.count() - 1, -1, -1):
            item = self.registro_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.registro_list.takeItem(i)

    # (dentro da classe AtaDetailsDialog, no ficheiro atas/view/ata_details_dialog.py)

    def save_changes(self):
        """Emite o sinal para que o controller salve os dados e exibe uma mensagem."""
        self.ata_updated.emit()
        # A janela não fecha mais aqui, permitindo múltiplos salvamentos
        QMessageBox.information(self, "Sucesso", "Alterações salvas com sucesso!")
