# view/abas_detalhes/object_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from urllib.parse import quote

def create_link_section(title, url):
    """Cria uma seção de link com título e URL clicável."""
    if not url:
        return None
    
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QVBoxLayout(frame)
    
    link_text = f'<b>{title}</b><br><a href="{url}">{url}</a>'
    
    link_label = QLabel(link_text)
    link_label.setOpenExternalLinks(True)
    link_label.setWordWrap(True)
    link_label.setTextFormat(Qt.TextFormat.RichText)
    
    layout.addWidget(link_label)
    return frame

def create_object_tab(self):
    """
    Cria a aba de links com um link para o Comprasnet e um link de busca para o PNCP.
    """
    object_tab = QWidget()
    main_layout = QVBoxLayout(object_tab)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    main_layout.setSpacing(15) # Adiciona espaço entre os links

    # 1. Gerar link para o Comprasnet Contratos
    contrato_id = self.data.get("id")
    comprasnet_url = None
    if contrato_id:
        comprasnet_url = f"https://contratos.comprasnet.gov.br/transparencia/contratos/{contrato_id}"
    
    comprasnet_section = create_link_section("Link para Comprasnet Contratos:", comprasnet_url)
    if comprasnet_section:
        main_layout.addWidget(comprasnet_section)

    # 2. Gerar link de BUSCA para o PNCP usando o número do processo
    processo_numero = self.data.get("processo")
    pncp_search_url = None
    if processo_numero:
        # Codifica o número do processo para ser usado em uma URL (ex: substitui '/' por '%2F')
        query_param = quote(processo_numero)
        pncp_search_url = f"https://pncp.gov.br/app/contratos?q={query_param}"
    
    pncp_section = create_link_section("Buscar Contrato no Portal Nacional (PNCP):", pncp_search_url)
    if pncp_section:
        main_layout.addWidget(pncp_section)

    # 3. Adicionar uma nota explicativa
    if pncp_section:
        explicacao = QLabel(
            "<i>Nota: O link do PNCP realiza uma busca pelo número do processo. "
            "Clique para ver os resultados no portal.</i>"
        )
        explicacao.setWordWrap(True)
        main_layout.addWidget(explicacao)

    # Se nenhum link pôde ser gerado
    if not comprasnet_section and not pncp_section:
        message_label = QLabel("<b>Nenhum link pôde ser gerado (faltam dados como ID ou N° do Processo).</b>")
        main_layout.addWidget(message_label)
        
    main_layout.addStretch() # Empurra tudo para cima

    return object_tab