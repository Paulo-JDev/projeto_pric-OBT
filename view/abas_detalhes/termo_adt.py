from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
    QListWidget, QListWidgetItem, QSplitter, QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
import json
import requests

class JsonHighlighter(QSyntaxHighlighter):
    """Destacador de sintaxe para JSON"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # Formato para strings (em verde)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#6A9955"))
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        
        # Formato para números (em azul claro)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((r'\b[0-9]+\b', number_format))
        self.highlighting_rules.append((r'\b[0-9]+\.[0-9]+\b', number_format))
        
        # Formato para null, true, false (em roxo)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#C586C0"))
        self.highlighting_rules.append((r'\bnull\b|\btrue\b|\bfalse\b', keyword_format))
        
        # Formato para chaves e colchetes (em amarelo)
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(QColor("#D7BA7D"))
        self.highlighting_rules.append((r'[\{\}\[\],:]', bracket_format))
        
        # Formato para chaves (em laranja)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"\s*:', key_format))
    
    def highlightBlock(self, text):
        import re
        
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, format)

def aba_termo_adt(self):
    """Cria a aba de 'Termo Aditivo' com visualizador de JSON"""
    termo_adt = QWidget()
    main_layout = QHBoxLayout(termo_adt)
    
    # Criar um splitter para dividir a lista de links e o conteúdo JSON
    splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # === PAINEL ESQUERDO - LINKS ===
    links_widget = QWidget()
    links_layout = QVBoxLayout(links_widget)
    
    # Título para a seção de links
    links_title = QLabel("LINKS:")
    links_title.setStyleSheet("font-size: 18px; font-weight: bold;")
    links_layout.addWidget(links_title)
    
    # Lista de links disponíveis
    self.links_list = QListWidget()
    self.links_list.setStyleSheet("""
        QListWidget {
            background-color: #1e1e1e;
            border: 1px solid #333;
            padding: 5px;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #333;
        }
        QListWidget::item:selected {
            background-color: #0078D7;
            color: white;
        }
        QListWidget::item:hover {
            background-color: #333;
        }
    """)
    
    # Tentar obter links da propriedade data
    termo_aditivo_info = self.data.get("links", {})
    
    # Lista de links padrão se não houver dados
    links_padrao = [
        "historico", "empenhos", "cronograma", "garantias", 
        "itens", "prepostos", "despesas_acessorias", "faturas",
        "ocorrencias", "terceirizados", "arquivos"
    ]
    
    # Adicionar links à lista
    if isinstance(termo_aditivo_info, dict) and termo_aditivo_info:
        for key in termo_aditivo_info.keys():
            item = QListWidgetItem(key)
            self.links_list.addItem(item)
    else:
        # Usar links padrão
        for link in links_padrao:
            item = QListWidgetItem(link)
            self.links_list.addItem(item)
    
    links_layout.addWidget(self.links_list)
    
    # === PAINEL DIREITO - CONTEÚDO JSON ===
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    
    # Título para o conteúdo
    content_title = QLabel("CONTEÚDO DO JSON")
    content_title.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
    content_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    content_layout.addWidget(content_title)
    
    # Área para exibir o JSON
    self.json_display = QTextEdit()
    self.json_display.setReadOnly(True)
    
    # Configurar a fonte monospace para melhor visualização
    font = QFont("Consolas", 10)
    self.json_display.setFont(font)
    
    self.json_display.setStyleSheet("""
        QTextEdit {
            background-color: #1e1e1e;
            border: 1px solid #333;
            color: white;
            padding: 10px;
        }
    """)
    
    # Adicionar o destacador de sintaxe JSON
    self.json_highlighter = JsonHighlighter(self.json_display.document())
    
    content_layout.addWidget(self.json_display)
    
    # Adicionar widgets ao splitter
    splitter.addWidget(links_widget)
    splitter.addWidget(content_widget)
    
    # Definir tamanhos iniciais do splitter (30% para links, 70% para conteúdo)
    splitter.setSizes([300, 700])
    
    # Adicionar o splitter ao layout principal
    main_layout.addWidget(splitter)
    
    # Função para carregar o JSON quando um link for clicado
    def load_json_content(item):
        # Limpar destaque de todos os itens
        for i in range(self.links_list.count()):
            list_item = self.links_list.item(i)
            list_item.setBackground(Qt.GlobalColor.transparent)
        
        # Destacar o item selecionado
        item.setBackground(QColor("#0078D7"))
        item.setForeground(QColor("#FFFFFF"))
        
        link_name = item.text()
        
        # URL do JSON com base no item selecionado
        url = None
        if isinstance(termo_aditivo_info, dict):
            url = termo_aditivo_info.get(link_name)
        
        if url and url.startswith("http"):
            try:
                # Tentar obter o JSON da URL
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        # Formatar o JSON para exibição
                        formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
                        # Definir o JSON com formatação de cores
                        self.json_display.setPlainText(formatted_json)
                    except json.JSONDecodeError:
                        self.json_display.setPlainText("Erro: O conteúdo recebido não é um JSON válido.")
                else:
                    self.json_display.setPlainText(f"Erro ao acessar a URL: {response.status_code}")
            except Exception as e:
                self.json_display.setPlainText(f"Erro de conexão: {str(e)}")
        else:
            # Exibir JSON simulado para demonstração
            dummy_json = {
                "titulo": f"Dados de {link_name}",
                "descricao": f"Esta é uma visualização de exemplo para {link_name}",
                "dados": {
                    "item1": "valor1",
                    "item2": "valor2",
                    "numeros": [1, 2, 3, 4, 5],
                    "status": True,
                    "disponivel": False,
                    "valores": None
                }
            }
            formatted_json = json.dumps(dummy_json, indent=4, ensure_ascii=False)
            self.json_display.setPlainText(formatted_json)
    
    # Conectar a função ao evento de clique na lista
    self.links_list.itemClicked.connect(load_json_content)
    
    # Selecionar o primeiro item automaticamente se houver itens
    if self.links_list.count() > 0:
        first_item = self.links_list.item(0)
        self.links_list.setCurrentItem(first_item)
        load_json_content(first_item)
    
    return termo_adt
