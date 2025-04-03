import json
#import tabulate
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QComboBox
from PyQt6.QtCore import Qt

def aba_termo_adt(self):
    termo_adt = QWidget()
    layout = QVBoxLayout(termo_adt)

    key_label = QLabel("Termo Aditivo:")
    termo_aditivo_info = self.data.get("links", {})

    combo = QComboBox()
    if isinstance(termo_aditivo_info, dict):
        combo.addItems(termo_aditivo_info.keys())

    json_viewer = QTextEdit()
    json_viewer.setReadOnly(True)

    def update_json_viewer():
        chave_selecionada = combo.currentText()
        url = termo_aditivo_info.get(chave_selecionada, "Nenhuma informação disponível.")
        
        if url.startswith("http"):  # Verifica se é um link válido
            try:
                import requests
                response = requests.get(url)
                json_data = response.json()

                # # Formata o JSON em uma tabela
                # table = tabulate.tabulate(json_data, headers="keys", tablefmt="grid")

                # Formata o JSON para exibir de forma mais organizada
                formatted_json = json.dumps(json_data, indent=4)
                
                json_viewer.setText(str(formatted_json))
            except Exception as e:
                json_viewer.setText(f"Erro ao carregar JSON: {e}")
        else:
            json_viewer.setText(url)  # Caso não seja um link, exibe o texto normal

    combo.currentIndexChanged.connect(update_json_viewer)

    layout.addWidget(key_label)
    layout.addWidget(combo)
    layout.addWidget(json_viewer)

    update_json_viewer()  # Exibir o primeiro link ao carregar

    return termo_adt

# import json
# import requests
# import tempfile
# import webbrowser
# import os
# from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextBrowser, 
#                             QLabel, QComboBox, QMessageBox)
# from PyQt6.QtCore import Qt, QUrl

# def aba_termo_adt(self):
    termo_adt = QWidget()
    layout = QVBoxLayout(termo_adt)

    key_label = QLabel("Termo Aditivo:")
    termo_aditivo_info = self.data.get("links", {})

    combo = QComboBox()
    if isinstance(termo_aditivo_info, dict):
        combo.addItems(termo_aditivo_info.keys())

    json_viewer = QTextBrowser()
    json_viewer.setOpenLinks(False)
    json_viewer.setReadOnly(True)

    def update_json_viewer():
        chave_selecionada = combo.currentText()
        url = termo_aditivo_info.get(chave_selecionada, "Nenhuma informação disponível.")
        
        if url.startswith("http"):
            try:
                response = requests.get(url)
                json_data = response.json()
                
                # Formata o JSON com links clicáveis
                formatted_text = json.dumps(json_data, indent=4, ensure_ascii=False)
                formatted_text = formatted_text.replace('"path_arquivo": "', '"path_arquivo": "LINK:')
                formatted_text = formatted_text.replace('.pdf"', '.pdf">👉 Abrir PDF</a>"')
                formatted_text = formatted_text.replace('.PDF"', '.PDF">👉 Abrir PDF</a>"')
                formatted_text = formatted_text.replace('LINK:', '<a href="')
                
                json_viewer.setHtml(f"<pre>{formatted_text}</pre>")
                
                # Função para baixar e abrir PDF
                def handle_pdf_click(pdf_url):
                    try:
                        # Cria diretório temporário se não existir
                        temp_dir = os.path.join(tempfile.gettempdir(), "contratos_pdf")
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Extrai nome do arquivo da URL
                        pdf_url_str = pdf_url.toString()
                        file_name = os.path.basename(pdf_url_str)
                        temp_path = os.path.join(temp_dir, file_name)
                        
                        # Baixa o arquivo
                        response = requests.get(pdf_url_str, stream=True)
                        response.raise_for_status()
                        
                        # Salva o arquivo
                        with open(temp_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        # Verifica se o arquivo foi salvo
                        if os.path.exists(temp_path):
                            webbrowser.open(f"file://{temp_path}")
                        else:
                            QMessageBox.warning(termo_adt, "Erro", "O arquivo PDF não pôde ser salvo.")
                            
                    except requests.RequestException as e:
                        QMessageBox.critical(termo_adt, "Erro de Download", f"Não foi possível baixar o PDF:\n{str(e)}")
                    except Exception as e:
                        QMessageBox.critical(termo_adt, "Erro", f"Ocorreu um erro inesperado:\n{str(e)}")
                
                json_viewer.anchorClicked.connect(handle_pdf_click)
                
            except Exception as e:
                json_viewer.setPlainText(f"Erro ao carregar JSON: {str(e)}")
        else:
            json_viewer.setPlainText(url)

    combo.currentIndexChanged.connect(update_json_viewer)

    layout.addWidget(key_label)
    layout.addWidget(combo)
    layout.addWidget(json_viewer)

    update_json_viewer()

    return termo_adt