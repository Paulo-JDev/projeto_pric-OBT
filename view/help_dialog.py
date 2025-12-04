import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, 
    QTabWidget, QScrollArea, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QDesktopServices, QFont
from utils.icon_loader import icon_manager

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda e Suporte")
        self.resize(700, 600)
        
        # Layout Principal
        main_layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Central de Ajuda")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fafafa;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Criar sistema de Abas
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Aba 1: FAQ
        self.tab_faq = QWidget()
        self.setup_faq_tab()
        self.tabs.addTab(self.tab_faq, "Perguntas Frequentes")

        # Aba 2: Documentos
        self.tab_docs = QWidget()
        self.setup_docs_tab()
        self.tabs.addTab(self.tab_docs, "Manuais e Documentos")

        # Botão Fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(100)
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        main_layout.addLayout(footer_layout)

    def setup_faq_tab(self):
        layout = QVBoxLayout(self.tab_faq)
        
        # Área de rolagem para caso existam muitas perguntas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20) # Espaço entre perguntas

        # --- LISTA DE PERGUNTAS E RESPOSTAS ---
        # Você pode adicionar mais itens a esta lista
        faq_data = [
            ("Como utilizo o sistema sem internet (Modo Offline)?", 
            "Primeiro, em um PC com internet, vá em 'Configurações' (engrenagem), digite a UASG e clique em 'Fazer DB'. Depois, ative o botão 'Modo de Obtenção de Dados' para a cor VERMELHA (Offline) para usar os dados baixados."),

            ("Como faço backup do meu trabalho (Status e Fiscais)?", 
            "Na aba 'Buscar UASG', clique no botão 'Status' e escolha 'Exportar Status (Backup)'. Isso gera um arquivo .json com suas edições. Para restaurar em outro computador, use a opção 'Importar Status'."),

            ("Posso mudar o local onde o Banco de Dados é salvo?", 
            "Sim. Vá em 'Configurações' e clique em 'Alterar Local...'. Você pode escolher uma nova pasta e o sistema perguntará se deseja copiar seus dados atuais ou criar um banco novo do zero."),

            ("Como cadastro um Contrato Manual antigo?", 
            "Recomendamos carregar a UASG primeiro. Depois, clique no botão 'Contrato Manual' (+) na aba inicial. É obrigatório preencher o Número do Contrato e a UASG para salvar."),

            ("Por que minhas alterações no contrato não foram salvas?", 
            "Para confirmar qualquer edição (objeto, fiscais, status), você deve obrigatoriamente clicar no botão 'SALVAR' no canto inferior direito da janela de detalhes antes de fechá-la.")
        ]

        for pergunta, resposta in faq_data:
            item_layout = QVBoxLayout()
            
            lbl_p = QLabel(f"❓ {pergunta}")
            lbl_p.setStyleSheet("font-weight: bold; font-size: 14px; color: #0056b3;")
            lbl_p.setWordWrap(True)
            
            lbl_r = QLabel(resposta)
            lbl_r.setStyleSheet("font-size: 13px; color: #fafafa; margin-left: 20px;")
            lbl_r.setWordWrap(True)
            
            item_layout.addWidget(lbl_p)
            item_layout.addWidget(lbl_r)
            
            # Linha separadora
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet("background-color: #ddd;")
            
            content_layout.addLayout(item_layout)
            content_layout.addWidget(line)

        content_layout.addStretch() # Empurra tudo para cima
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def setup_docs_tab(self):
        layout = QVBoxLayout(self.tab_docs)
        
        lbl_info = QLabel("Clique nos botões abaixo para abrir ou baixar os manuais.")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        # Área de lista de arquivos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # --- LISTA DE ARQUIVOS ---
        # Certifique-se de colocar esses arquivos na pasta 'docs' do seu projeto
        docs_list = [
            ("Manual_do_Usuario.pdf", "Guia completo de utilização do sistema."),
            ("Fluxo_de_Processos.pdf", "Diagrama de fluxo de contratações."),
            ("Notas_de_Versao.txt", "Lista de atualizações recentes.")
        ]

        # Caminho base onde os docs estão (ajuste conforme sua estrutura)
        base_docs_path = os.path.join(os.getcwd(), "docs") 

        for filename, description in docs_list:
            doc_frame = QFrame()
            doc_frame.setStyleSheet("QFrame { background-color: #f9f9f9; color: gray; border: 1px solid #ccc; border-radius: 5px; }")
            row_layout = QHBoxLayout(doc_frame)

            # Ícone
            icon_lbl = QLabel()
            if filename.endswith(".pdf"):
                icon_lbl.setPixmap(icon_manager.get_icon("pdf").pixmap(32, 32))
            else:
                icon_lbl.setPixmap(icon_manager.get_icon("arquivo").pixmap(32, 32))
            
            # Textos
            text_layout = QVBoxLayout()
            lbl_name = QLabel(filename)
            lbl_name.setStyleSheet("font-weight: bold;")
            lbl_desc = QLabel(description)
            lbl_desc.setStyleSheet("color: gray; font-size: 11px;")
            text_layout.addWidget(lbl_name)
            text_layout.addWidget(lbl_desc)

            # Botão Abrir
            btn_open = QPushButton("Abrir")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            # Usamos lambda com val padrão para capturar o valor atual do loop
            btn_open.clicked.connect(lambda _, f=filename: self.open_document(os.path.join(base_docs_path, f)))

            row_layout.addWidget(icon_lbl)
            row_layout.addLayout(text_layout)
            row_layout.addStretch()
            row_layout.addWidget(btn_open)

            content_layout.addWidget(doc_frame)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def open_document(self, file_path):
        """Tenta abrir o arquivo com o programa padrão do sistema."""
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "Arquivo não encontrado", 
                                f"Não foi possível localizar o arquivo:\n{file_path}\n\nVerifique se ele existe na pasta 'docs'.")