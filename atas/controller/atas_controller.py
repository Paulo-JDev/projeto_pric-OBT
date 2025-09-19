# atas/controller/atas_controller.py
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QHeaderView, QMenu
from PyQt6.QtGui import QStandardItem, QBrush, QColor, QFont
from PyQt6.QtCore import Qt
from datetime import date, datetime
from atas.model.atas_model import AtasModel
from utils.icon_loader import icon_manager 
from atas.view.ata_details_dialog import AtaDetailsDialog
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

class AtasController:
    def __init__(self, model: AtasModel, view):
        self.model = model
        self.view = view
        self._connect_signals()
        self.load_initial_data()

    def _connect_signals(self):
        self.view.import_button.clicked.connect(self.import_data)
        self.view.delete_button.clicked.connect(self.delete_selected_ata)
        self.view.add_button.clicked.connect(self.show_add_ata_dialog)
        self.view.generate_table_button.clicked.connect(self.generate_excel_report)
        self.view.table_view.doubleClicked.connect(self.show_details_on_double_click)
        self.view.table_view.customContextMenuRequested.connect(self.show_context_menu)

    def _parse_date_string(self, date_string):
        if not date_string: return None
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    def _create_dias_item(self, dias_restantes):
        item = QStandardItem(str(dias_restantes))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        if isinstance(dias_restantes, int):
            if dias_restantes < 0: item.setForeground(Qt.GlobalColor.red); item.setIcon(icon_manager.get_icon("delete"))
            elif dias_restantes <= 89: item.setForeground(QBrush(QColor("#FFA500"))); item.setIcon(icon_manager.get_icon("alert"))
            elif dias_restantes <= 179: item.setForeground(QBrush(QColor("#FFD700"))); item.setIcon(icon_manager.get_icon("mensagem"))
            else: item.setForeground(QBrush(QColor("#32CD32"))); item.setIcon(icon_manager.get_icon("aproved"))
        else: item.setForeground(QBrush(QColor("#AAAAAA"))); item.setIcon(icon_manager.get_icon("time"))
        return item

    def load_initial_data(self):
        try:
            atas = self.model.get_all_atas()
            self.populate_table(atas)
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Não foi possível carregar os dados:\n{e}")

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Selecionar Planilha", "", "Planilhas Excel (*.xlsx)")
        if not file_path: return
        success, message = self.model.import_from_spreadsheet(file_path)
        if success:
            QMessageBox.information(self.view, "Importação Concluída", message)
            self.load_initial_data()
        else:
            QMessageBox.critical(self.view, "Erro na Importação", message)

    def delete_ata_by_parecer(self, parecer_value):
        reply = QMessageBox.question(self.view, "Confirmação", "Tem certeza que deseja excluir esta ata?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.model.delete_ata(parecer_value):
                QMessageBox.information(self.view, "Sucesso", "Ata excluída com sucesso!")
                self.load_initial_data()
            else:
                QMessageBox.critical(self.view, "Erro", "Não foi possível excluir a ata.")

    def delete_selected_ata(self):
        selected_indexes = self.view.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self.view, "Nenhuma Seleção", "Selecione uma ou mais atas para excluir.")
            return
        reply = QMessageBox.question(self.view, "Confirmação", f"Excluir {len(selected_indexes)} ata(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        
        source_model = self.view.proxy_model.sourceModel()
        pareceres_to_delete = [source_model.item(self.view.proxy_model.mapToSource(idx).row(), 4).text() for idx in selected_indexes]
        
        for parecer in pareceres_to_delete:
            self.model.delete_ata(parecer)
        self.load_initial_data()

    def show_add_ata_dialog(self):
        from atas.view.add_ata_dialog import AddAtaDialog
        dialog = AddAtaDialog(self.view)
        dialog.ata_added.connect(self.add_new_ata)
        dialog.exec()

    def add_new_ata(self, ata_data):
        if self.model.add_ata(ata_data):
            QMessageBox.information(self.view, "Sucesso", "Ata adicionada!")
            self.load_initial_data()
        else:
            QMessageBox.critical(self.view, "Erro", "Não foi possível adicionar a ata.")

    def _create_centered_item(self, text):
        item = QStandardItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        return item

    def populate_table(self, atas: list):
        model = self.view.table_model
        model.clear()
        headers = ["Dias", "Número", "Ano", "Empresa", "Ata", "Objeto"]
        model.setHorizontalHeaderLabels(headers)
        today = date.today()
        for ata in atas:
            dias_restantes = "N/A"
            if ata.termino:
                termino_date = self._parse_date_string(ata.termino)
                if termino_date:
                    dias_restantes = (termino_date - today).days
            model.appendRow([
                self._create_dias_item(dias_restantes), self._create_centered_item(ata.numero), 
                self._create_centered_item(ata.ano), self._create_centered_item(ata.empresa), 
                self._create_centered_item(ata.contrato_ata_parecer), self._create_centered_item(ata.objeto)
            ])
        # Configura as colunas
        header = self.view.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); header.resizeSection(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); header.resizeSection(1, 75)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); header.resizeSection(2, 80)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed); header.resizeSection(4, 170)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

    def show_details_on_double_click(self, index):
        source_index = self.view.proxy_model.mapToSource(index)
        row = source_index.row()
        source_model = self.view.proxy_model.sourceModel()
        parecer_item = source_model.item(row, 4)
        if not parecer_item: return
        
        ata_data = self.model.get_ata_by_parecer(parecer_item.text())
        if ata_data:
            self.show_ata_details(ata_data)

    def show_context_menu(self, position):
        index = self.view.table_view.indexAt(position)
        if not index.isValid(): return
        source_index = self.view.proxy_model.mapToSource(index)
        parecer = self.view.proxy_model.sourceModel().item(source_index.row(), 4).text()
        if not parecer: return
        
        menu = QMenu(self.view)
        ver_mais_action = menu.addAction(icon_manager.get_icon("init"), "Ver/Editar Detalhes")
        ver_mais_action.triggered.connect(lambda: self.show_details_on_double_click(index))
        menu.addSeparator()
        excluir_action = menu.addAction(icon_manager.get_icon("delete"), "Excluir esta ata")
        excluir_action.triggered.connect(lambda: self.delete_ata_by_parecer(parecer))
        menu.exec(self.view.table_view.mapToGlobal(position))

    def show_ata_details(self, ata_data):
        """Abre a janela de detalhes e conecta o sinal de atualização."""
        dialog = AtaDetailsDialog(ata_data, self.view)
        dialog.ata_updated.connect(lambda: self.update_ata_from_dialog(dialog))
        dialog.exec()

    def update_ata_from_dialog(self, dialog):
        """Pega os dados da janela, atualiza o modelo e a linha da tabela."""
        updated_data = dialog.get_updated_data()
        registros = [dialog.registro_list.item(i).text() for i in range(dialog.registro_list.count())]

        parecer_value = dialog.ata_data.contrato_ata_parecer

        if self.model.update_ata(parecer_value, updated_data, registros):
            # Recarrega os dados da ata no próprio diálogo para manter a consistência
            dialog.ata_data = self.model.get_ata_by_parecer(parecer_value)
            dialog.load_data() # Recarrega a UI do diálogo com os novos dados

            # Atualiza a linha específica na tabela principal
            self.update_table_row(parecer_value)
        else:
            QMessageBox.critical(self.view, "Erro", "Não foi possível atualizar a ata.")

    def update_table_row(self, parecer_value):
        """Atualiza uma única linha da tabela com base no parecer."""
        source_model = self.view.proxy_model.sourceModel()
        for row in range(source_model.rowCount()):
            item = source_model.item(row, 4) # Coluna "Ata" que contém o parecer
            if item and item.text() == parecer_value:
                ata_data = self.model.get_ata_by_parecer(parecer_value)
                if ata_data:
                    # Atualiza os dados da linha
                    dias_restantes = "N/A"
                    if ata_data.termino:
                        termino_date = self._parse_date_string(ata_data.termino)
                        if termino_date:
                            dias_restantes = (termino_date - date.today()).days

                    source_model.setItem(row, 0, self._create_dias_item(dias_restantes))
                    source_model.item(row, 1).setText(ata_data.numero)
                    source_model.item(row, 2).setText(ata_data.ano)
                    source_model.item(row, 3).setText(ata_data.empresa)
                    source_model.item(row, 5).setText(ata_data.objeto)
                    print(f"✅ Linha da ata {parecer_value} atualizada na tabela.")
                break

    def generate_excel_report(self):
        """Gera e salva uma planilha Excel com os dados das atas e hyperlinks."""
        atas = self.model.get_all_atas()
        if not atas:
            QMessageBox.warning(self.view, "Nenhum Dado", "Não há atas para gerar a tabela.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Salvar Planilha como...", "Relatorio_Atas_Administrativas.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Atas Administrativas"

            # --- ESTILOS ---
            title_font = Font(bold=True, size=16, color="FFFFFF")
            subtitle_font = Font(bold=True, size=12, color="FFFFFF")
            header_font = Font(bold=True, color="FFFFFF")
            link_font = Font(color="0066CC", underline="single")
            header_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
            center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

            # --- CABEÇALHO ---
            ws.merge_cells('A1:L3')
            ws['A1'].value = "ATAS ADMINISTRATIVAS"
            ws['A1'].font = title_font
            ws['A1'].alignment = center_align

            ws.merge_cells('A4:L4')
            ws['A4'].value = f"ACORDOS ADMINISTRATIVOS EM VIGOR {datetime.now().year}"
            ws['A4'].font = subtitle_font
            ws['A4'].alignment = center_align

            # --- CABEÇALHOS DA TABELA ---
            headers = ["SETOR", "MODALIDADE", "N°", "ANO", "EMPRESA", "ATA - PARECER", "OBJETO",
                    "CELEBRAÇÃO", "TERMO ADITIVO", "PORTARIA DE FISCALIZAÇÃO", "TÉRMINO", "DIAS P/ VENCIMENTO"]
            ws.append(headers)
            header_row = ws.max_row
            for cell in ws[header_row]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align

            # --- DADOS ---
            today = date.today()
            for ata in atas:
                dias_restantes = "N/A"
                if ata.termino:
                    termino_date = self._parse_date_string(ata.termino)
                    if termino_date:
                        dias_restantes = (termino_date - today).days

                # Prepara os valores, incluindo hyperlinks
                parecer_val = ata.contrato_ata_parecer or "N/A"
                if ata.links and ata.links.serie_ata_link:
                    parecer_val = f'=HYPERLINK("{ata.links.serie_ata_link}", "{parecer_val}")'

                termo_val = ata.termo_aditivo or "N/A"
                if ata.links and ata.links.ta_link:
                    termo_val = f'=HYPERLINK("{ata.links.ta_link}", "{termo_val}")'

                portaria_val = ata.portaria_fiscalizacao or "N/A"
                if ata.links and ata.links.portaria_link:
                    portaria_val = f'=HYPERLINK("{ata.links.portaria_link}", "{portaria_val}")'

                ws.append([
                    ata.setor, ata.modalidade, ata.numero, ata.ano, ata.empresa,
                    parecer_val, ata.objeto, ata.celebracao, termo_val,
                    portaria_val, ata.termino, dias_restantes
                ])
                # Aplica estilo de link
                current_row = ws.max_row
                if "=" in str(ws[f'F{current_row}'].value): ws[f'F{current_row}'].font = link_font
                if "=" in str(ws[f'I{current_row}'].value): ws[f'I{current_row}'].font = link_font
                if "=" in str(ws[f'J{current_row}'].value): ws[f'J{current_row}'].font = link_font

            # --- AJUSTE DE COLUNAS ---
            for i, column_cells in enumerate(ws.columns):
                length = max(len(str(cell.value or "")) for cell in column_cells)
                ws.column_dimensions[get_column_letter(i + 1)].width = length + 2

            workbook.save(file_path)
            QMessageBox.information(self.view, "Sucesso", f"Planilha salva com sucesso em:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Ocorreu um erro ao gerar a planilha:\n{str(e)}")
