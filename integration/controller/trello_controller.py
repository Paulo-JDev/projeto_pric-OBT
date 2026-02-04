# integration/controller/trello_controller.py

import json
import os
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem


class TrelloController:
    def __init__(self, view, model, contratos_controller):
        self.view = view
        self.model = model
        self.contratos_controller = contratos_controller
        self.trello_json_path = Path("utils/json/trello_json.json")
        
        self.view.btn_save_creds.clicked.connect(self.save_creds_to_file)
        self.view.btn_sync_trello.clicked.connect(self.sync_selected_contracts)
        
        self.load_creds_from_file()
        self.refresh_contract_list()

    def save_creds_to_file(self):
        data = self.get_full_trello_data()
        data["api_key"] = self.view.api_key_input.text()
        data["token"] = self.view.token_input.text()
        data["list_id"] = self.view.list_id_input.text()
        
        with open(self.trello_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        self.view.log("✅ Configurações salvas em trello_json.json")

    def get_full_trello_data(self):
        if self.trello_json_path.exists():
            with open(self.trello_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"api_key": "", "token": "", "list_id": "", "sincronizados": []}

    def load_creds_from_file(self):
        data = self.get_full_trello_data()
        self.view.api_key_input.setText(data.get("api_key", ""))
        self.view.token_input.setText(data.get("token", ""))
        self.view.list_id_input.setText(data.get("list_id", ""))

    def refresh_contract_list(self):
        self.view.contract_list.clear()
        data = self.contratos_controller.model.get_contracts_with_status_not_default()
        trello_data = self.get_full_trello_data()
        ids_ja_no_trello = trello_data.get("sincronizados", [])

        self.contracts_map = {}
        for c in data:
            c_id = str(c.get('id'))
            # Só mostra se não estiver no histórico de sincronizados
            if c_id not in ids_ja_no_trello:
                display_text = f"{c.get('numero')} - {c.get('fornecedor_nome')}"
                item = QListWidgetItem(display_text)
                # Adiciona checkbox para seleção múltipla
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.view.contract_list.addItem(item)
                self.contracts_map[display_text] = c

    def sync_selected_contracts(self):
        items = [self.view.contract_list.item(i) for i in range(self.view.contract_list.count())]
        selected_items = [i for i in items if i.checkState() == Qt.CheckState.Checked]

        if not selected_items:
            self.view.log("⚠️ Marque ao menos um contrato na lista.")
            return

        trello_data = self.get_full_trello_data()
        self.model.api_key = trello_data["api_key"]
        self.model.token = trello_data["token"]

        for item in selected_items:
            contrato_base = self.contracts_map[item.text()]
            # Busca dados completos do banco (para pegar objeto_editado se houver)
            status_data = self.contratos_controller.model.get_all_status_data()
            
            # Tenta achar o objeto editado no log de status
            obj_final = contrato_base.get('objeto', 'N/A')
            for s in status_data:
                if str(s['contrato_id']) == str(contrato_base['id']):
                    if s.get('objeto_editado'):
                        obj_final = s['objeto_editado']
                    break

            titulo = f"Contrato: {contrato_base.get('numero')}"
            descricao = (
                f"**Fornecedor:** {contrato_base.get('fornecedor_nome')}\n"
                f"**CNPJ:** {contrato_base.get('fornecedor_cnpj', 'N/A')}\n"
                f"**Objeto:** {obj_final}\n"
                f"**Valor:** R$ {contrato_base.get('valor_global', '0,00')}\n"
                f"**Processo:** {contrato_base.get('processo', 'N/A')}"
            )

            success, response = self.model.create_card(trello_data["list_id"], titulo, descricao)
            
            if success:
                self.view.log(f"✅ Sincronizado: {contrato_base.get('numero')}")
                # Adiciona ao histórico para sumir da lista no refresh
                trello_data["sincronizados"].append(str(contrato_base['id']))
            else:
                self.view.log(f"❌ Erro no contrato {contrato_base.get('numero')}")

        # Salva o novo histórico e atualiza a lista
        with open(self.trello_json_path, 'w', encoding='utf-8') as f:
            json.dump(trello_data, f, indent=4)
        
        self.refresh_contract_list()
