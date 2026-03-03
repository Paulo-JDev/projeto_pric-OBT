# integration/controller/trello_controller.py
import json
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

from utils.utils import get_config_path

class TrelloController:
    def __init__(self, view, model, contratos_controller):
        self.view = view
        self.model = model
        self.trello_json_path = Path(get_config_path("utils/json/trello_json.json"))
        
        self.view.btn_save_creds.clicked.connect(self.save_config)
        self.load_config()

    def save_config(self):
        """Salva credenciais e mapeamentos sem apagar dados de sincronização."""
        # 1. Carrega dados existentes para preservar o que não está na tela (ex: cards_sincronizados)
        data = {}
        if self.trello_json_path.exists():
            try:
                with open(self.trello_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except: pass

        # 2. Atualiza apenas o que veio da interface
        data["api_key"] = self.view.api_key_input.text().strip()
        data["token"] = self.view.token_input.text().strip()
        
        # Mapeamentos separados
        data["mappings_contratos"] = {s: field.text().strip() for s, field in self.view.mapping_inputs_contratos.items()}
        data["mappings_atas"] = {s: field.text().strip() for s, field in self.view.mapping_inputs_atas.items()}
        
        try:
            with open(self.trello_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self.view, "Sucesso", "Configurações salvas com sucesso!")
        except Exception as e:
            QMessageBox.critical(self.view, "Erro", f"Falha ao salvar: {e}")

    def load_config(self):
        if not self.trello_json_path.exists():
            return
            
        try:
            with open(self.trello_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.view.api_key_input.setText(data.get("api_key", ""))
            self.view.token_input.setText(data.get("token", ""))
            
            mappings = data.get("mappings", {})
            for status, field in self.view.mapping_inputs.items():
                field.setText(mappings.get(status, ""))
        except Exception as e:
            print(f"Erro ao carregar trello_json: {e}")
