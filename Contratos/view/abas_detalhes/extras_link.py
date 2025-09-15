from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
    QListWidget, QListWidgetItem, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from utils.icon_loader import icon_manager
import json
import requests

class JsonHighlighter(QSyntaxHighlighter):
    """Destacador de sintaxe para JSON (código inalterado)."""
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
        self.highlighting_rules.append((r'\b[0-9]+\.?[0-9]*\b', number_format))
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
                length = match.end() - start
                self.setFormat(start, length, format)

def aba_extras_link(self):
    """Cria a aba de 'Extras' com visual aprimorado e carregamento por clique."""
    termo_adt = QWidget()
    main_layout = QHBoxLayout(termo_adt)
    
    splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # === PAINEL ESQUERDO - LINKS ===
    links_widget = QWidget()
    links_layout = QVBoxLayout(links_widget)
    
    links_title_layout = QHBoxLayout()
    links_icon = QLabel()
    links_icon.setPixmap(icon_manager.get_icon("url2").pixmap(24, 24))
    links_title = QLabel("INFORMAÇÕES ADICIONAIS") # Título melhorado
    links_title.setStyleSheet("font-size: 16px; font-weight: bold;")
    links_title_layout.addWidget(links_icon)
    links_title_layout.addWidget(links_title)
    links_title_layout.addStretch()
    links_layout.addLayout(links_title_layout)
    
    self.links_list = QListWidget()
    
    # --- Popula a lista de links com base no modo (Online/Offline) ---
    mode = self.model.load_setting("data_mode", "Online")
    links_para_mostrar = []
    if mode == "Offline":
        links_para_mostrar = ["historico", "empenhos", "itens", "arquivos"]
    else:
        links_para_mostrar = self.data.get("links", {}).keys()
        
    for key in links_para_mostrar:
        # --- MELHORIA VISUAL APLICADA AQUI ---
        # Formata o texto para melhor leitura (ex: "historico" -> "Histórico")
        display_text = key.replace('_', ' ').capitalize()
        item = QListWidgetItem(display_text)
        
        # Define uma fonte maior para os itens da lista
        font = QFont()
        font.setPointSize(11)
        item.setFont(font)
        
        # Guarda o nome original da chave (ex: "historico") nos dados do item
        item.setData(Qt.ItemDataRole.UserRole, key)
        self.links_list.addItem(item)
    
    links_layout.addWidget(self.links_list)
    
    # === PAINEL DIREITO - CONTEÚDO JSON ===
    content_widget = QWidget()
    content_layout = QVBoxLayout(content_widget)
    
    content_title_layout = QHBoxLayout()
    content_title = QLabel("CONTEÚDO DO JSON")
    content_title.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
    # --- O BOTÃO "MAIS REQUISIÇÕES" FOI REMOVIDO DAQUI ---
    content_title_layout.addStretch()
    content_title_layout.addWidget(content_title)
    content_icon = QLabel()
    content_icon.setPixmap(icon_manager.get_icon("brace").pixmap(24, 24))
    content_title_layout.addWidget(content_icon)
    content_title_layout.addStretch()
    content_layout.addLayout(content_title_layout)
    
    self.json_display = QTextEdit()
    self.json_display.setReadOnly(True)
    font = QFont("Consolas", 10)
    self.json_display.setFont(font)
    self.json_highlighter = JsonHighlighter(self.json_display.document())
    content_layout.addWidget(self.json_display)
    
    splitter.addWidget(links_widget)
    splitter.addWidget(content_widget)
    splitter.setSizes([300, 700])
    main_layout.addWidget(splitter)
    
    def load_json_content(item):
        """Busca o JSON do item clicado, usando o cache."""
        # Pega o nome original da chave dos dados do item
        link_name = item.data(Qt.ItemDataRole.UserRole)
        
        # Verifica se o resultado já está no cache
        if link_name in self.json_cache:
            print(f"✅ Carregando '{link_name}' do cache.")
            json_data, error_message = self.json_cache[link_name]
        else:
            # Se não está no cache, busca no model
            contrato_id = self.data.get("id")
            self.json_display.setPlainText(f"Buscando dados de '{link_name}'...")
            json_data, error_message = self.model.get_sub_data_for_contract(contrato_id, link_name)
            # Guarda o resultado no cache para futuras consultas
            if not error_message:
                print(f"💾 Salvando '{link_name}' no cache.")
                self.json_cache[link_name] = (json_data, error_message)

        if error_message or not json_data:
            msg = error_message if error_message else "Nenhum dado encontrado."
            self.json_display.setPlainText(f"Erro: {msg}")
        else:
            try:
                formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
                self.json_display.setPlainText(formatted_json)
            except TypeError:
                self.json_display.setPlainText("Erro: Os dados recebidos não puderam ser formatados.")

    # --- CONEXÃO DO SINAL RESTAURADA PARA O CLIQUE NA LISTA ---
    self.links_list.itemClicked.connect(load_json_content)
    
    # Seleciona e carrega o primeiro item automaticamente
    if self.links_list.count() > 0:
        first_item = self.links_list.item(0)
        self.links_list.setCurrentItem(first_item)
        load_json_content(first_item)
    
    return termo_adt