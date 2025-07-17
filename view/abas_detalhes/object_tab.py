from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

def create_object_tab(self):
    """
    Cria a aba 'PDF do contrato' com um link direto para a página de transparência.
    """
    object_tab = QWidget()
    layout = QVBoxLayout(object_tab)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Alinha o conteúdo ao topo
    
    # 1. Obter o ID do contrato
    contrato_id = self.data.get("id")

    if contrato_id:
        # 2. Construir a URL final
        url = f"https://contratos.comprasnet.gov.br/transparencia/contratos/{contrato_id}"

        # 3. Criar uma QLabel para exibir o link
        # Usamos HTML para criar um link clicável.
        link_text = f'<b>Link para o Contrato:</b> <a href="{url}">{url}</a>'
        
        link_label = QLabel(link_text)
        link_label.setOpenExternalLinks(True)  # Permite que o link seja aberto no navegador
        link_label.setWordWrap(True) # Garante que o link quebre a linha se for muito longo
        link_label.setTextFormat(Qt.TextFormat.RichText) # Habilita a interpretação do HTML

        # Adiciona um rótulo explicativo
        info_label = QLabel("Clique no link acima para abrir a página do contrato no seu navegador padrão.")
        info_label.setObjectName("info_label") # Para estilização, se necessário

        layout.addWidget(link_label)
        layout.addWidget(info_label)

    else:
        # Mensagem de erro se o ID do contrato não for encontrado
        message_label = QLabel("<b>Não foi possível gerar o link (ID do contrato não encontrado).</b>")
        layout.addWidget(message_label)

    return object_tab