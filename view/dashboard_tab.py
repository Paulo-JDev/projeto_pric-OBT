# view/dashboard_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, 
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

def create_dashboard_tab(main_window):
    """
    Cria a aba de Dashboard, que exibirá métricas e gráficos sobre os contratos.
    """
    dashboard_tab = QWidget()
    main_layout = QVBoxLayout(dashboard_tab)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(20)

    # --- Layout do Título e Botão de Atualizar ---
    header_layout = QHBoxLayout()
    title = QLabel("Dashboard de Contratos")
    title.setStyleSheet("font-size: 20px; font-weight: bold; color: #8AB4F7;")
    header_layout.addWidget(title)
    header_layout.addStretch()
    
    main_window.refresh_dashboard_button = QPushButton("Atualizar Dados")
    main_window.refresh_dashboard_button.setIcon(icon_manager.get_icon("refresh"))
    main_window.refresh_dashboard_button.setObjectName("header_button")
    header_layout.addWidget(main_window.refresh_dashboard_button)
    
    main_layout.addLayout(header_layout)

    # --- Grid para os KPIs (Key Performance Indicators) ---
    kpi_grid_layout = QGridLayout()
    kpi_grid_layout.setSpacing(20)
    main_layout.addLayout(kpi_grid_layout)

    # Dicionário aninhado para armazenar os widgets que serão atualizados
    main_window.dashboard_widgets = {
        'card': {},
        'value_label': {}
    }

    def create_kpi_card(title, icon_name):
        """Função auxiliar para criar um card de KPI padronizado."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setObjectName("kpi_card")
        card.setStyleSheet("QFrame#kpi_card { border: 1px solid #444; border-radius: 8px; }")
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #aaa;")
        
        value_label = QLabel("N/A")
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #8AB4F7;")
        
        icon_label = QLabel()
        icon_label.setPixmap(icon_manager.get_icon(icon_name).pixmap(32, 32))
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        top_layout.addWidget(icon_label)
        
        card_layout.addLayout(top_layout)
        card_layout.addWidget(value_label)
        
        # Retorna tanto o card (QFrame) quanto o label do valor (QLabel)
        return card, value_label

    # Criando e posicionando os cards de KPI
    kpi_titles = {
        "total_contratos": ("Total de Contratos", "contract"),
        "valor_total": ("Valor Global Total", "economy"),
        "ativos": ("Contratos Ativos", "aproved"),
        "expirando": ("Expirando em 90 dias", "alarm")
    }
    
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for (key, (title, icon)), pos in zip(kpi_titles.items(), positions):
        card, value_label = create_kpi_card(title, icon)
        kpi_grid_layout.addWidget(card, pos[0], pos[1])
        # Armazena ambos os widgets no dicionário para acesso posterior
        main_window.dashboard_widgets['card'][key] = card
        main_window.dashboard_widgets['value_label'][key] = value_label

    # --- Placeholder para Gráficos (sem alterações) ---
    charts_layout = QHBoxLayout()
    
    chart1_frame = QFrame()
    chart1_layout = QVBoxLayout(chart1_frame)
    chart1_label = QLabel("Gráfico de Status (Implementação Futura)")
    chart1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    chart1_frame.setStyleSheet("border: 1px dashed #555; border-radius: 8px;")
    chart1_layout.addWidget(chart1_label)
    
    chart2_frame = QFrame()
    chart2_layout = QVBoxLayout(chart2_frame)
    chart2_label = QLabel("Gráfico de Valores por Ano (Implementação Futura)")
    chart2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    chart2_frame.setStyleSheet("border: 1px dashed #555; border-radius: 8px;")
    chart2_layout.addWidget(chart2_label)
    
    charts_layout.addWidget(chart1_frame)
    charts_layout.addWidget(chart2_frame)
    main_layout.addLayout(charts_layout)
    
    main_layout.addStretch()
    
    return dashboard_tab