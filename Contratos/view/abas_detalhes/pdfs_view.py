# Contratos/view/abas_detalhes/pdfs_view.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, 
                             QHBoxLayout, QLineEdit, QFormLayout, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from urllib.parse import quote
import webbrowser
from utils.icon_loader import icon_manager

def create_link_section(title, url, link_text):
    """Cria uma seção de link com título e URL clicável."""
    if not url: return None
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QVBoxLayout(frame)
    display_html = f'<b>{title}</b><br><a href="{url}" style="color: #8AB4F8;">{link_text}</a>'
    link_label = QLabel(display_html)
    link_label.setOpenExternalLinks(True)
    link_label.setWordWrap(True)
    link_label.setTextFormat(Qt.TextFormat.RichText)
    layout.addWidget(link_label)
    return frame

def create_link_input_row(parent_dialog, label_text, placeholder_text):
    """Cria um QHBoxLayout contendo um QLineEdit e botões de Copiar/Abrir."""
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder_text)
    
    copy_button = QPushButton()
    copy_button.setIcon(icon_manager.get_icon("copy"))
    copy_button.setFixedSize(QSize(24, 24)) # Tamanho pequeno
    copy_button.setToolTip("Copiar Link")
    # Conecta ao método copy_to_clipboard da DetailsDialog
    copy_button.clicked.connect(lambda: parent_dialog.copy_to_clipboard(line_edit))

    open_button = QPushButton()
    open_button.setIcon(icon_manager.get_icon("external-link")) # Ícone de link externo
    open_button.setFixedSize(QSize(24, 24)) # Tamanho pequeno
    open_button.setToolTip("Abrir Link no Navegador")
    # Conecta a uma nova função lambda que abre o link
    open_button.clicked.connect(lambda: open_link_in_browser(line_edit.text()))
    
    hbox = QHBoxLayout()
    hbox.addWidget(line_edit)
    hbox.addWidget(copy_button)
    hbox.addWidget(open_button)
    
    return line_edit, hbox # Retorna o QLineEdit e o QHBoxLayout

# --- NOVA FUNÇÃO PARA ABRIR O LINK ---
def open_link_in_browser(url):
    """Abre a URL fornecida no navegador padrão."""
    if url and (url.startswith('http://') or url.startswith('https://')):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Erro ao abrir link '{url}': {e}")
            # Opcional: Mostrar uma QMessageBox de erro
            QMessageBox.warning(None, "Erro ao Abrir Link", f"Não foi possível abrir o link:\n{url}\n\nErro: {e}")
    elif url:
        print(f"Link inválido ou não suportado: {url}")
        # Opcional: Mostrar uma QMessageBox de aviso
        QMessageBox.warning(None, "Link Inválido", f"O link inserido não é válido ou não começa com http/https:\n{url}")

def create_object_tab(self):
    """
    Cria a aba de links com campos editáveis e um botão para carregar os links de arquivos.
    """
    object_tab = QWidget()
    main_layout = QVBoxLayout(object_tab)
    main_layout.setSpacing(15)

    # --- Links que NÃO precisam de requisição extra são exibidos imediatamente ---
    contrato_id = self.data.get("id")
    comprasnet_url = f"https://contratos.comprasnet.gov.br/transparencia/contratos/{contrato_id}"
    comprasnet_section = create_link_section(
        "Link para a página do Contrato (Comprasnet):", 
        comprasnet_url,
        "Acessar página do Comprasnet"
    )
    if comprasnet_section:
        main_layout.addWidget(comprasnet_section)

    processo_numero = self.data.get("processo")
    if processo_numero:
        query_param = quote(processo_numero)
        pncp_search_url = f"https://pncp.gov.br/app/contratos?q={query_param}"
        pncp_section = create_link_section(
            "Buscar Contrato no Portal Nacional (PNCP):", 
            pncp_search_url, 
            f"Buscar processo {processo_numero} no PNCP"
        )
        if pncp_section:
            main_layout.addWidget(pncp_section)
    
    # Container para os links dinâmicos da API
    self.links_container = QVBoxLayout()
    main_layout.addLayout(self.links_container)

    # --- NOVO: Campos editáveis para os links ---
    links_group = QGroupBox("Links de Documentos do Contrato")
    form_layout = QFormLayout(links_group)
    form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

    self.link_contrato_le, hbox_contrato = create_link_input_row(self, "Link Contrato (PDF):", "Cole o link do PDF do contrato")
    self.link_ta_le, hbox_ta = create_link_input_row(self, "Link Termo Aditivo (TA):", "Cole o link do Termo Aditivo")
    self.link_portaria_le, hbox_portaria = create_link_input_row(self, "Link Portaria:", "Cole o link da Portaria")
    self.link_pncp_espc_le, hbox_pncp = create_link_input_row(self, "Link PNCP Específico:", "Cole o link específico do contrato no PNCP")
    self.link_portal_marinha_le, hbox_marinha = create_link_input_row(self, "Link Portal Marinha:", "Cole o link do Portal da Marinha")

    form_layout.addRow(QLabel("<b>Link PDF do Contrato:</b>"), hbox_contrato)
    form_layout.addRow(QLabel("<b>Link Termo Aditivo (TA):</b>"), hbox_ta)
    form_layout.addRow(QLabel("<b>Link Portaria:</b>"), hbox_portaria)
    form_layout.addRow(QLabel("<b>Link PNCP Específico:</b>"), hbox_pncp)
    form_layout.addRow(QLabel("<b>Link Portal Marinha:</b>"), hbox_marinha)
    
    main_layout.addWidget(links_group)
    main_layout.addStretch()

    # --- Botão para buscar os links de arquivos ---
    files_button = QPushButton("Buscar e Preencher Link do Contrato (PDF) e Outros")
    button_hbox = QHBoxLayout()
    button_hbox.addStretch()
    button_hbox.addWidget(files_button)
    main_layout.addLayout(button_hbox)

    def fetch_and_display_file_links():
        files_button.setText("Buscando...")
        files_button.setEnabled(False)

        # Limpa os links antigos da API
        while self.links_container.count():
            child = self.links_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        arquivos, error_message = self.model.get_sub_data_for_contract(contrato_id, "arquivos")
        
        if error_message or not arquivos:
            error_label = QLabel(f"<b>{error_message or 'Nenhum arquivo encontrado na API.'}</b>")
            self.links_container.addWidget(error_label)
        else:
            link_contrato_encontrado = False
            for arquivo in reversed(arquivos):
                if arquivo.get("tipo") == "Contrato" and arquivo.get("path_arquivo") and not link_contrato_encontrado:
                    self.link_contrato_le.setText(arquivo["path_arquivo"])
                    link_contrato_encontrado = True
                
                link_url = arquivo.get("path_arquivo")
                link_description = arquivo.get("descricao") or arquivo.get("tipo") or "Clique aqui para abrir"
                section = create_link_section(f"Link para '{arquivo.get('tipo', 'Arquivo')}':", link_url, link_description)
                if section:
                    self.links_container.insertWidget(0, section)
            
            if not link_contrato_encontrado:
                print("Link do tipo 'Contrato' não encontrado nos arquivos da API.")

        files_button.setText("Buscar Links de Arquivos (PDF, etc.)")
        files_button.setEnabled(True)

    files_button.clicked.connect(fetch_and_display_file_links)
    
    return object_tab