import requests
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                             QHBoxLayout, QPushButton, QComboBox)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager
from datetime import datetime

def get_empenhos_data(contrato_id):
    """Busca, retorna e ordena os dados de empenhos."""
    if not contrato_id:
        return None, "ID do contrato não fornecido."
    api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/empenhos"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                data.sort(key=lambda x: datetime.strptime(x.get('data_emissao', '1900-01-01'), '%Y-%m-%d'), reverse=True)
            return data, None
        else:
            return None, f"Erro na API: Status {response.status_code}"
    except (requests.RequestException, json.JSONDecodeError) as e:
        return None, f"Erro ao processar dados: {e}"

def create_empenhos_tab(self):
    """
    Cria a aba 'Empenhos' com um card para cada empenho, separados por uma única linha.
    """
    empenhos_tab = QWidget()
    main_layout = QVBoxLayout(empenhos_tab)
    
    # --- Layout Superior com Botão de Busca e Filtro (sem alterações) ---
    top_layout = QHBoxLayout()
    search_button = QPushButton("Buscar Empenhos")
    search_button.setIcon(icon_manager.get_icon("search"))
    search_button.setFixedHeight(40)
    top_layout.addWidget(search_button)
    top_layout.addStretch()
    year_filter_label = QLabel("Filtrar por Ano:")
    top_layout.addWidget(year_filter_label)
    year_combo_box = QComboBox()
    year_combo_box.setFixedWidth(120)
    year_combo_box.setVisible(False)
    top_layout.addWidget(year_combo_box)
    main_layout.addLayout(top_layout)
    
    # --- Container para os resultados (sem alterações) ---
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVisible(False)
    main_layout.addWidget(scroll_area)
    results_container = QWidget()
    results_layout = QVBoxLayout(results_container)
    scroll_area.setWidget(results_container)

    all_empenhos = []

    def display_empenhos(empenhos_to_display):
        """Função que exibe os empenhos, cada um em sua própria caixa (QFrame)."""
        while results_layout.count():
            child = results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not empenhos_to_display:
            results_layout.addWidget(QLabel("<b>Nenhum empenho encontrado para o ano selecionado.</b>"))
            return

        # --- NOVA LÓGICA DE LAYOUT ---
        for index, empenho in enumerate(empenhos_to_display, 1):
            # 1. Cria a "caixa" (QFrame) para cada empenho.
            empenho_frame = QFrame()
            # O estilo define a borda da caixa, o espaçamento interno e a margem inferior que a separa da próxima.
            empenho_frame.setStyleSheet("border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;")
            
            # Layout principal do card (Vertical)
            card_layout = QVBoxLayout(empenho_frame)
            card_layout.setSpacing(8) # Espaço entre as linhas de texto
            
            # Linha 1: Numerador, Nº do empenho e Data
            line1_layout = QHBoxLayout()
            line1_layout.addWidget(QLabel(f"<b>{index}.</b>"))
            line1_layout.addWidget(QLabel(f"<b>Nº do empenho:</b> {empenho.get('numero', 'N/A')}"))
            line1_layout.addWidget(QLabel(f"<b>Data da emissão:</b> {empenho.get('data_emissao', 'N/A')}"))
            line1_layout.addStretch()
            card_layout.addLayout(line1_layout)

            # Linha 2: Plano Interno
            card_layout.addWidget(QLabel(f"<b>Plano interno:</b> {empenho.get('planointerno', 'N/A')}"))

            # Linha 3: Natureza da Despesa
            card_layout.addWidget(QLabel(f"<b>Natureza Despesa:</b> {empenho.get('naturezadespesa', 'N/A')}"))

            # Linha 4: Valores
            valores_layout = QHBoxLayout()
            valores_layout.addWidget(QLabel(f"<b>Empenhado:</b> R$ {empenho.get('empenhado', '0,00')}"))
            valores_layout.addWidget(QLabel(f"<b>Liquidado:</b> R$ {empenho.get('liquidado', '0,00')}"))
            valores_layout.addWidget(QLabel(f"<b>Pago:</b> R$ {empenho.get('pago', '0,00')}"))
            valores_layout.addStretch()
            card_layout.addLayout(valores_layout)

            results_layout.addWidget(empenho_frame)
        
        results_layout.addStretch() # Mantém os cards no topo

    def on_year_filter_changed(selected_year):
        """Filtra os empenhos exibidos quando um ano é selecionado."""
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
        empenhos, error_message = get_empenhos_data(contrato_id)
        
        loading_label.deleteLater()
        
        if error_message or not empenhos:
            msg = f"<b>Não foi possível carregar:</b><br>{error_message}" if error_message else "<b>Nenhum empenho encontrado.</b>"
            results_layout.addWidget(QLabel(msg))
            all_empenhos = []
            year_combo_box.setVisible(False)
        else:
            all_empenhos = empenhos
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