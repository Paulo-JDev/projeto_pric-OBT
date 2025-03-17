from PyQt6.QtWidgets import QLabel, QLineEdit
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression

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
    search_label = QLabel()
    search_label.setPixmap(icons["magnifying-glass"].pixmap(30, 30))
    layout.addWidget(search_label)

    search_bar = QLineEdit()
    search_bar.setPlaceholderText("Digite para buscar...")
    search_bar.setStyleSheet("""
        QLineEdit {
            background-color: #1e1e1e;
            color: #8AB4F7;
            font-size: 14px;
            font-weight: bold;
            padding: 8px;
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
    layout.addWidget(search_bar)
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
