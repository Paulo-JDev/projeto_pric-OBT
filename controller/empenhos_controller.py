# controller/empenhos_controller.py

from PyQt6.QtWidgets import QMessageBox, QFileDialog
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime
import re

class EmpenhoController:
    def __init__(self, model, parent_view=None):
        self.model = model
        self.parent_view = parent_view

    @staticmethod
    def _to_float(value_str):
        if not isinstance(value_str, str):
            return 0.0
        return float(value_str.replace('.', '').replace(',', '.'))

    def generate_report_to_excel(self, contract_data):
        """
        Orquestra a busca de dados, o processamento e a criação do relatório Excel
        com uma aba de resumo e abas detalhadas para cada período.
        """
        contrato_id = contract_data.get("id")

        # 1. Busca os dados necessários
        empenhos, error_empenhos = self.model.get_sub_data_for_contract(contrato_id, "empenhos")
        historico, error_historico = self.model.get_sub_data_for_contract(contrato_id, "historico")

        if error_empenhos or error_historico or not historico:
            QMessageBox.critical(self.parent_view, "Erro de Dados", "Não foi possível buscar o histórico ou os empenhos para gerar o relatório.")
            return

        # 2. Processa os dados para agrupar empenhos por período
        report_data = self._process_data_for_excel(historico, empenhos)

        # 3. Pede ao usuário onde salvar o arquivo
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_view,
            "Salvar Relatório de Empenhos",
            f"Relatorio_Empenhos_Contrato_{contract_data.get('numero', '').replace('/', '-')}.xlsx",
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        # 4. Cria o arquivo Excel
        try:
            self._create_excel_file(file_path, report_data)
            QMessageBox.information(self.parent_view, "Sucesso", f"Relatório salvo com sucesso em:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self.parent_view, "Erro ao Gerar Excel", f"Ocorreu um erro ao criar a planilha:\n{str(e)}")

    def _process_data_for_excel(self, historico, empenhos):
        """Prepara os dados para o relatório, incluindo a lógica de verificação."""
        periodos = []
        for item in sorted(historico, key=lambda x: x['vigencia_inicio']):
            if item.get("codigo_tipo") in ["50", "55"]:
                periodos.append({
                    "titulo": f"{item['tipo']} {item['numero']}",
                    "inicio": datetime.strptime(item['vigencia_inicio'], "%Y-%m-%d").date(),
                    "fim": datetime.strptime(item['vigencia_fim'], "%Y-%m-%d").date(),
                    "valor_global": self._to_float(item.get('valor_global', '0,00')), # <<< CORRIGIDO
                    "empenhos_do_periodo": []
                })

        for empenho in empenhos:
            try:
                data_emissao = datetime.strptime(empenho['data_emissao'], "%Y-%m-%d").date()
                for periodo in periodos:
                    if periodo['inicio'] <= data_emissao <= periodo['fim']:
                        periodo['empenhos_do_periodo'].append(empenho)
                        break
            except (ValueError, TypeError):
                continue

        report = []
        for periodo in periodos:
            total_empenhado = sum(self._to_float(e.get('empenhado', '0,00')) for e in periodo['empenhos_do_periodo']) # <<< CORRIGIDO
            total_pago = sum(self._to_float(e.get('pago', '0,00')) for e in periodo['empenhos_do_periodo']) # <<< CORRIGIDO

            obs = "OK"
            if total_empenhado > periodo['valor_global'] or total_pago > periodo['valor_global']:
                obs = "Sera??"

            report.append({
                "titulo": periodo['titulo'],
                "inicio": periodo['inicio'].strftime("%d/%m/%Y"),
                "fim": periodo['fim'].strftime("%d/%m/%Y"),
                "valor_global": periodo['valor_global'],
                "total_empenhado": total_empenhado,
                "total_pago": total_pago,
                "obs": obs,
                "empenhos_detalhados": periodo['empenhos_do_periodo']
            })
        
        return report

    def _create_excel_file(self, file_path, report_data):
        """Cria e formata o arquivo .xlsx com a aba de resumo e as abas detalhadas."""
        workbook = Workbook()
        
        # --- 1. CRIAÇÃO DA ABA DE RESUMO ---
        ws_resumo = workbook.active
        ws_resumo.title = "Resumo Geral"
        
        # Estilos
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        center_align = Alignment(horizontal='center', vertical='center')
        
        headers_resumo = ["Período", "Vigência", "Valor Global", "Total Empenhado", "Total Pago", "OBS"]
        ws_resumo.append(headers_resumo)
        for cell in ws_resumo[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        for row_data in report_data:
            ws_resumo.append([
                row_data['titulo'], f"{row_data['inicio']} a {row_data['fim']}",
                row_data['valor_global'], row_data['total_empenhado'],
                row_data['total_pago'], row_data['obs']
            ])

        for row in ws_resumo.iter_rows(min_row=2, max_row=ws_resumo.max_row):
            row[0].alignment, row[1].alignment, row[5].alignment = center_align, center_align, center_align
            row[2].number_format = '"R$" #,##0.00'
            row[3].number_format = '"R$" #,##0.00'
            row[4].number_format = '"R$" #,##0.00'
            if row[5].value == "Sera??":
                row[5].font = Font(bold=True, color="FF0000")

        for i, column_letter in enumerate(get_column_letter(c+1) for c in range(ws_resumo.max_column)):
            ws_resumo.column_dimensions[column_letter].auto_size = True

        # --- 2. CRIAÇÃO DAS ABAS DETALHADAS PARA CADA PERÍODO ---
        for periodo_data in report_data:
            sheet_title = re.sub(r'[\\/*?:\[\]]', '', periodo_data['titulo'])[:31]
            ws_detalhe = workbook.create_sheet(title=sheet_title)

            # --- LÓGICA ADICIONADA PARA A SEÇÃO "BASE" ---
            # Estilos para a nova seção
            base_header_font = Font(bold=True, color="FFFFFF")
            base_header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
            base_label_font = Font(bold=True)
            
            # Título da Seção
            ws_detalhe.merge_cells('A1:C1')
            base_title_cell = ws_detalhe['A1']
            base_title_cell.value = "INFORMAÇÕES DE BASE DO PERÍODO"
            base_title_cell.font = base_header_font
            base_title_cell.fill = base_header_fill
            base_title_cell.alignment = Alignment(horizontal='center')

            # Campo Período de Vigência
            ws_detalhe['A2'] = "Período de Vigência:"
            ws_detalhe['A2'].font = base_label_font
            ws_detalhe['B2'] = f"{periodo_data['inicio']} a {periodo_data['fim']}"
            
            # Campo Valor Global
            ws_detalhe['A3'] = "Valor Global do Período:"
            ws_detalhe['A3'].font = base_label_font
            ws_detalhe['B3'] = periodo_data['valor_global']
            ws_detalhe['B3'].number_format = '"R$" #,##0.00'
            # --- FIM DA LÓGICA DA SEÇÃO "BASE" ---


            # Cabeçalhos da tabela de empenhos (agora começam na linha 5)
            headers_detalhe = [
                "Número Empenho", "Data Emissão", "Credor", "Natureza da Despesa",
                "Valor Empenhado", "Valor a Liquidar", "Valor Pago", "Documento de Pagamento"
            ]
            ws_detalhe.append(headers_detalhe) # Isso vai adicionar na próxima linha vazia (linha 5)
            
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            center_align = Alignment(horizontal='center', vertical='center')

            for cell in ws_detalhe[5]: # Aplica estilo na linha 5
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align

            for empenho in periodo_data['empenhos_detalhados']:
                doc_pagamento_url = empenho.get("links", {}).get("documento_pagamento")
                numero_empenho = empenho.get('numero', 'N/A')
                
                row_to_append = [
                    numero_empenho,
                    datetime.strptime(empenho.get('data_emissao'), "%Y-%m-%d").date() if empenho.get('data_emissao') else "N/A",
                    empenho.get('credor', 'N/A'),
                    empenho.get('naturezadespesa', 'N/A'),
                    self._to_float(empenho.get('empenhado', '0,00')), # <<< CORRIGIDO
                    self._to_float(empenho.get('aliquidar', '0,00')), # <<< CORRIGIDO
                    self._to_float(empenho.get('pago', '0,00')),      # <<< CORRIGIDO
                    f'=HYPERLINK("{doc_pagamento_url}", "{numero_empenho}_linkdoc")' if doc_pagamento_url else "Sem link"
                ]
                ws_detalhe.append(row_to_append)

            # Formata as células da aba de detalhe
            for row in ws_detalhe.iter_rows(min_row=6, max_row=ws_detalhe.max_row):
                row[0].alignment = center_align
                row[1].alignment = center_align
                row[1].number_format = 'DD/MM/YYYY'
                row[4].number_format = '"R$" #,##0.00'
                row[5].number_format = '"R$" #,##0.00'
                row[6].number_format = '"R$" #,##0.00'
                if row[7].value != "Sem link":
                    row[7].font = Font(color="0563C1", underline="single")
                    row[7].alignment = center_align

            for i, column_letter in enumerate(get_column_letter(c+1) for c in range(ws_detalhe.max_column)):
                ws_detalhe.column_dimensions[column_letter].auto_size = True
        
        workbook.save(file_path)
