import requests
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                             QGridLayout, QPushButton)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

def get_empenhos_data(contrato_id):
    """Busca e retorna os dados de empenhos de um contrato específico."""
    if not contrato_id:
        return None, "ID do contrato não fornecido."

    api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/empenhos"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Erro na API: Status {response.status_code}"
    except requests.RequestException as e:
        return None, f"Erro de rede: {e}"
    except json.JSONDecodeError:
        return None, "Erro: A resposta da API não é um JSON válido."

def create_empenhos_tab(self):
    """
    Cria a aba 'Empenhos' com um botão para carregar os dados sob demanda.
    """
    empenhos_tab = QWidget()
    main_layout = QVBoxLayout(empenhos_tab)
    
    search_button = QPushButton("Buscar Empenhos")
    search_button.setIcon(icon_manager.get_icon("search"))
    search_button.setFixedHeight(40)
    main_layout.addWidget(search_button)
    
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setVisible(False)
    main_layout.addWidget(scroll_area)

    results_container = QWidget()
    results_layout = QVBoxLayout(results_container)
    scroll_area.setWidget(results_container)

    def fetch_and_display_empenhos():
        """
        Função que será chamada pelo clique do botão.
        Ela faz a requisição e constrói a interface dos resultados.
        """
        while results_layout.count():
            child = results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        loading_label = QLabel("<b>Buscando dados dos empenhos, por favor aguarde...</b>")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.addWidget(loading_label)
        scroll_area.setVisible(True)
        
        search_button.setEnabled(False)
        search_button.setText("Buscando...")

        contrato_id = self.data.get("id")
        empenhos, error_message = get_empenhos_data(contrato_id)
        
        loading_label.deleteLater()
        
        if error_message:
            results_layout.addWidget(QLabel(f"<b>Não foi possível carregar os empenhos:</b><br>{error_message}"))
        elif not empenhos:
            results_layout.addWidget(QLabel("<b>Nenhum empenho encontrado para este contrato.</b>"))
        else:
            for empenho in empenhos:
                empenho_frame = QFrame()
                empenho_frame.setFrameShape(QFrame.Shape.StyledPanel)
                grid_layout = QGridLayout(empenho_frame)

                def add_field(row, col, label, value):
                    label_widget = QLabel(f"<b>{label}:</b> {value}")
                    label_widget.setWordWrap(True)
                    grid_layout.addWidget(label_widget, row, col)

                # --- CAMPOS AJUSTADOS PARA O SEU JSON ---
                add_field(0, 0, "Nº do empenho", empenho.get("numero", "N/A"))
                add_field(0, 1, "Data da emissão", empenho.get("data_emissao", "N/A"))
                add_field(0, 2, "Fonte de recurso", empenho.get("fonte_recurso", "N/A"))
                add_field(0, 3, "Programa de Trabalho", empenho.get("programa_trabalho", "N/A"))
                
                add_field(1, 0, "Plano interno", empenho.get("planointerno", "N/A"))
                add_field(1, 1, "Natureza Despesa", empenho.get("naturezadespesa", "N/A"))
                
                add_field(2, 0, "Empenhado", f"R$ {empenho.get('empenhado', '0,00')}")
                add_field(2, 1, "Liquidado", f"R$ {empenho.get('liquidado', '0,00')}")
                add_field(2, 2, "Pago", f"R$ {empenho.get('pago', '0,00')}")

                results_layout.addWidget(empenho_frame)
        
        search_button.setEnabled(True)
        search_button.setText("Buscar Empenhos Novamente")

    search_button.clicked.connect(fetch_and_display_empenhos)

    return empenhos_tab