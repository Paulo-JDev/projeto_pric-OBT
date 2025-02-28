import os
import sys
import requests
import json
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox, QGridLayout, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt

class DetailsDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Contrato")

        # Definir o tamanho fixo da janela
        self.setFixedSize(1200, 500)

        # Layout do diálogo
        layout = QFormLayout(self)

        # Filtrar itens com valor "None"
        filtered_data = {key: value for key, value in data.items() if value is not None}

        for key, value in filtered_data.items():
            key_label = QLabel(f"{key.capitalize()}: ")
            value_label = QLabel(str(value))

            # Configurar quebra de linha automática para o valor
            value_label.setWordWrap(True)

            layout.addRow(key_label, value_label)



class UASGApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerenciador de UASG")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab 1: Input UASG
        self.input_tab = QWidget()
        self.input_layout = QVBoxLayout()
        self.input_tab.setLayout(self.input_layout)

        self.label = QLabel("Digite o número do UASG:")
        self.input_layout.addWidget(self.label)

        self.uasg_input = QLineEdit()
        self.input_layout.addWidget(self.uasg_input)

        self.fetch_button = QPushButton("Buscar e Criar Tabela")
        self.fetch_button.clicked.connect(self.fetch_and_create_table)
        self.input_layout.addWidget(self.fetch_button)

        self.delete_button = QPushButton("Deletar Arquivo e Banco de Dados")
        self.delete_button.clicked.connect(self.delete_uasg_data)
        self.input_layout.addWidget(self.delete_button)

        self.tabs.addTab(self.input_tab, "Buscar UASG")

        # Tab 2: Display Tables
        self.table_tab = QWidget()
        self.table_layout = QVBoxLayout()
        self.table_tab.setLayout(self.table_layout)

        # Buttons grid
        self.buttons_grid = QGridLayout()

        self.menu_button = QPushButton("UASG")
        self.menu_button.setFixedSize(70, 30)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: #808080;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #139bf0;
            }
        """)
        self.menu_button.setMenu(QMenu(self.menu_button))
        self.buttons_grid.addWidget(self.menu_button, 0, 0)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.setFixedSize(70, 30)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        self.clear_button.clicked.connect(self.clear_table_tab)
        self.buttons_grid.addWidget(self.clear_button, 0, 1)

        self.table_layout.addLayout(self.buttons_grid)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Digite para buscar...")
        self.search_bar.textChanged.connect(self.filter_table)
        self.table_layout.addWidget(self.search_bar)

        # Table display
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Número", "Nome", "Licitação", "Fornecedor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table_layout.addWidget(self.table)

        self.tabs.addTab(self.table_tab, "Visualizar Tabelas")

        # Store loaded UASGs
        self.loaded_uasgs = {}
        self.current_data = []
        self.current_uasg = None

        # Load saved UASGs
        self.load_saved_uasgs()

    def load_saved_uasgs(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        database_dir = os.path.join(base_dir, "database")
        if not os.path.exists(database_dir):
            return

        for uasg_dir in os.listdir(database_dir):
            if uasg_dir.startswith("uasg_"):
                uasg_path = os.path.join(database_dir, uasg_dir)
                json_file = os.path.join(uasg_path, f"{uasg_dir}_contratos.json")
                if os.path.isfile(json_file):
                    with open(json_file, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        uasg = uasg_dir.split("_")[1]
                        self.loaded_uasgs[uasg] = data
                        self.add_uasg_to_menu(uasg)

    def fetch_and_create_table(self):
        uasg = self.uasg_input.text()
        if not uasg:
            self.label.setText("Por favor, insira um número UASG válido.")
            return

        if uasg in self.loaded_uasgs:
            self.label.setText(f"UASG {uasg} já carregada.")
            return

        attempts = 0
        max_attempts = 5
        success = False

        while attempts < max_attempts and not success:
            try:
                # URL da API
                url_api = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"
                resposta = requests.get(url_api, timeout=10)
                resposta.raise_for_status()
                dados = resposta.json()

                # Diretório para salvar os arquivos
                base_dir = os.path.dirname(os.path.abspath(__file__))
                database_dir = os.path.join(base_dir, "database", f"uasg_{uasg}")
                os.makedirs(database_dir, exist_ok=True)

                # Salva os dados em JSON
                arquivo_saida = os.path.join(database_dir, f"uasg_{uasg}_contratos.json")
                with open(arquivo_saida, 'w', encoding='utf-8') as arquivo:
                    json.dump(dados, arquivo, ensure_ascii=False, indent=4)

                # Criação do banco de dados
                nome_db = os.path.join(database_dir, f"uasg_{uasg}_contratos.db")
                conexao = sqlite3.connect(nome_db)
                cursor = conexao.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contratos (
                        numero INTEGER,
                        nome TEXT,
                        licitacao_numero TEXT,
                        fornecedor_nome TEXT
                    )
                ''')

                # Inserção de dados
                for contrato in dados:
                    numero = contrato.get("numero")
                    nome = contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido")
                    licitacao_numero = contrato.get("licitacao_numero")
                    fornecedor_nome = contrato.get("fornecedor", {}).get("nome")

                    cursor.execute('''
                        INSERT INTO contratos (numero, nome, licitacao_numero, fornecedor_nome)
                        VALUES (?, ?, ?, ?)
                    ''', (numero, nome, licitacao_numero, fornecedor_nome))

                conexao.commit()
                conexao.close()

                # Adiciona a UASG carregada
                self.loaded_uasgs[uasg] = dados
                self.add_uasg_to_menu(uasg)
                self.update_table(uasg)
                self.tabs.setCurrentWidget(self.table_tab)
                self.label.setText(f"Dados da UASG {uasg} carregados com sucesso!")
                success = True

            except (requests.exceptions.RequestException, ValueError) as e:
                attempts += 1
                self.label.setText(f"Tentativa {attempts}/{max_attempts} falhou. Erro: {e}")

        if not success:
            self.label.setText("Não foi possível buscar os dados após 5 tentativas. Verifique a conexão ou o número da UASG.")

    def delete_uasg_data(self):
        uasg = self.uasg_input.text()
        if not uasg:
            QMessageBox.warning(self, "Erro", "Por favor, insira um número UASG válido para deletar.")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        database_dir = os.path.join(base_dir, "database", f"uasg_{uasg}")
        if os.path.exists(database_dir):
            for file in os.listdir(database_dir):
                os.remove(os.path.join(database_dir, file))
            os.rmdir(database_dir)
            QMessageBox.information(self, "Sucesso", f"UASG {uasg} e seus dados foram deletados com sucesso.")
            self.loaded_uasgs.pop(uasg, None)
            self.refresh_uasg_menu()
    
        # else:
        #     QMessageBox.warning(self, "Erro", "Nenhum dado encontrado para a UASG informada.")

    def add_uasg_to_menu(self, uasg):
        action = self.menu_button.menu().addAction(f"UASG {uasg}")
        action.triggered.connect(lambda: self.update_table(uasg))

    def refresh_uasg_menu(self):
        self.menu_button.menu().clear()
        for uasg in self.loaded_uasgs:
            self.add_uasg_to_menu(uasg)

    def update_table(self, uasg):
        self.current_data = self.loaded_uasgs[uasg]
        self.populate_table(self.current_data)

    def populate_table(self, data):
        # Filtrar itens com valor "None"
        filtered_data = [
            {key: value for key, value in contrato.items() if value is not None}
            for contrato in data
        ]

        self.table.setRowCount(len(filtered_data))
        for row_index, contrato in enumerate(filtered_data):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(contrato.get("numero", ""))))
            self.table.setItem(row_index, 1, QTableWidgetItem(
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
            ))
            self.table.setItem(row_index, 2, QTableWidgetItem(contrato.get("licitacao_numero", "")))
            self.table.setItem(row_index, 3, QTableWidgetItem(
                contrato.get("fornecedor", {}).get("nome", "")
            ))

    def filter_table(self):
        filter_text = self.search_bar.text().lower()
        filtered_data = [
            contrato for contrato in self.current_data
            if any(filter_text in str(value).lower() for value in contrato.values())
        ]
        self.populate_table(filtered_data)

    def clear_table_tab(self):
        self.search_bar.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        QMessageBox.information(self, "Limpeza", "A área foi limpa com sucesso!")

    def show_context_menu(self, position):
        item = self.table.itemAt(position)
        if item is None:
            return

        row = item.row()
        contrato = self.current_data[row]

        menu = QMenu(self)
        details_action = menu.addAction("Ver Detalhes")
        details_action.triggered.connect(lambda: self.show_details_dialog(contrato))
        menu.exec(self.table.mapToGlobal(position))

    def show_details_dialog(self, contrato):
        details_dialog = DetailsDialog(contrato, self)
        details_dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UASGApp()
    window.show()
    sys.exit(app.exec())
