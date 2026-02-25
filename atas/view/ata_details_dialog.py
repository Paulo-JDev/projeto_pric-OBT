# atas/view/ata_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QTabWidget, QWidget,
                             QDateEdit, QListWidget, QListWidgetItem, QInputDialog,
                             QMessageBox, QTextEdit, QComboBox, QFrame, QApplication)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from utils.icon_loader import icon_manager
from datetime import datetime
from Contratos.view.abas_detalhes.pdfs_view import create_link_input_row, open_link_in_browser
from atas.view.abas_detalhes.fiscalizacao_ata_tab import create_fiscalizacao_ata_tab
from atas.controller.controller_fiscal_ata import save_fiscalizacao_ata, load_fiscalizacao_ata

class AtaDetailsDialog(QDialog):
    ata_updated = pyqtSignal()

    def __init__(self, ata_data, model, parent=None):
        super().__init__(parent)
        self.ata_data = ata_data
        self.model = model
        self.setWindowTitle(f"ATA: {ata_data.empresa} ({ata_data.contrato_ata_parecer})")
        self.setMinimumSize(800, 500)
        self.setWindowIcon(icon_manager.get_icon("edit"))

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_general_tab()
        self.create_links_tab()
        self.create_status_tab()

        self.fiscal_tab = create_fiscalizacao_ata_tab(self)
        self.tabs.addTab(self.fiscal_tab, "Fiscalização")

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
        self.nup_le = QLineEdit()
        self.cnpj_le = QLineEdit()
        self.setor_le = QLineEdit()
        self.modalidade_le = QLineEdit()
        self.empresa_le = QLineEdit()
        self.objeto_le = QLineEdit()
        self.termo_aditivo_le = QLineEdit()
        self.portaria_le = QLineEdit()
        self.valor_global_le = QLineEdit()

        # Campos de data
        self.celebracao_de = QDateEdit(calendarPopup=True)
        self.celebracao_de.setDisplayFormat("dd/MM/yyyy")
        self.termino_de = QDateEdit(calendarPopup=True)
        self.termino_de.setDisplayFormat("dd/MM/yyyy")

        # ===== Linhas em grade (duas colunas) =====

        # Linha 1: Número | Ano
        h_num_ano = QHBoxLayout()
        h_num_ano.addWidget(self.numero_le)
        h_num_ano.addWidget(self.ano_le)
        layout.addRow(QLabel("<b>Número / Ano:</b>"), h_num_ano)

        # Linha 2: CNPJ | NUP
        h_cnpj_nup = QHBoxLayout()
        h_cnpj_nup.addWidget(self.cnpj_le)
        h_cnpj_nup.addWidget(self.nup_le)
        layout.addRow(QLabel("<b>CNPJ / NUP:</b>"), h_cnpj_nup)

        # Linha 3: Setor | Modalidade
        h_setor_modalidade = QHBoxLayout()
        h_setor_modalidade.addWidget(self.setor_le)
        h_setor_modalidade.addWidget(self.modalidade_le)
        layout.addRow(QLabel("<b>Setor / Modalidade:</b>"), h_setor_modalidade)

        # Linha 4: Empresa (sozinha, mas pode ser larga)
        layout.addRow(QLabel("<b>Empresa:</b>"), self.empresa_le)

        # Linha 5: Objeto (sozinha)
        layout.addRow(QLabel("<b>Objeto:</b>"), self.objeto_le)

        # Linha 6: Termo Aditivo | Portaria de Fiscalização
        h_termo_portaria = QHBoxLayout()
        h_termo_portaria.addWidget(self.termo_aditivo_le)
        h_termo_portaria.addWidget(self.portaria_le)
        layout.addRow(QLabel("<b>Termo Aditivo / Portaria:</b>"), h_termo_portaria)

        # Linha 7: Valor Global (sozinho ou com outro campo, se desejar)
        layout.addRow(QLabel("<b>Valor Global:</b>"), self.valor_global_le)

        # Linha 8: Datas (Celebração | Término)
        h_datas = QHBoxLayout()
        h_datas.addWidget(self.celebracao_de)
        h_datas.addWidget(self.termino_de)
        layout.addRow(QLabel("<b>Data de Celebração / Término:</b>"), h_datas)

        self.tabs.addTab(general_tab, "Informações Gerais")

    def create_status_tab(self):
        """Cria a aba 'Status' que contém o dropdown e os registros com estilo aprimorado."""
        status_tab = QWidget()
        main_layout = QVBoxLayout(status_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ============= 1. Dropdown de Status =============
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; color: #E5E5E5; font-size: 13px;")
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems([
            "SEÇÃO ATAS", "EMPRESA", "SIGDEM", "SIGAD","ASSINADO", "PUBLICADO", "PORTARIA",
            "ALERTA PRAZO", "ATA GERADA", "NOTA TÉCNICA", "AGU", "PRORROGADO"
        ])
        self.status_dropdown.setFixedWidth(230)
        self.status_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #1F1F1F;
                border: 1px solid #444;
                border-radius: 4px;
                color: #F1F1F1;
                padding: 4px 8px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #5c8dff;
            }
            QComboBox::drop-down {
                width: 22px;
                border-left: 1px solid #444;
            }
            QComboBox QAbstractItemView {
                background-color: #202020;
                selection-background-color: #5c8dff;
                color: #F1F1F1;
                border: 1px solid #333;
                outline: none;
            }
        """)
        status_layout.addStretch()
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_dropdown)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # ============= 2. Frame com lista de registros =============
        registros_frame = QFrame()
        registros_frame.setFrameShape(QFrame.Shape.StyledPanel)
        registros_frame.setStyleSheet("QFrame { background-color: #141414; border: 1px solid #303030; border-radius: 4px; }")

        registros_layout = QVBoxLayout(registros_frame)
        registros_layout.setContentsMargins(8, 8, 8, 8)

        self.registro_list = QListWidget()
        self.registro_list.setWordWrap(True)
        self.registro_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                color: #F1F1F1;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 5px; /* Reduzido o padding horizontal de 10px para 5px */
                margin: 4px 0;
            }
            QListWidget::indicator {
                width: 16px; /* Reduzido de 18px para 16px */
                height: 16px; /* Reduzido de 18px para 16px */
                border: 1px solid #666;
                background: #222;
                border-radius: 3px;
            }
            QListWidget::indicator:checked {
                background-color: #3a8dfd;
                border-radius: 3px;
                border: 1px solid #3a8dfd;
            }
            QListWidget::item:selected {
                background-color: rgba(90, 140, 255, 0.25);
            }
        """)
        registros_layout.addWidget(self.registro_list)
        main_layout.addWidget(registros_frame)

        # ============= 3. Botões de ações =============
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        add_button = QPushButton("Adicionar Registro")
        add_button.setIcon(icon_manager.get_icon("add_comment"))
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self.add_registro)

        delete_button = QPushButton("Excluir Selecionado")
        delete_button.setIcon(icon_manager.get_icon("delete"))
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.clicked.connect(self.delete_registro)

        copy_button = QPushButton("Copiar Selecionado")
        copy_button.setIcon(icon_manager.get_icon("copy")) # Assumindo que 'copy' é um ícone válido
        copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_button.clicked.connect(self.copy_selected_registros) # Conecta à nova função

        for btn in (add_button, delete_button, copy_button):
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2A2A2A;
                    color: #E5E5E5;
                    border: 1px solid #3A3A3A;
                    border-radius: 4px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background-color: #3a8dfd;
                    border: 1px solid #3a8dfd;
                    color: white;
                }
            """)
            buttons_layout.addWidget(btn)

        main_layout.addLayout(buttons_layout)

        self.tabs.addTab(status_tab, "Status")

    def create_links_tab(self):
        """Cria a aba para inserir os links."""
        links_tab = QWidget()
        layout = QFormLayout(links_tab)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.serie_ata_link_le = QLineEdit()
        self.portaria_link_le = QLineEdit()
        self.ta_link_le = QLineEdit()
        self.portal_licitacoes_link_le = QLineEdit()

        self.serie_ata_link_le, hbox_ata = create_link_input_row(self, "Link Série Ata:", "Cole aqui o link da Série da Ata (opcional)")
        self.portaria_link_le, hbox_portaria_ata = create_link_input_row(self, "Link Portaria:", "Cole aqui o link da Portaria (opcional)")
        self.ta_link_le, hox_ta_ata = create_link_input_row(self, "Link Termo Aditivo:", "Cole aqui o link do Termo Aditivo (opcional)")
        self.portal_licitacoes_link_le, hbox_portal_licitacao = create_link_input_row(self, "Link Portal Licitação:", "Cole aqui o link do Portal de Licitação (opcional)")

        layout.addRow(QLabel("<b>Link Série Ata:</b>"), hbox_ata)
        layout.addRow(QLabel("<b>Link Portaria:</b>"), hbox_portaria_ata)
        layout.addRow(QLabel("<b>Link Termo Aditivo:</b>"), hox_ta_ata)
        layout.addRow(QLabel("<b>Link Portal Licitação:</b>"), hbox_portal_licitacao)

        self.tabs.addTab(links_tab, "Links Atas")

    def load_data(self):
        """Carrega os dados da ata nos campos da interface."""
        self.numero_le.setText(self.ata_data.numero or "")
        self.ano_le.setText(self.ata_data.ano or "")
        self.nup_le.setText(self.ata_data.nup or "")
        self.cnpj_le.setText(getattr(self.ata_data, "cnpj", "") or "")
        self.setor_le.setText(self.ata_data.setor or "")
        self.modalidade_le.setText(self.ata_data.modalidade or "")
        self.empresa_le.setText(self.ata_data.empresa or "")
        self.objeto_le.setText(self.ata_data.objeto or "")
        self.termo_aditivo_le.setText(self.ata_data.termo_aditivo or "")
        self.portaria_le.setText(self.ata_data.portaria_fiscalizacao or "")
        self.valor_global_le.setText(getattr(self.ata_data.valor_global, "valor_global", "") or "")

        # Links
        self.serie_ata_link_le.setText(self.ata_data.serie_ata_link or "")
        self.portaria_link_le.setText(self.ata_data.portaria_link or "")
        self.ta_link_le.setText(self.ata_data.ta_link or "")
        self.portal_licitacoes_link_le.setText(self.ata_data.portal_licitacoes_link or "")

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

        # Fiscalização
        load_fiscalizacao_ata(self.model, self.ata_data.contrato_ata_parecer, self)
        

    def get_updated_data(self):
        """Retorna um dicionário com os dados atualizados da interface."""
        updated_data = {
            'setor': self.setor_le.text(), # NOVO: Pega o valor do setor
            'modalidade': self.modalidade_le.text(),
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'empresa': self.empresa_le.text(),
            'contrato_ata_parecer': self.ata_data.contrato_ata_parecer, # Mantém o ID original
            'objeto': self.objeto_le.text(),
            'celebracao': self.celebracao_de.date().toString("yyyy-MM-dd"),
            'termino': self.termino_de.date().toString("yyyy-MM-dd"),
            #'observacoes': self.observacoes_te.text(),
            'termo_aditivo': self.termo_aditivo_le.text(),
            'portaria_fiscalizacao': self.portaria_le.text(),
            'nup': self.nup_le.text(),
            'cnpj': self.cnpj_le.text(),             # NOVO
            'valor_global': self.valor_global_le.text(),  # NOVO
            'portal_licitacoes_link': self.portal_licitacoes_link_le.text(),
            'status': self.status_dropdown.currentText() if hasattr(self, 'status_dropdown') else '',
            'serie_ata_link': self.serie_ata_link_le.text(),
            'portaria_link': self.portaria_link_le.text(),
            'ta_link': self.ta_link_le.text()
        }

        # Coleta dados dos registros
        if hasattr(self, 'registro_list'):
            updated_data['registros'] = [self.registro_list.item(i).text() for i in range(self.registro_list.count())]
        else:
            updated_data['registros'] = []

        # Coleta dados da fiscalização (se a aba existir)
        if hasattr(self, 'fiscal_gestor'):
            updated_data['fiscalizacao'] = {
                'gestor': self.fiscal_gestor.text(),
                'gestor_substituto': self.fiscal_gestor_substituto.text(),
                'fiscal_tecnico': self.fiscalizacao_tecnico.text(),
                'fiscal_tec_substituto': self.fiscalizacao_tec_substituto.text(),
                'fiscal_administrativo': self.fiscalizacao_administrativo.text(),
                'fiscal_admin_substituto': self.fiscalizacao_admin_substituto.text(),
                'observacoes': self.fiscal_observacoes.toPlainText(),
            }
        else:
            updated_data['fiscalizacao'] = {}

        return updated_data

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

    def copy_selected_registros(self):
        """
        Copia o texto dos registros que estão com a caixa de seleção marcada
        para a área de transferência.
        """
        checked_texts = []
        for i in range(self.registro_list.count()):
            item = self.registro_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_texts.append(item.text())

        if not checked_texts:
            QMessageBox.information(self, "Copiar Registros", "Nenhum registro marcado para copiar.")
            return

        # Coleta o texto de todos os itens marcados
        text_to_copy = "\n".join(checked_texts)

        # Copia para a área de transferência
        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)

        QMessageBox.information(self, "Copiar Registros", f"{len(checked_texts)} registro(s) copiado(s) para a área de transferência.")

    def copy_to_clipboard(self, line_edit: QLineEdit):
        """Copia o texto de um QLineEdit para a área de transferência."""
        from PyQt6.QtWidgets import QApplication, QMessageBox

        text = line_edit.text().strip()
        if not text:
            QMessageBox.information(self, "Copiar link", "Não há link para copiar.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copiar link", "Link copiado para a área de transferência.")

    def save_changes(self):
        """Emite um sinal para o controller salvar todos os dados."""
        # O controller vai pegar os dados, salvar TUDO (Geral e Fiscalização),
        # e depois mostrar a mensagem de sucesso ou erro.
        self.ata_updated.emit()
