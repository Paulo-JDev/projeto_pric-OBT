# view/abas_detalhes/object_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from urllib.parse import quote
import requests
import json

def create_link_section(title, url, link_text):
    """Cria uma seção de link com título e URL clicável."""
    if not url:
        return None
    
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.StyledPanel)
    layout = QVBoxLayout(frame)
    
    display_html = f'<b>{title}</b><br><a href="{url}">{link_text}</a>'
    
    link_label = QLabel(display_html)
    link_label.setOpenExternalLinks(True)
    link_label.setWordWrap(True)
    link_label.setTextFormat(Qt.TextFormat.RichText)
    
    layout.addWidget(link_label)
    return frame

def get_pdf_link(contrato_id):
    """
    Busca o link direto do PDF na API de arquivos do contrato.
    Retorna o URL do 'path_arquivo' ou None se não encontrar.
    """
    if not contrato_id:
        return None
    
    api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/arquivos"
    print(f"Buscando link do PDF em: {api_url}")

    try:
        response = requests.get(api_url, timeout=10)
        # Se a requisição falhar (ex: 404), não continua
        if response.status_code != 200:
            print(f"API de arquivos retornou status {response.status_code}. Nenhum PDF encontrado.")
            return None

        data = response.json()
        
        # Verifica se a resposta é uma lista, se não está vazia e se o primeiro item tem a chave 'path_arquivo'
        if isinstance(data, list) and data and 'path_arquivo' in data[0]:
            pdf_url = data[0]['path_arquivo']
            print(f"Link do PDF encontrado: {pdf_url}")
            return pdf_url
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ao buscar link do PDF para contrato {contrato_id}: {e}")
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        # Se a resposta JSON for vazia ([]) ou malformada, o erro será capturado aqui.
        print(f"Resposta da API de arquivos não continha um link de PDF válido para o contrato {contrato_id}: {e}")
        
    return None

def create_object_tab(self):
    """
    Cria a aba de links com um link para o Comprasnet e um link de busca para o PNCP.
    """
    object_tab = QWidget()
    main_layout = QVBoxLayout(object_tab)
    main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    main_layout.setSpacing(15) # Adiciona espaço entre os links

    contrato_id = self.data.get("id")

    # 1. Buscar o link direto para o PDF
    pdf_url = get_pdf_link(contrato_id)
    if pdf_url:
        pdf_section = create_link_section("Link direto para o PDF do Contrato:", pdf_url, "Clique aqui para Baixar o PDF")
        if pdf_section:
            main_layout.addWidget(pdf_section)

    # 2. Gerar link para o Comprasnet Contratos
    comprasnet_url = None
    if contrato_id:
        comprasnet_url = f"https://contratos.comprasnet.gov.br/transparencia/contratos/{contrato_id}"
    
    comprasnet_section = create_link_section(
        "Link para a página do Contrato (Comprasnet):", 
        comprasnet_url,
        "Acessar página do Comprasnet" # Texto que o usuário verá
    )
    if comprasnet_section:
        main_layout.addWidget(comprasnet_section)

    # 3. Gerar link de BUSCA para o PNCP usando o número do processo
    processo_numero = self.data.get("processo")
    pncp_search_url = None
    if processo_numero:
        # Codifica o número do processo para ser usado em uma URL (ex: substitui '/' por '%2F')
        query_param = quote(processo_numero)
        pncp_search_url = f"https://pncp.gov.br/app/contratos?q={query_param}"
    
    pncp_section = create_link_section("Buscar Contrato no Portal Nacional (PNCP):", pncp_search_url, f"Buscar processo {processo_numero} no PNCP")
    if pncp_section:
        main_layout.addWidget(pncp_section)

    # 4. Adicionar uma nota explicativa
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