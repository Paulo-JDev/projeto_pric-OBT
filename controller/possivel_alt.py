


#dias_restantes = (vigencia_fim - today).days if isinstance(vigencia_fim, datetime.date) else "Erro Data"
# correçã para usar esse codigo de cima

''' def populate_table(self, data):
    """Preenche a tabela com os dados fornecidos."""
    self.view.table.setRowCount(len(data))
    self.view.table.setColumnCount(6)  # Agora temos 6 colunas, incluindo "Dias"
    self.view.table.setHorizontalHeaderLabels(["Dias", "Sigla OM", "Contrato/Ata", "Processo", "Fornecedor", "N° de Serie"])

    today = date.today()  # Correção: usar date.today() ao invés de datetime.today().date()

    for row_index, contrato in enumerate(data):
        # Calcular dias restantes
        vigencia_fim_str = contrato.get("vigencia_fim", "")
        if vigencia_fim_str:
            try:
                vigencia_fim = datetime.strptime(vigencia_fim_str, "%Y-%m-%d").date()
                dias_restantes = (vigencia_fim - today).days
            except ValueError:
                dias_restantes = "Erro Data"  # Se a data for inválida
        else:
            dias_restantes = "Sem Data"  # Se não houver data de vencimento

        dias_item = QTableWidgetItem(str(dias_restantes))
        dias_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Definir cor do texto se o contrato já venceu
        if isinstance(dias_restantes, int) and dias_restantes < 0:
            dias_item.setForeground(Qt.GlobalColor.red)

        self.view.table.setItem(row_index, 0, dias_item)

        # Preenchendo outras colunas
        self.view.table.setItem(row_index, 1, QTableWidgetItem(
            contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
        ))
        self.view.table.setItem(row_index, 2, QTableWidgetItem(str(contrato.get("numero", ""))))
        self.view.table.setItem(row_index, 3, QTableWidgetItem(str(contrato.get("processo", ""))))
        self.view.table.setItem(row_index, 4, QTableWidgetItem(
            contrato.get("fornecedor", {}).get("nome", "")
        ))
        self.view.table.setItem(row_index, 5, QTableWidgetItem(str(contrato.get("licitacao_numero", ""))))
'''
