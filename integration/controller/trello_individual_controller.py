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
        """
        Sincroniza o contrato individualmente.
        Se já existir um card para este contrato, ele é removido antes de criar o novo na lista correta.
        """
        config = self._get_config()
        self.trello_model.api_key = config.get("api_key")
        self.trello_model.token = config.get("token")
        
        list_id = config.get("mappings", {}).get(status_atual)
        if not list_id:
            return False, f"Status '{status_atual}' não mapeado para uma lista no Trello."

        contrato_id_local = str(contrato_data.get('id'))
        
        # --- LÓGICA DE MOVIMENTAÇÃO (Excluir antigo se existir) ---
        historico_cards = config.get("cards_sincronizados", {})
        if contrato_id_local in historico_cards:
            old_card_id = historico_cards[contrato_id_local]
            # Tenta deletar o card antigo para não duplicar em listas diferentes
            self.trello_model.delete_card(old_card_id)

        # --- DADOS DO CONTRATO ---
        fornecedor = contrato_data.get('fornecedor_nome') or contrato_data.get('fornecedor', {}).get('nome', 'N/A')
        cnpj = contrato_data.get('fornecedor_cnpj') or contrato_data.get('fornecedor', {}).get('cnpj_cpf_idgener', 'N/A')
        
        # Prioriza objeto editado se disponível
        obj_final = contrato_data.get('objeto_editado') or contrato_data.get('objeto', 'N/A')
        
        # Valor e Processo
        valor = contrato_data.get('valor_global', '0,00')
        processo = contrato_data.get('processo', 'N/A')

        # --- FORMATAÇÃO MARKDOWN ---
        description = (
            f"### 📋 Informações do Contrato\n"
            f"**🏢 Fornecedor:** {fornecedor}\n"
            f"**🆔 CNPJ:** {cnpj}\n\n"
            f"**🔹 Objeto:**\n> {obj_final}\n\n"
            f"**💰 Valor Global:** R$ {valor}\n"
            f"**📑 Processo:** {processo}\n"
            f"--- \n*Atualizado via CA 360 em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        titulo = f"Contrato: {contrato_data.get('numero', 'S/N')}"
        
        # --- ENVIO ---
        success, res = self.trello_model.create_card(list_id, titulo, description)

        if success:
            # Salva o novo card_id no histórico para futuras movimentações
            config.setdefault("cards_sincronizados", {})[contrato_id_local] = res.get('id')
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True, res
        
        return False, res
