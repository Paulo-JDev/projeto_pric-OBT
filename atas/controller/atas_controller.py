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
from openpyxl.drawing.image import Image
import os

class AtasController:
    def __init__(self, model: AtasModel, view):
        self.model = model
        self.view = view
        self._connect_signals()
        self.load_initial_data()

    def _connect_signals(self):
        self.view.delete_button.clicked.connect(self.delete_selected_ata)
        self.view.add_button.clicked.connect(self.show_add_ata_dialog)
        
        # --- SIGNALS DO MENU "DADOS" ---
        self.view.import_action.triggered.connect(self.import_data)
        self.view.export_completo_action.triggered.connect(self.generate_excel_report)
        self.view.template_vazio_action.triggered.connect(self.generate_empty_template)
        self.view.export_para_importacao_action.triggered.connect(self.export_for_reimport)

        self.view.table_view.doubleClicked.connect(self.show_details_on_double_click)
        self.view.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.view.preview_table.doubleClicked.connect(self.show_details_on_preview_double_click)
        self.view.refresh_preview_button.clicked.connect(self.populate_previsualization_table)
        self.view.refresh_table_button.clicked.connect(self.load_initial_data)

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
        """Carrega os dados e popula ambas as tabelas na inicialização."""
        try:
            atas = self.model.get_all_atas()
            self.populate_table(atas)
            self.populate_previsualization_table()
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Não foi possível carregar os dados:\n{e}")

    def _get_status_style(self, status_text):
        """Retorna a cor e a fonte para um determinado status."""
        status_styles = {
            "SEÇÃO ATAS": (QColor("#FFFFFF"), QFont.Weight.Bold),
            "ATA GERADA": (QColor(230, 230, 150), QFont.Weight.Bold),
            "EMPRESA": (QColor(230, 230, 150), QFont.Weight.Bold),
            "SIGDEM": (QColor(230, 180, 100), QFont.Weight.Bold),
            "ASSINADO": (QColor(230, 180, 100), QFont.Weight.Bold),
            "PUBLICADO": (QColor(135, 206, 250), QFont.Weight.Bold),
            "PORTARIA": (QColor(230, 230, 150), QFont.Weight.Bold),
            "ALERTA PRAZO": (QColor(255, 160, 160), QFont.Weight.Bold),
            "NOTA TÉCNICA": (QColor(255, 160, 160), QFont.Weight.Bold),
            "AGU": (QColor(255, 160, 160), QFont.Weight.Bold),
            "PRORROGADO": (QColor(135, 206, 250), QFont.Weight.Bold)
        }
        color, weight = status_styles.get(status_text, (QColor("#FFFFFF"), QFont.Weight.Normal))
        return QBrush(color), weight

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
        headers = ["Dias", "Número", "Ano", "Empresa", "Ata", "Objeto", "Status"]
        model.setHorizontalHeaderLabels(headers)
        today = date.today()
        for ata in atas:
            dias_restantes = "N/A"
            if ata.termino:
                termino_date = self._parse_date_string(ata.termino)
                if termino_date:
                    dias_restantes = (termino_date - today).days

            status_text = ata.status_info.status if ata.status_info else "SEÇÃO ATAS"
            status_item = self._create_centered_item(status_text)
            brush, weight = self._get_status_style(status_text)
            status_item.setForeground(brush)
            font = status_item.font()
            font.setWeight(weight)
            status_item.setFont(font)

            model.appendRow([
                self._create_dias_item(dias_restantes), self._create_centered_item(ata.numero), 
                self._create_centered_item(ata.ano), self._create_centered_item(ata.empresa), 
                self._create_centered_item(ata.contrato_ata_parecer), self._create_centered_item(ata.objeto),
                status_item
            ])
        # Configura as colunas
        header = self.view.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); header.resizeSection(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); header.resizeSection(1, 75)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed); header.resizeSection(2, 80)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed); header.resizeSection(4, 170)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(6, 180)

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
            self.populate_previsualization_table()
            #self.populate_table(atas=self.model.get_all_atas())
        else:
            QMessageBox.critical(self.view, "Erro", "Não foi possível atualizar a ata.")

    def update_table_row(self, parecer_value):
        """Atualiza uma única linha da tabela com base no parecer."""
        source_model = self.view.proxy_model.sourceModel()
        for row in range(source_model.rowCount()):
            item_parecer = source_model.item(row, 4) # Coluna "Ata"
            if item_parecer and item_parecer.text() == parecer_value:
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
                    source_model.item(row, 2).setText(str(ata_data.ano))
                    source_model.item(row, 3).setText(ata_data.empresa)
                    source_model.item(row, 5).setText(ata_data.objeto)

                    # --- LÓGICA DE ATUALIZAÇÃO DO STATUS CORRIGIDA ---
                    status_item = source_model.item(row, 6)
                    status_item.setText(ata_data.status)
                    brush, weight = self._get_status_style(ata_data.status)
                    status_item.setForeground(brush)
                    font = status_item.font()
                    font.setWeight(weight)
                    status_item.setFont(font)
                    # --- FIM DA CORREÇÃO ---

                    print(f"✅ Linha da ata {parecer_value} atualizada na tabela.")
                break

    def generate_excel_report(self):
        """
        Gera e salva uma planilha Excel com os dados das atas, usando formatação avançada
        e hyperlinks dinâmicos.
        """
        atas = self.model.get_all_atas()
        if not atas:
            QMessageBox.warning(self.view, "Nenhum Dado", "Não há atas para gerar a tabela.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Salvar Planilha como...", "Relatorio_Atas_Administrativas.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # --- PREPARAÇÃO DA PLANILHA ---
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Atas Administrativas"
            ano_atual = datetime.now().year
            data_atual_str = datetime.now().strftime("%d/%m/%Y")

            # --- ESTILOS ---
            title_font = Font(bold=True, size=14)
            subtitle_font = Font(bold=True, size=12)
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
            link_font = Font(color="0000FF", underline="single") # Cor azul padrão de link
            green_font = Font(color="00B050")

            # --- CABEÇALHO COM LOGOS ---
            try:
                path_icone = os.path.join('utils', 'icons', 'icone.ico')
                if os.path.exists(path_icone):
                    logo_esquerdo = Image(path_icone)
                    logo_esquerdo.height = 70; logo_esquerdo.width = 70
                    ws.add_image(logo_esquerdo, 'A1')
            except Exception as e:
                print(f"Aviso: Não foi possível carregar o ícone esquerdo: {e}")

            ws.merge_cells('B1:K3')
            ws['B1'].value = "CENTRO DE INTENDÊNCIA DA MARINHA EM BRASÍLIA\nDIVISÃO DE OBTENÇÃO"
            ws['B1'].font = title_font
            ws['B1'].alignment = center_align

            ws.merge_cells('A4:L4')
            ws['A4'].value = f"ACORDOS ADMINISTRATIVOS EM VIGOR {ano_atual}"
            ws['A4'].font = subtitle_font
            ws['A4'].alignment = center_align
            
            ws['L6'] = f"Data: {data_atual_str}"
            ws['L6'].font = Font(bold=True, italic=True)
            ws['L6'].alignment = Alignment(horizontal='center')

            # --- CABEÇALHOS DA TABELA ---
            headers = [
                "SETOR", "MODALIDADE", "N°", "ANO", "EMPRESA", "ATAS", "OBJETO",
                "CELEBRAÇÃO", "TERMO ADITIVO", "PORTARIA DE FISCALIZAÇÃO", "TÉRMINO", "DIAS P/ VENCIMENTO"
            ]
            ws.append(headers)
            header_row_num = ws.max_row
            for cell in ws[header_row_num]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align

            # --- DADOS E FÓRMULAS ---
            today = date.today()
            for row_idx, ata in enumerate(atas, start=header_row_num + 1):
                # Prepara os valores com hyperlinks
                parecer_val = ata.contrato_ata_parecer or "N/A"
                has_parecer_link = hasattr(ata, 'links') and ata.links and ata.links.serie_ata_link
                if has_parecer_link:
                    parecer_val = f'=HYPERLINK("{ata.links.serie_ata_link}", "{parecer_val}")'

                termo_val = ata.termo_aditivo or "N/A"
                has_ta_link = hasattr(ata, 'links') and ata.links and ata.links.ta_link
                if has_ta_link:
                    termo_val = f'=HYPERLINK("{ata.links.ta_link}", "{termo_val}")'
                
                portaria_val = ata.portaria_fiscalizacao or "N/A"
                has_portaria_link = hasattr(ata, 'links') and ata.links and ata.links.portaria_link
                if has_portaria_link:
                    portaria_val = f'=HYPERLINK("{ata.links.portaria_link}", "{portaria_val}")'

                # Prepara as datas
                data_celebracao_excel = self._parse_date_string(ata.celebracao)
                data_termino_excel = self._parse_date_string(ata.termino)
                
                row_data = [
                    ata.setor, ata.modalidade, ata.numero, ata.ano, ata.empresa,
                    parecer_val, ata.objeto, data_celebracao_excel, termo_val,
                    portaria_val, data_termino_excel,
                    f'=IF(ISBLANK(K{row_idx}), "N/A", K{row_idx}-TODAY())'
                ]
                ws.append(row_data)

                # --- Formatação da linha ---
                current_row = ws[row_idx]
                for cell in current_row:
                    cell.alignment = center_align

                if has_parecer_link: current_row[5].font = link_font
                if has_ta_link: current_row[8].font = link_font
                if has_portaria_link: current_row[9].font = link_font
                
                # Formato de data e dias
                current_row[7].number_format = 'DD/MM/YYYY'
                current_row[10].number_format = 'DD/MM/YYYY'
                current_row[11].font = green_font
                current_row[11].number_format = '0'

            # --- AJUSTE FINAL DAS LARGURAS DAS COLUNAS ---
            ws.column_dimensions['A'].width = 12; ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 10; ws.column_dimensions['D'].width = 10
            ws.column_dimensions['E'].width = 35; ws.column_dimensions['F'].width = 25
            ws.column_dimensions['G'].width = 45; ws.column_dimensions['H'].width = 15
            ws.column_dimensions['I'].width = 15; ws.column_dimensions['J'].width = 25
            ws.column_dimensions['K'].width = 15; ws.column_dimensions['L'].width = 18

            workbook.save(file_path)
            QMessageBox.information(self.view, "Sucesso", f"Planilha salva com sucesso em:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self.view, "Erro ao Gerar Planilha", f"Ocorreu um erro ao gerar a planilha:\n{str(e)}")

    def generate_empty_template(self):
        """Gera uma planilha Excel vazia com os cabeçalhos necessários para a importação."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Salvar Modelo de Planilha Vazia", "Modelo_Importacao_Atas.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Dados Atas"

            # Cabeçalhos exatos que o método de importação espera
            headers = [
                'SETOR', 'MODALIDADE', 'Nº/', 'ANO', 'EMPRESA', 
                'CONTRATO – ATA PARECER', 'OBJETO', 'CELEBRAÇÃO', 
                'TERMO ADITIVO', 'PORTARIA DE FISCALIZAÇÃO', 'TERMINO', 'OBSERVAÇÕES'
            ]
            ws.append(headers)

            # Estilo
            header_font = Font(bold=True)
            for cell in ws[1]:
                cell.font = header_font

            workbook.save(file_path)
            QMessageBox.information(self.view, "Sucesso", f"Modelo de planilha vazia salvo em:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Não foi possível gerar o modelo: {e}")

    def export_for_reimport(self):
        """Exporta todos os dados atuais para uma planilha no formato exato de importação."""
        atas = self.model.get_all_atas()
        if not atas:
            QMessageBox.warning(self.view, "Nenhum Dado", "Não há atas para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Exportar Dados para Re-importação", "Backup_Atas_Importacao.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            workbook = Workbook()
            ws = workbook.active
            ws.title = "Dados Atas"

            headers = [
                'SETOR', 'MODALIDADE', 'Nº/', 'ANO', 'EMPRESA', 
                'CONTRATO – ATA PARECER', 'OBJETO', 'CELEBRAÇÃO', 
                'TERMO ADITIVO', 'PORTARIA DE FISCALIZAÇÃO', 'TERMINO', 'OBSERVAÇÕES'
            ]
            ws.append(headers)

            for ata in atas:
                ws.append([
                    ata.setor, ata.modalidade, ata.numero, ata.ano, ata.empresa,
                    ata.contrato_ata_parecer, ata.objeto, ata.celebracao,
                    ata.termo_aditivo, ata.portaria_fiscalizacao, ata.termino,
                    ata.observacoes
                ])

            workbook.save(file_path)
            QMessageBox.information(self.view, "Sucesso", f"Dados exportados com sucesso para:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Ocorreu um erro ao exportar os dados: {e}")

# ================================================================ PRE-VISUALIZAÇÃO ==================================================
    def populate_previsualization_table(self):
        """Popula a tabela de pré-visualização com atas que não estão no status padrão."""
        model = self.view.preview_model
        model.clear()
        headers = ["Dias", "Ata", "Empresa", "Objeto", "Status"]
        model.setHorizontalHeaderLabels(headers)

        atas = self.model.get_atas_with_status_not_default()
        today = date.today()

        for ata in atas:
            dias_restantes = "N/A"
            if ata.termino:
                termino_date = self._parse_date_string(ata.termino)
                if termino_date:
                    dias_restantes = (termino_date - today).days

            dias_item = self._create_dias_item(dias_restantes)

            parecer_item = self._create_centered_item(ata.contrato_ata_parecer)
            # Guarda o parecer como identificador único
            parecer_item.setData(ata.contrato_ata_parecer, Qt.ItemDataRole.UserRole)

            status_text = ata.status_info.status if ata.status_info else "SEÇÃO ATAS"
            status_item = self._create_centered_item(status_text)
            brush, weight = self._get_status_style(status_text)
            status_item.setForeground(brush)
            font = status_item.font()
            font.setWeight(weight)
            status_item.setFont(font)

            model.appendRow([
                dias_item,
                parecer_item,
                self._create_centered_item(ata.empresa),
                self._create_centered_item(ata.objeto),
                status_item
            ])

        # Ajusta as colunas da tabela de pré-visualização
        header = self.view.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed); header.resizeSection(0, 80)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed); header.resizeSection(1, 170)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed); header.resizeSection(4, 180)

    def show_details_on_preview_double_click(self, index):
        """Abre os detalhes da ata a partir da tabela de pré-visualização."""
        proxy_model = self.view.preview_proxy_model
        source_index = proxy_model.mapToSource(index)
        row = source_index.row()

        # O parecer está na coluna 1 e guardado no UserRole
        parecer_item = proxy_model.sourceModel().item(row, 1)
        if not parecer_item: return

        parecer_value = parecer_item.data(Qt.ItemDataRole.UserRole)
        ata_data = self.model.get_ata_by_parecer(parecer_value)

        if ata_data:
            self.show_ata_details(ata_data)