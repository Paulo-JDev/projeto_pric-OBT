# integration/controller/trello_controller.py
import requests
from PyQt6.QtWidgets import QMessageBox

class TrelloController:
    def __init__(self, view, model, contratos_controller):
        self.view = view
        self.model = model
        self.contratos_controller = contratos_controller
        self.view.btn_sync_trello.clicked.connect(self.test_single_sync)

    # integration/controller/trello_controller.py

    def test_single_sync(self):
        """Teste de envio de um único contrato selecionado com formatação específica."""
        creds = self.view.get_credentials()
        
        if not all([creds["key"], creds["token"], creds["list_id"]]):
            QMessageBox.warning(self.view, "Erro de Configuração", "Preencha API Key, Token e ID da Lista.")
            return

        self.model.api_key = creds["key"]
        self.model.token = creds["token"]

        # 1. Pegar seleção da tabela principal
        selected_indexes = self.contratos_controller.view.table.selectionModel().selectedIndexes()
        
        if not selected_indexes:
            self.view.log("⚠️ Nenhum contrato selecionado na tabela. Selecione uma linha primeiro.")
            return

        # Mapeamento para o dado real (considerando filtros/ordenação)
        proxy_model = self.contratos_controller.view.table.model()
        source_index = proxy_model.mapToSource(selected_indexes[0])
        row = source_index.row()
        contrato = self.contratos_controller.get_current_data()[row]

        # 2. Formatação do Identificador (ex: 87010/25 - 71/00)
        # Extraímos a UASG e os anos (assumindo formato YYYY-MM-DD ou similar na vigência)
        uasg = contrato.get('uasg_code', '000000')
        numero_full = contrato.get('numero', '0/0') # Ex: "00071/2025"
        
        # Tenta extrair o ano do contrato para formatar a UASG (ex: 2025 -> 25)
        ano_contrato_curto = "00"
        if "/" in numero_full:
            partes_num = numero_full.split("/")
            num_so = partes_num[0].lstrip('0') # "00071" -> "71"
            ano_full = partes_num[1]
            ano_contrato_curto = ano_full[-2:]
        else:
            num_so = numero_full

        # Monta o título: UASG/ANO - NUMERO/SUB
        # Como o seu exemplo 87010/25-71/00, vamos aproximar:
        titulo_card = f"Contrato: {uasg}/{ano_contrato_curto} - {num_so}/00"
        
        self.view.log(f"Enviando para Trello: {titulo_card}...")

        # 3. Descrição detalhada
        descricao = (
            f"**Fornecedor:** {contrato.get('fornecedor_nome', 'N/A')}\n"
            f"**CNPJ:** {contrato.get('fornecedor_cnpj', 'N/A')}\n"
            f"**Objeto:** {contrato.get('objeto', 'N/A')}\n"
            f"**Valor:** R$ {contrato.get('valor_global', '0,00')}\n"
            f"**Processo:** {contrato.get('processo', 'N/A')}"
        )

        # 4. Envio
        success, response = self.model.create_card(creds["list_id"], titulo_card, descricao)

        if success:
            self.view.log(f"✅ SUCESSO! Card criado no Trello.")
            self.view.log(f"Link: {response.get('shortUrl')}")
        else:
            # Se der erro, vamos logar a resposta bruta para identificar o motivo
            self.view.log(f"❌ ERRO API: {response}")
