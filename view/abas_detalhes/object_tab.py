from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QSize
import fitz  # PyMuPDF
import requests
import os
import time
import webbrowser

from utils.icon_loader import icon_manager

def get_download_folder(model_instance): # Adicionado model_instance como argumento
    """Retorna o caminho da pasta de download configurada ou a pasta Downloads padrão."""
    if model_instance:
        saved_path = model_instance.load_setting("pdf_download_path")
        if saved_path and os.path.isdir(saved_path):
            return saved_path
    return os.path.join(os.path.expanduser("~"), "Downloads") # Padrão

def get_pdf_url(self):
    """Obtém o link real do PDF a partir do JSON da API."""
    id_contrato = self.data.get("id", "")
    api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{id_contrato}/arquivos"

    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()  # Converte a resposta para uma lista de dicionários
            if isinstance(data, list) and len(data) > 0:  # Verifica se é uma lista e não está vazia
                # Idealmente, verificar o tipo de arquivo se a API puder retornar outros tipos
                # Por agora, assume-se que o primeiro é o PDF principal.
                if data[0].get("path_arquivo", "").lower().endswith(".pdf"):
                    return data[0].get("path_arquivo", None)
                print(f"Primeiro arquivo não é um PDF: {data[0].get('path_arquivo')}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter link do PDF: {e}")
    
    return None  # Retorna None se falhar

def download_pdf(self, model_instance, max_retries=5, wait_time=3): # Adicionado model_instance
    """
    Faz o download do PDF do contrato e salva na pasta Downloads/pdfs salvos.
    """
    pdf_url = get_pdf_url(self)

    if not pdf_url:
        print("Não foi possível obter o link do PDF.")
        return None

    download_folder = get_download_folder(model_instance) # Passa model_instance
    pdfs_folder = os.path.join(download_folder, "pdfs salvos")
    os.makedirs(pdfs_folder, exist_ok=True)

    # Obtém informações do contrato
    contrato_numero = self.data.get("numero", "")
    empresa_nome = self.data.get("fornecedor", {}).get("nome", "")
    responsavel = self.data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
    novo_nome_arquivo = f"{responsavel}_{contrato_numero} - {empresa_nome}.pdf".replace("/", "-")
    novo_pdf_path = os.path.join(pdfs_folder, novo_nome_arquivo)

    # Se o arquivo renomeado já existe, retorna direto
    if os.path.exists(novo_pdf_path):
        print(f"PDF já salvo: {novo_pdf_path}")
        return novo_pdf_path  

    # Nome original do arquivo antes de renomear
    pdf_filename = os.path.basename(pdf_url)
    pdf_path = os.path.join(pdfs_folder, pdf_filename)

    for tentativa in range(1, max_retries + 1):
        try:
            response = requests.get(pdf_url, timeout=10)
            if response.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                print(f"PDF baixado: {pdf_path}")

                # Renomeia para o formato desejado
                os.rename(pdf_path, novo_pdf_path)
                print(f"Arquivo renomeado para: {novo_pdf_path}")

                return novo_pdf_path  # Retorna o caminho do PDF salvo
            else:
                print(f"Tentativa {tentativa}: Erro {response.status_code}, aguardando...")
        
        except requests.exceptions.RequestException as e:
            print(f"Tentativa {tentativa}: Erro ao baixar PDF: {e}")

        time.sleep(wait_time)

    print("Falha ao baixar o PDF após várias tentativas.")
    return None

def open_pdf(self):
    """Baixa e abre o PDF no navegador."""
    pdf_path = download_pdf(self, self.model) # Passa self.model (que é model_instance)
    if pdf_path and os.path.exists(pdf_path):
        webbrowser.open(os.path.abspath(pdf_path))

class PDFViewer(QWidget):
    """Widget personalizado para visualizar PDFs."""
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.init_ui()

    def init_ui(self):
        """Inicializa a interface do visualizador de PDF."""
        layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        self.load_pdf()

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

    def load_pdf(self):
        """Carrega e exibe as páginas do PDF."""
        if not os.path.exists(self.pdf_path):
            self.content_layout.addWidget(QLabel("<b>Arquivo PDF não encontrado.</b>"))
            return

        try:
            doc = fitz.open(self.pdf_path)  # Abre o PDF com PyMuPDF
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)  # Carrega a página
                pix = page.get_pixmap()  # Renderiza a página como uma imagem

                # Converte a imagem para QImage
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(image)

                # Exibe a imagem em um QLabel
                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.content_layout.addWidget(label)

        except Exception as e:
            self.content_layout.addWidget(QLabel(f"<b>Erro ao carregar PDF:</b> {str(e)}"))

def create_object_tab(self):
    """Cria a aba para exibir o PDF do contrato."""
    object_tab = QWidget()
    layout = QVBoxLayout(object_tab)

    pdf_url = get_pdf_url(self)

    if pdf_url:
        # Cria um botão "VER PDF"
        ver_pdf_button = QPushButton("VER PDF")
        ver_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005BB5;
            }
        """)
        ver_pdf_button.clicked.connect(lambda: open_pdf(self))  # Abre o PDF ao clicar
        ver_pdf_button.setIcon(icon_manager.get_icon("download-pdf")) # copy_btn.setIcon(icon_manager.get_icon("copy"))
        ver_pdf_button.setIconSize(QSize(32, 32))
        layout.addWidget(ver_pdf_button)  # Adiciona o botão no topo da tela

    pdf_path = download_pdf(self, self.model) # Passa self.model (que é model_instance)
    if pdf_path and os.path.exists(pdf_path):
        pdf_viewer = PDFViewer(pdf_path)
        layout.addWidget(pdf_viewer)
    else:
        message_label = QLabel("<b>Não há nenhum documento para visualização</b>")
        layout.addWidget(message_label)

    return object_tab
