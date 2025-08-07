# view/abas_detalhes/object_tab.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from urllib.parse import quote

# As importações de 'requests' e 'json' não são mais necessárias aqui,
# pois a lógica de busca foi movida para o UASGModel.

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

# A função get_pdf_link foi removida daqui e sua lógica foi movida para o UASGModel.

def create_object_tab(self):
    """
    Cria a aba de links com um botão para carregar os links de arquivos
    do contrato, funcionando nos modos Online e Offline.
    """
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
    
    main_layout.addStretch() # Empurra o botão para baixo

    # --- Botão para buscar os links de arquivos (PDF e outros) ---
    files_button = QPushButton("Buscar Links de Arquivos (PDF, etc.)")
    # Removido o ícone fixo para não confundir
    
    button_hbox = QHBoxLayout()
    button_hbox.addStretch()
    button_hbox.addWidget(files_button)
    main_layout.addLayout(button_hbox)

    def fetch_and_display_file_links():
        """Função chamada pelo clique do botão, que agora usa o Model."""
        files_button.setText("Buscando...")
        files_button.setEnabled(False)

        # --- A MÁGICA ACONTECE AQUI ---
        # Pede os dados ao model, que sabe se está online ou offline
        arquivos, error_message = self.model.get_sub_data_for_contract(contrato_id, "arquivos")
        
        if error_message or not arquivos:
            msg = error_message if error_message else "Nenhum arquivo encontrado."
            error_frame = QFrame()
            error_frame.setFrameShape(QFrame.Shape.StyledPanel)
            error_layout = QVBoxLayout(error_frame)
            error_label = QLabel(f"<b>{msg}</b>")
            error_layout.addWidget(error_label)
            links_container.insertWidget(0, error_frame)
            files_button.setText("Tentar Novamente")
            files_button.setEnabled(True)
        else:
            # Se encontrou arquivos, cria um link para cada um
            for arquivo in reversed(arquivos): # reversed para inserir do último ao primeiro no topo
                link_url = arquivo.get("path_arquivo")
                # O texto do link será a descrição do arquivo, ou o tipo, ou um texto padrão
                link_description = arquivo.get("descricao") or arquivo.get("tipo") or "Clique aqui para abrir"
                
                section = create_link_section(
                    f"Link para '{arquivo.get('tipo', 'Arquivo')}':", 
                    link_url, 
                    link_description
                )
                if section:
                    links_container.insertWidget(0, section) # Insere no topo
            
            files_button.setVisible(False) # Oculta o botão após o sucesso

    files_button.clicked.connect(fetch_and_display_file_links)
    
    return object_tab