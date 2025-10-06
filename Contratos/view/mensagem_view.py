# Contratos/view/mensagem_view.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QTextEdit, QPushButton, QFrame, QSplitter, QWidget, QTabWidget)
from PyQt6.QtCore import Qt
from utils.icon_loader import icon_manager

class MensagemDialog(QDialog):
    """
    Define a interface da janela de geração de mensagens com abas para organização.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerador de Mensagem de Alerta")
        self.setMinimumSize(1100, 750)

        main_layout = QVBoxLayout(self)
        
        # --- TELA PRINCIPAL AGORA É UM QTabWidget ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- ABA 1: GERADOR DE MENSAGEM ---
        generator_tab = QWidget()
        generator_layout = QHBoxLayout(generator_tab)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # PAINEL ESQUERDO (Apenas Variáveis)
        variables_widget = QWidget()
        variables_layout = QVBoxLayout(variables_widget)
        variables_layout.addWidget(QLabel("<b>Índice de Variáveis</b>"))
        self.variables_list = QListWidget()
        variables_layout.addWidget(self.variables_list)
        
        # PAINEL DIREITO (Edição e Pré-visualização)
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        text_splitter = QSplitter(Qt.Orientation.Vertical)

        # Área de Edição
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("<b>Modelo em Edição:</b>"))
        self.current_template_label = QLabel("Nenhum")
        self.current_template_label.setStyleSheet("font-style: italic; color: #8AB4F8;")
        title_layout.addWidget(self.current_template_label)
        title_layout.addStretch()
        editor_layout.addLayout(title_layout)
        self.template_text_edit = QTextEdit()
        self.template_text_edit.setPlaceholderText("Selecione um modelo abaixo para carregar...")
        editor_layout.addWidget(self.template_text_edit)
        
        # Área de Pré-visualização
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.addWidget(QLabel("<b>Pré-visualização (com variáveis aplicadas)</b>"))
        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        preview_layout.addWidget(self.preview_text_edit)

        text_splitter.addWidget(editor_widget)
        text_splitter.addWidget(preview_widget)
        right_panel_layout.addWidget(text_splitter)
        
        # Seção de botões de modelo
        right_panel_layout.addWidget(QLabel("<b>Modelos Disponíveis</b>"))
        self.template_buttons_frame = QFrame()
        self.template_buttons_layout = QHBoxLayout(self.template_buttons_frame)
        self.template_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_panel_layout.addWidget(self.template_buttons_frame)
        
        main_splitter.addWidget(variables_widget)
        main_splitter.addWidget(right_panel_widget)
        main_splitter.setSizes([350, 750])
        generator_layout.addWidget(main_splitter)
        
        # Adiciona a primeira aba
        self.tabs.addTab(generator_tab, "Gerador de Mensagem")

        # --- ABA 2: COMENTÁRIOS ---
        comments_tab = QWidget()
        comments_layout = QVBoxLayout(comments_tab)
        
        comments_layout.addWidget(QLabel("<b>Registros e Comentários da Mensagem</b>"))
        self.comment_list = QListWidget()
        comments_layout.addWidget(self.comment_list)

        comment_buttons_layout = QHBoxLayout()
        comment_buttons_layout.addStretch()
        
        self.add_comment_button = QPushButton("Adicionar Comentário")
        
        # --- NOVO BOTÃO DE COPIAR ---
        self.copy_comment_button = QPushButton()
        self.copy_comment_button.setIcon(icon_manager.get_icon("copy"))
        self.copy_comment_button.setToolTip("Copiar selecionado(s)")
        
        self.delete_comment_button = QPushButton("Excluir Selecionado(s)")

        comment_buttons_layout.addWidget(self.add_comment_button)
        comment_buttons_layout.addWidget(self.delete_comment_button)
        comment_buttons_layout.addWidget(self.copy_comment_button) # Adicionado aqui
        
        comments_layout.addLayout(comment_buttons_layout)
        
        self.tabs.addTab(comments_tab, "Comentários")

        # --- BOTÕES INFERIORES (Fora das abas) ---
        bottom_buttons_layout = QHBoxLayout()
        self.save_template_button = QPushButton("Salvar Modelo")
        self.save_comments_button = QPushButton("Salvar Comentários")
        bottom_buttons_layout.addWidget(self.save_template_button)
        bottom_buttons_layout.addWidget(self.save_comments_button)
        bottom_buttons_layout.addStretch()
        self.copy_button = QPushButton("Copiar Mensagem Pronta")
        main_layout.addLayout(bottom_buttons_layout)