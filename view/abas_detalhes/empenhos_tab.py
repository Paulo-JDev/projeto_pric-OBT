from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                             QHBoxLayout, QPushButton, QComboBox)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager
from datetime import datetime

def create_empenhos_tab(self):
    """
    Cria a aba 'Empenhos' que busca dados através do Model (Online/Offline).
    """
    empenhos_tab = QWidget()
    main_layout = QVBoxLayout(empenhos_tab)
    
    # --- Layout Superior (sem alterações) ---
    top_layout = QHBoxLayout()
    search_button = QPushButton("Buscar Empenhos")
    search_button.setIcon(icon_manager.get_icon("search"))
    search_button.setFixedHeight(40)
    top_layout.addWidget(search_button)

    self.report_button = QPushButton("Gerar Relatório de Empenhos (XLSX)")
    self.report_button.setIcon(icon_manager.get_icon("relatoria"))
    self.report_button.setFixedHeight(40)
    self.report_button.setVisible(False)
    self.report_button.clicked.connect(self.generate_empenho_report_to_excel)
    top_layout.addWidget(self.report_button)

    self.email_button = QPushButton("Disparar XLSX por E-mail")
    self.email_button.setIcon(icon_manager.get_icon("icon_send"))
    self.email_button.setFixedHeight(40)
    # Conecta a um novo método que será criado na DetailsDialog
    self.email_button.clicked.connect(self.open_email_dialog) 
    top_layout.addWidget(self.email_button)

    top_layout.addStretch()
    year_filter_label = QLabel("Filtrar por Ano:")
    top_layout.addWidget(year_filter_label)
    year_combo_box = QComboBox()
    year_combo_box.setFixedWidth(120)
    year_combo_box.setVisible(False)
    top_layout.addWidget(year_combo_box)
    main_layout.addLayout(top_layout)
    
    # --- Container de resultados (sem alterações) ---
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVisible(False)
    main_layout.addWidget(scroll_area)
    results_container = QWidget()
    results_layout = QVBoxLayout(results_container)
    scroll_area.setWidget(results_container)

    all_empenhos = []

    def display_empenhos(empenhos_to_display):
        """Função que exibe os empenhos (sem alterações na lógica visual)."""
        while results_layout.count():
            child = results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not empenhos_to_display:
            results_layout.addWidget(QLabel("<b>Nenhum empenho encontrado para o ano selecionado.</b>"))
            return

        for index, empenho in enumerate(empenhos_to_display, 1):
            empenho_frame = QFrame()
            empenho_frame.setStyleSheet("border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;")
            card_layout = QVBoxLayout(empenho_frame)
            card_layout.setSpacing(8)
            
            line1_layout = QHBoxLayout()
            line1_layout.addWidget(QLabel(f"<b>{index}.</b>"))
            line1_layout.addWidget(QLabel(f"<b>Nº do empenho:</b> {empenho.get('numero', 'N/A')}"))
            line1_layout.addWidget(QLabel(f"<b>Data da emissão:</b> {empenho.get('data_emissao', 'N/A')}"))
            line1_layout.addStretch()
            card_layout.addLayout(line1_layout)
            card_layout.addWidget(QLabel(f"<b>Plano interno:</b> {empenho.get('planointerno', 'N/A')}"))
            card_layout.addWidget(QLabel(f"<b>Natureza Despesa:</b> {empenho.get('naturezadespesa', 'N/A')}"))
            valores_layout = QHBoxLayout()
            valores_layout.addWidget(QLabel(f"<b>Empenhado:</b> R$ {empenho.get('empenhado', '0,00')}"))
            valores_layout.addWidget(QLabel(f"<b>Liquidado:</b> R$ {empenho.get('liquidado', '0,00')}"))
            valores_layout.addWidget(QLabel(f"<b>Pago:</b> R$ {empenho.get('pago', '0,00')}"))
            valores_layout.addStretch()
            card_layout.addLayout(valores_layout)
            results_layout.addWidget(empenho_frame)
        
        results_layout.addStretch()

    def on_year_filter_changed(selected_year):
        """Filtra os empenhos (sem alterações)."""
        if selected_year == "Todos":
            display_empenhos(all_empenhos)
        else:
            filtered_empenhos = [e for e in all_empenhos if e.get("data_emissao", "").startswith(selected_year)]
            display_empenhos(filtered_empenhos)

    def fetch_and_display_empenhos():
        """Função principal que busca os dados e ativa o filtro."""
        nonlocal all_empenhos
        loading_label = QLabel("<b>Buscando dados...</b>")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        display_empenhos([])
        results_layout.addWidget(loading_label)
        scroll_area.setVisible(True)
        
        search_button.setEnabled(False)
        search_button.setText("Buscando...")

        contrato_id = self.data.get("id")

        empenhos, error_message = self.model.get_sub_data_for_contract(contrato_id, "empenhos")
        
        loading_label.deleteLater()
        
        if error_message or not empenhos:
            msg = f"<b>Não foi possível carregar:</b><br>{error_message}" if error_message else "<b>Nenhum empenho encontrado.</b>"
            results_layout.addWidget(QLabel(msg))
            all_empenhos = []
            year_combo_box.setVisible(False)
        else:
            all_empenhos = empenhos
            self.report_button.setVisible(True)
            year_combo_box.blockSignals(True)
            year_combo_box.clear()
            years = sorted(list(set(e.get("data_emissao", "")[:4] for e in all_empenhos if e.get("data_emissao"))), reverse=True)
            if years:
                year_combo_box.addItem("Todos")
                year_combo_box.addItems(years)
                year_combo_box.setVisible(True)
            year_combo_box.blockSignals(False)
            display_empenhos(all_empenhos)
        
        search_button.setEnabled(True)
        search_button.setText("Buscar Empenhos Novamente")

    search_button.clicked.connect(fetch_and_display_empenhos)
    year_combo_box.currentTextChanged.connect(on_year_filter_changed)

    return empenhos_tab