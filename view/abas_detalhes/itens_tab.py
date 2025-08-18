# view/abas_detalhes/itens_tab.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                             QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

def create_itens_tab(self):
    """
    Cria a aba 'Itens' que busca e exibe os itens de um contrato.
    Funciona nos modos Online e Offline.
    """
    itens_tab = QWidget()
    main_layout = QVBoxLayout(itens_tab)
    
    # --- Layout Superior com o botão de busca ---
    top_layout = QHBoxLayout()
    search_button = QPushButton("Buscar Itens do Contrato")
    search_button.setIcon(icon_manager.get_icon("search"))
    search_button.setFixedHeight(40)
    top_layout.addWidget(search_button)

    self.itens_report_button = QPushButton("Gerar Relatório de Itens (XLSX)")
    self.itens_report_button.setIcon(icon_manager.get_icon("excel_up")) # Reutilizando ícone
    self.itens_report_button.setFixedHeight(40)
    self.itens_report_button.setVisible(False) # Começa invisível
    self.itens_report_button.clicked.connect(self.generate_itens_report_to_excel) # Conecta a novo método
    top_layout.addWidget(self.itens_report_button)

    top_layout.addStretch()
    main_layout.addLayout(top_layout)
    
    # --- Container de resultados com scroll ---
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVisible(False) # Começa invisível
    main_layout.addWidget(scroll_area)
    
    results_container = QWidget()
    results_layout = QVBoxLayout(results_container)
    scroll_area.setWidget(results_container)

    def display_itens(itens_to_display):
        """Função interna para renderizar os cards dos itens."""
        # Limpa resultados anteriores
        while results_layout.count():
            child = results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not itens_to_display:
            results_layout.addWidget(QLabel("<b>Nenhum item encontrado para este contrato.</b>"))
            return

        for index, item in enumerate(itens_to_display, 1):
            item_frame = QFrame()
            item_frame.setStyleSheet("border: 1px solid #444; border-radius: 5px; padding: 10px; margin-bottom: 10px;")
            card_layout = QVBoxLayout(item_frame)
            card_layout.setSpacing(8)
            
            # Linha 1: Título e Valor Total
            line1_layout = QHBoxLayout()
            line1_layout.addWidget(QLabel(f"<b>Item {index}:</b> {item.get('tipo_id', 'N/A')}"))
            line1_layout.addStretch()
            valor_total = item.get('valortotal', '0,00')
            quant = item.get('quantidade', '0,00')
            valorunitario = item.get('valorunitario', '0,00')
            line1_layout.addWidget(QLabel(f"<b>Quantidade:</b> {quant}"))
            line1_layout.addWidget(QLabel(f"<b>Valor Unitário:</b> R$ {valorunitario}"))
            line1_layout.addWidget(QLabel(f"<b>Valor Total:</b> R$ {valor_total}"))

            card_layout.addLayout(line1_layout)

            # Linha 2: Grupo e CATMAT/SER
            line2_layout = QHBoxLayout()
            line2_layout.addWidget(QLabel(f"<b>Grupo:</b> {item.get('grupo_id', 'N/A')}"))
            line2_layout.addStretch()
            line2_layout.addWidget(QLabel(f"<b>CATMAT/SER:</b> {item.get('catmatseritem_id', 'N/A')}"))
            card_layout.addLayout(line2_layout)

            # Linha 3: Descrição Complementar
            card_layout.addWidget(QLabel(f"<b>Descrição:</b> {item.get('descricao_complementar', 'N/A')}"))
            
            results_layout.addWidget(item_frame)
        
        results_layout.addStretch()

    def fetch_and_display_itens():
        """Função principal que busca os dados e os exibe."""
        loading_label = QLabel("<b>Buscando dados dos itens...</b>")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        display_itens([]) # Limpa a tela
        results_layout.addWidget(loading_label)
        scroll_area.setVisible(True)
        
        search_button.setEnabled(False)
        search_button.setText("Buscando...")

        contrato_id = self.data.get("id")

        # A chamada de busca é feita através do model, que lida com o modo online/offline
        itens, error_message = self.model.get_sub_data_for_contract(contrato_id, "itens")
        
        loading_label.deleteLater()
        
        if error_message or not itens:
            self.itens_report_button.setVisible(False)
            msg = f"<b>Não foi possível carregar:</b><br>{error_message}" if error_message else "<b>Nenhum item encontrado.</b>"
            results_layout.addWidget(QLabel(msg))
        else:
            self.itens_report_button.setVisible(True)
            display_itens(itens)
        
        search_button.setEnabled(True)
        search_button.setText("Buscar Itens Novamente")

    search_button.clicked.connect(fetch_and_display_itens)

    return itens_tab
