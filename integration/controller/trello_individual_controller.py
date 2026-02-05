# integration/controller/trello_individual_controller.py
import json
from datetime import datetime
from pathlib import Path

class TrelloIndividualController:
    def __init__(self, trello_model):
        self.trello_model = trello_model
        self.config_path = Path("utils/json/trello_json.json")

    def _get_config(self):
        if not self.config_path.exists():
            return {"api_key": "", "token": "", "mappings": {}, "cards_sincronizados": {}}
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def sync_contract(self, contrato_data, status_atual):
        config = self._get_config()
        self.trello_model.api_key = config.get("api_key")
        self.trello_model.token = config.get("token")
        
        list_id = config.get("mappings", {}).get(status_atual)
        if not list_id:
            return False, f"ID da lista para '{status_atual}' não configurado."

        contrato_id_local = str(contrato_data.get('id'))
        historico_cards = config.get("cards_sincronizados", {})

        # Coleta de dados (Garantindo que apareçam CNPJ e Fornecedor)
        fornecedor = contrato_data.get('fornecedor_nome') or contrato_data.get('fornecedor', {}).get('nome', 'N/A')
        cnpj = contrato_data.get('fornecedor_cnpj') or contrato_data.get('fornecedor', {}).get('cnpj_cpf_idgener', 'N/A')
        obj_final = contrato_data.get('objeto_editado') or contrato_data.get('objeto', 'N/A')
        
        titulo = f"Contrato: {contrato_data.get('numero', 'S/N')}"
        description = (
            f"### 📋 Informações do Contrato\n"
            f"**🏢 Fornecedor:** {fornecedor}\n"
            f"**🆔 CNPJ:** {cnpj}\n\n"
            f"**🔹 Objeto:**\n> {obj_final}\n\n"
            f"**💰 Valor Global:** R$ {contrato_data.get('valor_global', '0,00')}\n"
            f"**📑 Processo:** {contrato_data.get('processo', 'N/A')}\n"
            f"--- \n*Sincronizado via CA 360 em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        # SE O CARD JÁ EXISTE NO TRELLO -> MOVE E ATUALIZA
        if contrato_id_local in historico_cards:
            card_id_trello = historico_cards[contrato_id_local]
            success, res = self.trello_model.update_card(card_id_trello, list_id, titulo, description)
            if success:
                return True, res
            # Se deu erro no update (ex: card foi excluído manualmente no Trello), tentamos criar um novo:
            else: pass 

        # SE NÃO EXISTE (OU FALHOU UPDATE) -> CRIA NOVO
        success, res = self.trello_model.create_card(list_id, titulo, description)

        if success:
            config.setdefault("cards_sincronizados", {})[contrato_id_local] = res.get('id')
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True, res
        
        return False, res
