# view/abas_detalhes/object_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from urllib.parse import quote
import requests
#import json
from utils.icon_loader import icon_manager

def create_link_section(title, url, link_text):
    """Cria uma seção de link com título e URL clicável."""
    if not url:
        return None
    
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

def get_pdf_link(contrato_id):
    """Busca o link direto do PDF na API de arquivos do contrato."""
    if not contrato_id:
        return None
    
    api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/arquivos"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        if isinstance(data, list) and data and 'path_arquivo' in data[0]:
            return data[0]['path_arquivo']
    except Exception as e:
        print(f"Erro ao buscar link do PDF: {e}")
    return None

def create_object_tab(self):
    """Cria a aba de links com um botão para carregar o link do PDF sob demanda."""
    object_tab = QWidget()
    main_layout = QVBoxLayout(object_tab)
    main_layout.setSpacing(15)

    # Container para os resultados dos links, começa vazio
    links_container = QVBoxLayout()
    main_layout.addLayout(links_container)

    contrato_id = self.data.get("id")

    # --- Links que NÃO precisam de requisição extra são exibidos imediatamente ---
    comprasnet_url = f"https://contratos.comprasnet.gov.br/transparencia/contratos/{contrato_id}"
    comprasnet_section = create_link_section(
        "Link para a página do Contrato (Comprasnet):", 
        comprasnet_url,
        "Acessar página do Comprasnet"
    )
    if comprasnet_section:
        links_container.addWidget(comprasnet_section)

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
            links_container.addWidget(pncp_section)

     # 4. Adicionar uma nota explicativa
    if pncp_section:
        explicacao = QLabel(
        "<i>Nota: O link do PNCP realiza uma busca pelo número do processo. "
         "Clique para ver os resultados no portal.</i>" )
        explicacao.setWordWrap(True)
        main_layout.addWidget(explicacao)
    
    main_layout.addStretch() # Empurra o botão para baixo

    # --- Botão para buscar o link do PDF ---
    pdf_button = QPushButton("Buscar link direto para o contrato")
    pdf_button.setIcon(icon_manager.get_icon("download-pdf"))

    # Layout para alinhar o botão à direita
    button_hbox = QHBoxLayout()
    button_hbox.addStretch() # Espaço à esquerda
    button_hbox.addWidget(pdf_button) # Botão à direita
    main_layout.addLayout(button_hbox)

    def fetch_pdf_link():
        """Função chamada pelo clique do botão."""
        pdf_button.setText("Buscando...")
        pdf_button.setEnabled(False)

        pdf_url = get_pdf_link(contrato_id)
        
        if pdf_url:
            pdf_section = create_link_section(
                "Link direto para o PDF do Contrato:", 
                pdf_url, 
                "Clique aqui para Baixar o PDF"
            )
            # Insere o link do PDF no topo do container de links
            links_container.insertWidget(0, pdf_section)
            pdf_button.setVisible(False) # Oculta o botão após o sucesso
        else:
            # Cria um frame para a mensagem de erro
            error_frame = QFrame()
            error_frame.setFrameShape(QFrame.Shape.StyledPanel)
            error_layout = QVBoxLayout(error_frame)
            error_label = QLabel("<b>Link direto para o PDF não encontrado.</b>")
            error_layout.addWidget(error_label)
            links_container.insertWidget(0, error_frame)
            pdf_button.setText("Tentar Novamente")
            pdf_button.setEnabled(True)

    pdf_button.clicked.connect(fetch_pdf_link)
    
    return object_tab
