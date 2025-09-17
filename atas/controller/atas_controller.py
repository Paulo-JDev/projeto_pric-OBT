# atas/controller/atas_controller.py
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QStandardItem, QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from datetime import date, datetime
from atas.model.atas_model import AtasModel
from utils.icon_loader import icon_manager # Importa o gerenciador de ícones

class AtasController:
    def __init__(self, model: AtasModel, view):
        self.model = model
        self.view = view
        self._connect_signals()
        self.load_initial_data()

    def _connect_signals(self):
        """Conecta os sinais dos widgets da view aos métodos do controller."""
        self.view.import_button.clicked.connect(self.import_data)
        self.view.delete_button.clicked.connect(self.delete_selected_ata)
        self.view.add_button.clicked.connect(lambda: QMessageBox.information(self.view, "Info", "Funcionalidade 'Adicionar' em desenvolvimento."))
        self.view.generate_table_button.clicked.connect(lambda: QMessageBox.information(self.view, "Info", "Funcionalidade 'Gerar Tabela' em desenvolvimento."))

    def _parse_date_string(self, date_string):
        """Converte string de data no formato YYYY-MM-DD para objeto date."""
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    def _create_dias_item(self, dias_restantes):
        """Cria e formata o item da coluna 'Dias' com cores e ícones."""
        item = QStandardItem(str(dias_restantes))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = item.font()
        font.setBold(True)
        item.setFont(font)

        if isinstance(dias_restantes, int):
            if dias_restantes < 0:
                item.setForeground(Qt.GlobalColor.red)
                item.setIcon(icon_manager.get_icon("delete"))
            elif dias_restantes <= 89:
                item.setForeground(QBrush(QColor("#FFA500")))  # Laranja
                item.setIcon(icon_manager.get_icon("alert"))
            elif dias_restantes <= 179:
                item.setForeground(QBrush(QColor("#FFD700")))  # Amarelo
                item.setIcon(icon_manager.get_icon("mensagem"))
            else:
                item.setForeground(QBrush(QColor("#32CD32")))  # Verde
                item.setIcon(icon_manager.get_icon("aproved"))
        else:  # "N/A"
            item.setForeground(QBrush(QColor("#AAAAAA")))
            item.setIcon(icon_manager.get_icon("time"))
        return item

    def load_initial_data(self):
        """Carrega os dados do banco de dados e popula a tabela na inicialização."""
        try:
            atas = self.model.get_all_atas()
            self.populate_table(atas)
        except Exception as e:
            QMessageBox.critical(self.view, "Erro ao Carregar Dados", f"Não foi possível carregar os dados do banco de atas:\n{e}")

    def import_data(self):
        """Abre o diálogo para selecionar um arquivo e importa os dados."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Selecionar Planilha Excel",
            "",
            "Planilhas Excel (*.xlsx)"
        )
        if not file_path:
            return

        success, message = self.model.import_from_spreadsheet(file_path)
        if success:
            QMessageBox.information(self.view, "Importação Concluída", message)
            self.load_initial_data()
        else:
            QMessageBox.critical(self.view, "Erro na Importação", message)

    def delete_selected_ata(self):
        """Exclui a(s) linha(s) selecionada(s) da tabela e do banco de dados."""
        selected_proxy_indexes = self.view.table_view.selectionModel().selectedRows()
        if not selected_proxy_indexes:
            QMessageBox.warning(self.view, "Nenhuma Seleção", "Por favor, selecione uma ou mais atas para excluir.")
            return

        reply = QMessageBox.question(self.view, "Confirmação",
                                     f"Tem certeza que deseja excluir {len(selected_proxy_indexes)} registro(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        source_model = self.view.proxy_model.sourceModel()
        ids_to_delete = [source_model.item(self.view.proxy_model.mapToSource(idx).row(), 0).data(Qt.ItemDataRole.UserRole) for idx in selected_proxy_indexes]

        deleted_count = sum(1 for ata_id in ids_to_delete if self.model.delete_ata(ata_id))
        
        QMessageBox.information(self.view, "Concluído", f"{deleted_count} de {len(ids_to_delete)} registro(s) foram excluídos.")
        self.load_initial_data()

    def populate_table(self, atas: list):
        """Preenche a tabela da view com os dados das atas, incluindo a formatação gráfica."""
        model = self.view.table_model
        model.clear()
        
        headers = ["Dias", "Número", "Ano", "Empresa", "Ata", "Objeto"]
        model.setHorizontalHeaderLabels(headers)

        today = date.today()

        for ata in atas:
            dias_restantes = "N/A"
            if ata.termino:
                # Converte a string para objeto date antes de calcular
                termino_date = self._parse_date_string(ata.termino)
                if termino_date:
                    delta = termino_date - today
                    dias_restantes = delta.days
            
            # Usa a nova função para criar o item formatado
            dias_item = self._create_dias_item(dias_restantes)
            dias_item.setData(ata.id, Qt.ItemDataRole.UserRole)
            
            model.appendRow([
                dias_item,
                QStandardItem(str(ata.numero)),
                QStandardItem(str(ata.ano)),
                QStandardItem(str(ata.empresa)),
                QStandardItem(str(ata.contrato_ata_parecer)),
                QStandardItem(str(ata.objeto))
            ])
