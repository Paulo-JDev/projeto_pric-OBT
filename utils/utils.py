from PyQt6.QtWidgets import QLabel, QLineEdit, QHBoxLayout
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression
import os
import sys


def refresh_uasg_menu(self):
        """Atualiza o menu com as UASGs carregadas."""
        menu = self.view.menu_button.menu()
        menu.clear()  # Limpa o menu antes de adicionar as UASGs

        if not self.loaded_uasgs:
            # Se não houver UASGs carregadas, desabilita o botão
            self.view.menu_button.setEnabled(False)
            print("Nenhuma UASG carregada. Botão desabilitado.")
        else:
            # Se houver UASGs carregadas, habilita o botão e adiciona as UASGs ao menu
            self.view.menu_button.setEnabled(True)
            for uasg in self.loaded_uasgs:
                action = menu.addAction(f"UASG {uasg}")
                action.triggered.connect(lambda checked, uasg=uasg: self.update_table(uasg))

class MultiColumnFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_regular_expression = QRegularExpression()
    
    def setFilterRegularExpression(self, regex):
        self.filter_regular_expression = regex
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for column in range(self.sourceModel().columnCount()):
            index = self.sourceModel().index(source_row, column, source_parent)
            data = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            if data is not None:
                data_str = str(data)
                if self.filter_regular_expression.match(data_str).hasMatch():
                    return True  
        return False  

def on_search_text_changed(text, proxy_model):
    regex = QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption)
    proxy_model.setFilterRegularExpression(regex)

def setup_search_bar(icons, layout, proxy_model, table_view):
    # Criar um layout horizontal para a barra de busca
    search_layout = QHBoxLayout()
    search_layout.setContentsMargins(0, 0, 0, 0)  # Sem margens
    search_layout.setSpacing(5)  # Espaçamento mínimo
    
    # Label com ícone
    search_label = QLabel()
    search_label.setPixmap(icons["magnifying-glass"].pixmap(24, 24))  # Ícone menor
    search_layout.addWidget(search_label)

    # Campo de busca
    search_bar = QLineEdit()
    search_bar.setPlaceholderText("Digite para buscar...")
    search_bar.setStyleSheet("""
        QLineEdit {
            background-color: #1e1e1e;
            color: #8AB4F7;
            font-size: 14px;
            font-weight: bold;
            padding: 5px 8px;
            border: 1px solid #8AB4F7;
            border-radius: 5px; 
        }
        QLineEdit:focus {
            border: 1px solid #8AB4F7;
            background-color: #181928;
            color: #FFFFFF;
            border-radius: 5px;
        }
    """) 
    
    search_bar.textChanged.connect(lambda text: update_search_and_selection(text, proxy_model, table_view))
    search_layout.addWidget(search_bar)
    
    # Adiciona o layout horizontal ao layout principal
    layout.addLayout(search_layout)
    
    return search_bar

def update_search_and_selection(text, proxy_model, table_view):
    proxy_model.setFilterRegularExpression(QRegularExpression(text, QRegularExpression.PatternOption.CaseInsensitiveOption))
    
    # Manter a seleção ao filtrar
    selected_indexes = table_view.selectionModel().selectedIndexes()
    selected_rows = {proxy_model.mapToSource(index).row() for index in selected_indexes}
    
    table_view.selectionModel().clearSelection()
    
    for row in selected_rows:
        for column in range(table_view.model().columnCount()):
            proxy_index = proxy_model.mapFromSource(table_view.model().index(row, column))
            if proxy_index.isValid():
                table_view.selectionModel().select(proxy_index, table_view.selectionModel().SelectionFlag.Select | table_view.selectionModel().SelectionFlag.Rows)
                break

def resource_path(relative_path):
    """Retorna o caminho absoluto para um recurso, funcionando tanto no desenvolvimento quanto no empacotamento."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
