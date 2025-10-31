# Contratos/view/abas_detalhes/fiscal_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit
)
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager


def create_fiscal_tab(parent):
    """
    Cria a aba de Fiscalização com 6 campos de texto editáveis.
    
    Args:
        parent: Instância do DetailsDialog que contém os dados do contrato
        
    Returns:
        QWidget: Widget da aba de fiscalização
    """
    fiscal_tab = QWidget()
    main_layout = QVBoxLayout(fiscal_tab)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    # Verificação inicial dos dados
    if not parent.data:
        main_layout.addWidget(QLabel("Erro: Nenhum dado foi carregado para o contrato."))
        return fiscal_tab

    # ==================== TÍTULO ====================
    title_layout = QHBoxLayout()
    
    # Ícone de fiscalização
    fiscal_icon = QLabel()
    fiscal_icon.setPixmap(icon_manager.get_icon("law_menu").pixmap(32, 32))
    fiscal_icon.setFixedSize(32, 32)
    title_layout.addWidget(fiscal_icon)
    
    # Texto do título: Número do Contrato + Nome da Empresa
    numero_contrato = parent.data.get('numero', 'N/A')
    empresa_nome = parent.data.get('fornecedor', {}).get('nome', 'Empresa não informada')
    
    title_label = QLabel(f"Fiscalização - Contrato {numero_contrato} | {empresa_nome}")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    title_layout.addWidget(title_label)
    title_layout.addStretch(1)
    
    main_layout.addLayout(title_layout)

    # ==================== FORMULÁRIO DE FISCALIZAÇÃO ====================
    fiscal_group = QGroupBox("DADOS DE FISCALIZAÇÃO")
    fiscal_layout = QFormLayout(fiscal_group)
    fiscal_layout.setVerticalSpacing(15)
    fiscal_layout.setHorizontalSpacing(20)

    # Função helper para criar campos de texto com botão de copiar
    def create_text_field(label_text, field_name, multiline=False):
        """
        Cria um campo de texto com label e botão de copiar.
        
        Args:
            label_text: Texto da label
            field_name: Nome do atributo no parent (ex: 'fiscal_gestor')
            multiline: Se True, usa QTextEdit; se False, usa QLineEdit
        """
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; min-width: 180px;")
        
        hbox = QHBoxLayout()
        
        # Cria o campo de texto (QLineEdit ou QTextEdit)
        if multiline:
            text_widget = QTextEdit()
            text_widget.setMaximumHeight(80)  # Limita altura para não ocupar muito espaço
            text_widget.setPlaceholderText(f"Digite {label_text.lower()}")
        else:
            text_widget = QLineEdit()
            text_widget.setPlaceholderText(f"Digite {label_text.lower()}")
        
        text_widget.setMinimumWidth(400)
        text_widget.setMaximumWidth(600)
        
        # Armazena referência no parent para acesso posterior
        setattr(parent, field_name, text_widget)
        
        hbox.addWidget(text_widget, stretch=1)
        
        # Botão de copiar
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        copy_btn.setToolTip("Copiar")
        
        # Conecta ao método de copiar (diferente para QLineEdit e QTextEdit)
        if multiline:
            copy_btn.clicked.connect(lambda: parent.copy_text_edit_to_clipboard(text_widget))
        else:
            copy_btn.clicked.connect(lambda: parent.copy_to_clipboard(text_widget))
        
        hbox.addWidget(copy_btn, stretch=0)
        hbox.addStretch(1)
        
        fiscal_layout.addRow(label, hbox)
        
        return text_widget

    # ==================== 6 CAMPOS DE FISCALIZAÇÃO ====================
    
    # Campo 1: Gestor do Contrato
    create_text_field("Gestor:", "fiscal_gestor", multiline=False)
    
    # Campo 2: Gestor Substituto
    create_text_field("Gestor Substituto:", "fiscal_gestor_substituto", multiline=False)

    # Campo 3: Fiscal tecnico
    create_text_field("Fiscal Tecnico:", "fiscalizacao_tecnico", multiline=False)
    
    # Campo 4: Fiscal Substituto
    create_text_field("Fiscal Tecnico Substituto:", "fiscalizacao_tec_substituto", multiline=False)
    
    # Campo 5: Setor Responsável
    create_text_field("Fiscal Administrativo:", "fiscalizacao_administrativo", multiline=False)
    
    # 6. Fiscal Administrativo Subs (antes: "Data da Fiscalização")
    create_text_field("Fiscal Administrativo Subs:", "fiscalizacao_admin_substituto", multiline=False)
    
    # 7. Observações (mantido)
    create_text_field("Observações:", "fiscal_observacoes", multiline=True)

    main_layout.addWidget(fiscal_group)
    main_layout.addStretch()

    return fiscal_tab
