# integration/controller/trello_individual_controller.py
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

class TrelloIndividualController:
    def __init__(self, trello_model):
        self.trello_model = trello_model
        self.config_path = Path("utils/json/trello_json.json")

    def sync_contract(self, contrato_data, status_atual):
        """Disparado pelo botão CA-Trello nos detalhes do contrato."""
        
        # 1. Carrega Configurações
        if not self.config_path.exists():
            return False, "Configurações não encontradas."
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        list_id = config.get("mappings", {}).get(status_atual)
        if not list_id:
            return False, f"Nenhuma lista mapeada para o status: {status_atual}"

        # 2. Prepara Dados (Prioriza objeto editado)
        obj_final = contrato_data.get('objeto_editado') or contrato_data.get('objeto') or 'N/A'
        
        description = (
            f"### 📋 Detalhes do Registro\n"
            f"**Fornecedor:** {contrato_data.get('fornecedor_nome', 'N/A')}\n"
            f"**CNPJ:** {contrato_data.get('fornecedor_cnpj', 'N/A')}\n\n"
            f"**🔹 Objeto:**\n>{obj_final}\n\n"
            f"**💰 Valor Global:** R$ {contrato_data.get('valor_global', '0,00')}\n"
            f"**📑 Processo:** {contrato_data.get('processo', 'N/A')}\n"
            f"--- \n*Sincronizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        # 3. Envio API
        self.trello_model.api_key = config.get("api_key")
        self.trello_model.token = config.get("token")
        
        return self.trello_model.create_card(list_id, f"Contrato: {contrato_data.get('numero')}", description)
