# integration/controller/trello_individual_controller.py
import json
from datetime import datetime
from pathlib import Path

class TrelloIndividualController:
    def __init__(self, trello_model):
        self.trello_model = trello_model
        self.config_path = Path("utils/json/trello_json.json")
        self.comments_path = Path("utils/json/trello_comments.json")

    def _get_config(self):
        if not self.config_path.exists():
            return {"api_key": "", "token": "", "mappings": {}, "cards_sincronizados": {}}
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def _get_comment_history(self):
        if not self.comments_path.exists():
            return {} # Estrutura: {"id_contrato": [id_reg1, id_reg2]}
        with open(self.comments_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def sync_contract(self, contrato_data, status_atual, model_contratos):
        """
        Sincroniza individualmente: Move/Atualiza ou Cria novo.
        Envia registros como comentários individuais.
        """
        config = self._get_config()
        self.trello_model.api_key = config.get("api_key")
        self.trello_model.token = config.get("token")
        
        list_id = config.get("mappings", {}).get(status_atual)
        if not list_id:
            return False, f"Status '{status_atual}' não mapeado para uma lista no Trello."

        contrato_id_local = str(contrato_data.get('id'))
        historico_cards = config.get("cards_sincronizados", {})
        comment_history = self._get_comment_history()

        # --- COLETA DE DADOS ROBUSTA (Garantindo CNPJ e Fornecedor) ---
        fornecedor = contrato_data.get('fornecedor_nome') or contrato_data.get('fornecedor', {}).get('nome', 'N/A')
        cnpj = contrato_data.get('fornecedor_cnpj') or contrato_data.get('fornecedor', {}).get('cnpj_cpf_idgener', 'N/A')
        obj_final = contrato_data.get('objeto_editado') or contrato_data.get('objeto', 'N/A')
        
        titulo = f"Contrato: {contrato_data.get('numero', 'S/N')}"
        description = (
            f"### 📋 Dados do Contrato\n"
            f"**🏢 Fornecedor:** {fornecedor}\n"
            f"**🆔 CNPJ:** {cnpj}\n\n"
            f"**🔹 Objeto:**\n> {obj_final}\n\n"
            f"**💰 Valor Global:** R$ {contrato_data.get('valor_global', '0,00')}\n"
            f"**📑 Processo:** {contrato_data.get('processo', 'N/A')}\n"
            f"--- \n*Sincronizado via CA 360 em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        card_id_trello = None
        res_final = None

        # --- LÓGICA: ATUALIZAR/MOVER OU CRIAR NOVO ---
        if contrato_id_local in historico_cards:
            card_id_trello = historico_cards[contrato_id_local]
            success_up, res_up = self.trello_model.update_card(card_id_trello, list_id, titulo, description)
            if success_up:
                res_final = res_up
            else:
                card_id_trello = None # Força criação de um novo se o antigo foi deletado no Trello

        if not card_id_trello:
            success_new, res_new = self.trello_model.create_card(list_id, titulo, description)
            if success_new:
                card_id_trello = res_new.get('id')
                res_final = res_new
                config.setdefault("cards_sincronizados", {})[contrato_id_local] = card_id_trello
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            else:
                return False, res_new

        # --- ADIÇÃO DOS REGISTROS COMO COMENTÁRIOS ---
        # Busca os registros direto do banco de dados
        registros_db = self.get_contract_records_with_ids(model_contratos, contrato_id_local)
        
        if registros_db:
            # Pega lista de IDs já enviados para este contrato
            enviados = comment_history.get(contrato_id_local, [])
            novos_enviados = False

            for reg in registros_db:
                reg_id = str(reg['id'])
                if reg_id not in enviados:
                    # Se o ID do registro não está no JSON, envia para o Trello
                    texto_comentario = f"📌 **Registro Local (ID: {reg_id}):**\n{reg['texto']}"
                    if self.trello_model.add_comment(card_id_trello, texto_comentario):
                        enviados.append(reg_id)
                        novos_enviados = True

            # Se houve novos comentários, atualiza o arquivo trello_comments.json
            if novos_enviados:
                comment_history[contrato_id_local] = enviados
                with open(self.comments_path, 'w', encoding='utf-8') as f:
                    json.dump(comment_history, f, indent=4, ensure_ascii=False)

        return True, res_final

    def get_contract_records_with_ids(self, model, contrato_id):
        """Busca registros trazendo ID e Texto para controle de duplicidade."""
        from Contratos.model.models import RegistroStatus
        db = model._get_db_session()
        try:
            registros = db.query(RegistroStatus).filter(RegistroStatus.contrato_id == contrato_id).all()
            return [{'id': r.id, 'texto': r.texto} for r in registros]
        finally:
            db.close()
