# atas/controller/atas_controller.py
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QHeaderView, QMenu
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
        self.view.add_button.clicked.connect(self.show_add_ata_dialog)
        self.view.generate_table_button.clicked.connect(lambda: QMessageBox.information(self.view, "Info", "Funcionalidade 'Gerar Tabela' em desenvolvimento."))

        self.view.table_view.doubleClicked.connect(self.show_details_on_double_click)
        self.view.table_view.customContextMenuRequested.connect(self.show_context_menu)

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
            QMessageBox.warning(self.view, "Nenhuma Seleção", 
                              "Por favor, selecione uma ou mais atas para excluir.")
            return

        # Conta quantas atas serão excluídas
        total_selected = len(selected_proxy_indexes)
        
        # Confirmação
        reply = QMessageBox.question(self.view, "Confirmação",
                                   f"Tem certeza que deseja excluir {total_selected} ata(s) selecionada(s)?\n\n"
                                   "Esta ação não poderá ser desfeita.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Coleta os IDs das atas a serem excluídas
        source_model = self.view.proxy_model.sourceModel()
        ids_to_delete = []
        
        for proxy_index in selected_proxy_indexes:
            source_index = self.view.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
            # O ID está armazenado no UserRole do primeiro item da linha
            ata_id = source_model.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if ata_id:
                ids_to_delete.append(ata_id)

        # Exclui as atas do banco de dados
        deleted_count = 0
        failed_count = 0
        
        for ata_id in ids_to_delete:
            if self.model.delete_ata(ata_id):
                deleted_count += 1
            else:
                failed_count += 1
        
        # Mostra o resultado
        if failed_count == 0:
            QMessageBox.information(self.view, "Exclusão Concluída", 
                                  f"{deleted_count} ata(s) excluída(s) com sucesso!")
        else:
            QMessageBox.warning(self.view, "Exclusão Parcial", 
                              f"{deleted_count} ata(s) excluída(s) com sucesso.\n"
                              f"{failed_count} ata(s) não puderam ser excluídas.")
        
        # Recarrega a tabela para mostrar as mudanças
        self.load_initial_data()

    def show_add_ata_dialog(self):
        """Exibe a janela de adicionar nova ata."""
        from atas.view.add_ata_dialog import AddAtaDialog
        
        dialog = AddAtaDialog(self.view)
        dialog.ata_added.connect(self.add_new_ata)
        dialog.exec()

    def show_details_on_double_click(self, index):
        """Abre a janela de detalhes ao dar um duplo clique na linha."""
        source_index = self.view.proxy_model.mapToSource(index)
        row = source_index.row()

        source_model = self.view.proxy_model.sourceModel()
        # Coluna 4 contém o "contrato_ata_parecer"
        parecer_item = source_model.item(row, 4)
        if not parecer_item:
            return

        parecer_value = parecer_item.text()
        ata_data = self.model.get_ata_by_parecer(parecer_value)
        
        if ata_data:
            self.show_ata_details(ata_data)
        else:
            QMessageBox.warning(self.view, "Ata não encontrada",
                                f"Não foi possível encontrar os detalhes para a ata: {parecer_value}")

    def add_new_ata(self, ata_data):
        """Adiciona uma nova ata ao banco de dados."""
        try:
            success = self.model.add_ata(ata_data)
            if success:
                QMessageBox.information(self.view, "Sucesso", 
                                      f"Ata {ata_data['numero']}/{ata_data['ano']} adicionada com sucesso!")
                self.load_initial_data()  # Recarrega a tabela
            else:
                QMessageBox.critical(self.view, "Erro", "Não foi possível adicionar a ata.")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Erro ao adicionar ata:\n{e}")

    def _create_centered_item(self, text):
        """Cria um item centralizado para a tabela."""
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

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
                dias_item,  # Já formatado
                self._create_centered_item(ata.numero),
                self._create_centered_item(ata.ano),
                self._create_centered_item(ata.empresa),
                self._create_centered_item(ata.contrato_ata_parecer),
                self._create_centered_item(ata.objeto)
            ])
        
        # ADICIONE ESTAS LINHAS NO FINAL:
        # Configurar colunas APÓS popular os dados
        header = self.view.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # Dias - fixo
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Número - fixo  
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Ano - fixo
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Empresa - flexível
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Ata - fixo
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Objeto - flexível
        
        # Tamanhos das colunas fixas
        header.resizeSection(0, 80)   # Dias
        header.resizeSection(1, 75)  # Número
        header.resizeSection(2, 80)   # Ano  
        header.resizeSection(4, 170)  # Ata

    def show_context_menu(self, position):
        """Exibe o menu de contexto."""
        index = self.view.table_view.indexAt(position)
        if not index.isValid():
            return
            
        source_index = self.view.proxy_model.mapToSource(index)
        row = source_index.row()
        
        source_model = self.view.proxy_model.sourceModel()
        ata_id = source_model.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if not ata_id:
            return
            
        ata_data = self.model.get_ata_by_id(ata_id)
        if not ata_data:
            return
            
        menu = QMenu(self.view)
        
        ver_mais_action = menu.addAction(icon_manager.get_icon("init"), "Ver mais")
        ver_mais_action.triggered.connect(lambda: self.show_ata_details(ata_data))
        
        menu.addSeparator()
        
        excluir_action = menu.addAction(icon_manager.get_icon("delete"), "Excluir esta ata")
        excluir_action.triggered.connect(lambda: self.delete_single_ata(ata_id))
        
        menu.exec(self.view.table_view.mapToGlobal(position))

    def show_ata_details(self, ata_data):
        """Exibe a janela de detalhes da ata (similar ao sistema de contratos)."""
        details_text = (
            f"📋 DETALHES DA ATA\n\n"
            f"Número: {ata_data.numero}/{ata_data.ano}\n"
            f"Empresa: {ata_data.empresa}\n"
            f"Objeto: {ata_data.objeto}\n"
            f"Contrato/Ata/Parecer: {ata_data.contrato_ata_parecer}\n"
            f"Data de Término: {ata_data.termino or 'Não definida'}\n"
            f"Observações: {ata_data.observacoes or 'Nenhuma'}\n\n"
            f"💡 Em breve: Janela completa de edição como no sistema de contratos!"
        )
        
        msg = QMessageBox(self.view)
        msg.setWindowTitle("Detalhes da Ata")
        msg.setText(details_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setWindowIcon(icon_manager.get_icon("init"))
        msg.exec()

    def delete_single_ata(self, ata_id):
        """Exclui uma única ata após confirmação."""
        reply = QMessageBox.question(
            self.view, 
            "Confirmação de Exclusão",
            "⚠️ Tem certeza que deseja excluir esta ata?\n\n"
            "Esta ação não poderá ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.model.delete_ata(ata_id):
                QMessageBox.information(
                    self.view, 
                    "Sucesso", 
                    "✅ Ata excluída com sucesso!"
                )
                self.load_initial_data()  # Recarrega a tabela
            else:
                QMessageBox.critical(
                    self.view, 
                    "Erro", 
                    "❌ Não foi possível excluir a ata.\nVerifique os logs para mais detalhes."
                )
