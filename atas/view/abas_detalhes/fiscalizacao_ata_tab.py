# atas/view/abas_detalhes/fiscalizacao_ata_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QHBoxLayout, QTextEdit, QPushButton, QGroupBox
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager

def create_fiscalizacao_ata_tab(parent):
    """Cria a aba de Fiscalização para Atas."""
    tab = QWidget()
    main = QVBoxLayout(tab)
    main.setContentsMargins(10, 10, 10, 10)
    main.setSpacing(15)

    title = QLabel(f"Fiscalização da Ata - {parent.ata_data.contrato_ata_parecer}")
    title.setStyleSheet("font-size: 16px; font-weight: bold;")
    main.addWidget(title)

    group = QGroupBox("DADOS DE FISCALIZAÇÃO")
    form = QFormLayout(group)
    form.setVerticalSpacing(12)

    def add_field(label, attr, multiline=False):
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: bold; min-width: 180px;")
        box = QHBoxLayout()
        widget = QTextEdit() if multiline else QLineEdit()
        widget.setPlaceholderText(f"Digite {label[:-1].lower()}...")
        widget.setMinimumWidth(400)
        setattr(parent, attr, widget)
        copy_btn = QPushButton()
        copy_btn.setIcon(icon_manager.get_icon("copy"))
        copy_btn.setIconSize(QSize(16, 16))
        copy_btn.setFixedSize(24, 24)
        if multiline:
            copy_btn.clicked.connect(lambda _, w=widget: parent.copy_text_edit_to_clipboard(w))
        else:
            copy_btn.clicked.connect(lambda _, w=widget: parent.copy_to_clipboard(w))
        box.addWidget(widget)
        box.addWidget(copy_btn)
        form.addRow(lbl, box)

    add_field("Gestor:", "fiscal_gestor")
    add_field("Gestor Substituto:", "fiscal_gestor_substituto")
    add_field("Fiscal Técnico:", "fiscalizacao_tecnico")
    add_field("Fiscal Técnico Substituto:", "fiscalizacao_tec_substituto")
    add_field("Fiscal Administrativo:", "fiscalizacao_administrativo")
    add_field("Fiscal Administrativo Substituto:", "fiscalizacao_admin_substituto")
    add_field("Observações:", "fiscal_observacoes", multiline=True)

    main.addWidget(group)
    return tab
