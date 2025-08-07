from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QTextEdit, QPushButton, QFrame, QSplitter, QWidget)
from PyQt6.QtCore import Qt

class MensagemDialog(QDialog):
    """
    Define a interface da janela de geração de mensagens com pré-visualização.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerador de Mensagem de Alerta")
        self.setMinimumSize(900, 600)

        main_layout = QVBoxLayout(self)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- PAINEL ESQUERDO (Variáveis) ---
        variables_widget = QWidget()
        variables_layout = QVBoxLayout(variables_widget)
        variables_layout.addWidget(QLabel("<b>Índice de Variáveis</b>"))
        self.variables_list = QListWidget()
        variables_layout.addWidget(self.variables_list)
        
        # --- PAINEL DIREITO (Edição e Pré-visualização) ---
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        
        text_splitter = QSplitter(Qt.Orientation.Vertical)

        # Área de Edição (Superior)
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # --- CAMPO QUE ESTAVA FALTANDO, ADICIONADO AQUI ---
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("<b>Modelo em Edição:</b>"))
        self.current_template_label = QLabel("Nenhum") # Este é o campo que faltava
        self.current_template_label.setStyleSheet("font-style: italic; color: #8AB4F8;")
        title_layout.addWidget(self.current_template_label)
        title_layout.addStretch()
        editor_layout.addLayout(title_layout)
        
        self.template_text_edit = QTextEdit()
        self.template_text_edit.setPlaceholderText("Selecione um modelo abaixo para carregar...")
        editor_layout.addWidget(self.template_text_edit)
        
        # Área de Pré-visualização (Inferior)
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
        main_splitter.setSizes([300, 600])
        main_layout.addWidget(main_splitter)
        
        # Botões Inferiores
        bottom_buttons_layout = QHBoxLayout()
        self.save_template_button = QPushButton("Salvar Modelo")
        bottom_buttons_layout.addWidget(self.save_template_button)
        bottom_buttons_layout.addStretch()
        self.copy_button = QPushButton("Copiar Mensagem Pronta")
        bottom_buttons_layout.addWidget(self.copy_button)
        main_layout.addLayout(bottom_buttons_layout)