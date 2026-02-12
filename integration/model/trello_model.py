# integration/model/trello_model.py
import requests
import json
import os

class TrelloModel:
    def __init__(self, api_key=None, token=None):
        """
        Inicializa o modelo do Trello.

        Se api_key/token não forem fornecidos, carrega de utils/json/trello_json.json
        """
        self.base_url = "https://api.trello.com/1"

        # Se credenciais foram passadas, usa elas
        if api_key and token:
            self.api_key = api_key
            self.token = token
            self.config = {}
        else:
            # Caso contrário, carrega do arquivo JSON
            self._load_config()

    def _load_config(self):
        """Carrega configurações do arquivo trello_json.json"""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "..",
            "utils", 
            "json", 
            "trello_json.json"
        )

        if not os.path.exists(config_path):
            print(f"⚠️ Arquivo de configuração não encontrado: {config_path}")
            self.config = {}
            self.api_key = ""
            self.token = ""
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            # Extrai credenciais
            self.api_key = self.config.get("api_key", "")
            self.token = self.config.get("token", "")

            if not self.api_key or not self.token:
                print("⚠️ Credenciais do Trello não configuradas em trello_json.json")
            else:
                print("✅ Credenciais do Trello carregadas com sucesso")

        except Exception as e:
            print(f"❌ Erro ao carregar configuração do Trello: {e}")
            self.config = {}
            self.api_key = ""
            self.token = ""

    def get_list_id_for_status(self, status):
        """
        Retorna o ID da lista mapeada para o status.

        """
        return self.config.get("mappings", {}).get(status)

    def get_card_id_for_contract(self, contract_id):
        """
        Retorna o ID do card no Trello para um contrato específico.
        """
        return self.config.get("cards_sincronizados", {}).get(str(contract_id))

    def save_card_sync(self, contract_id, card_id):
        """
        Salva a relação contrato → card no arquivo JSON.
        """
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "..",
            "utils", 
            "json", 
            "trello_json.json"
        )

        try:
            # Garante que a chave existe
            if "cards_sincronizados" not in self.config:
                self.config["cards_sincronizados"] = {}

            # Adiciona/atualiza o mapeamento
            self.config["cards_sincronizados"][str(contract_id)] = card_id

            # Salva de volta no arquivo
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            print(f"✅ Relação contrato {contract_id} → card {card_id} salva")

        except Exception as e:
            print(f"❌ Erro ao salvar relação contrato-card: {e}")

    def create_card(self, list_id, name, desc):
        """
        Cria um novo cartão no Trello.
        """
        url = f"{self.base_url}/cards"
        query = {
            'key': self.api_key,
            'token': self.token,
            'idList': list_id,
            'name': name,
            'desc': desc
        }
        try:
            response = requests.post(url, params=query)
            if response.status_code == 200:
                return (True, response.json())
            else:
                return (False, response.text)
        except Exception as e:
            return (False, str(e))

    def delete_card(self, card_id):
        """
        Remove um card específico do Trello.
        """
        url = f"{self.base_url}/cards/{card_id}"
        query = {'key': self.api_key, 'token': self.token}
        try:
            response = requests.delete(url, params=query)
            return response.status_code == 200
        except:
            return False

    def update_card(self, card_id, id_list, name, desc):
        """
        Move o card para uma nova lista e atualiza título/descrição.
        """
        url = f"{self.base_url}/cards/{card_id}"
        query = {
            'key': self.api_key,
            'token': self.token,
            'idList': id_list,
            'name': name,
            'desc': desc
        }
        try:
            response = requests.put(url, params=query)
            if response.status_code == 200:
                return (True, response.json())
            else:
                return (False, response.text)
        except Exception as e:
            return (False, str(e))

    def add_comment(self, card_id, text):
        """
        Adiciona um comentário a um card existente.
        """
        url = f"{self.base_url}/cards/{card_id}/actions/comments"
        query = {
            'key': self.api_key,
            'token': self.token,
            'text': text
        }
        try:
            response = requests.post(url, params=query)
            return response.status_code == 200
        except:
            return False

    def get_all_cards(self, board_id=None):
        """
        Busca todos os cards de um board.
        """
        if not board_id:
            board_id = self.config.get("board_id")

        if not board_id:
            print("❌ Board ID não configurado")
            return []

        url = f"{self.base_url}/boards/{board_id}/cards"
        query = {
            'key': self.api_key,
            'token': self.token
        }

        try:
            response = requests.get(url, params=query)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erro ao buscar cards: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Erro ao buscar cards: {e}")
            return []

    def get_card_comments(self, card_id):
        """
        Busca todos os comentários de um card.
        """
        url = f"{self.base_url}/cards/{card_id}/actions"
        query = {
            'key': self.api_key,
            'token': self.token,
            'filter': 'commentCard'
        }

        try:
            response = requests.get(url, params=query)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except:
            return []

    def delete_comment(self, card_id, comment_id):
        url = f"{self.base_url}/actions/{comment_id}"
        query = {
            'key': self.api_key,
            'token': self.token
        }

        try:
            response = requests.delete(url, params=query)
            return response.status_code == 200
        except:
            return False

    def set_due_date(self, card_id, date_string):
        """Define a data de entrega (vencimento) do card."""
        # O Trello espera formato ISO. Vamos garantir que YYYY-MM-DD funcione.
        url = f"{self.base_url}/cards/{card_id}"
        query = {
            'key': self.api_key, 
            'token': self.token, 
            'due': date_string  # Aceita '2026-12-31' ou null para remover
        }
        try:
            requests.put(url, params=query)
            return True
        except:
            return False

    def add_attachment(self, card_id, url, name):
        """Adiciona um link como anexo no card."""
        url_api = f"{self.base_url}/cards/{card_id}/attachments"
        query = {
            'key': self.api_key, 
            'token': self.token, 
            'url': url,
            'name': name
        }
        try:
            requests.post(url_api, params=query)
            return True
        except:
            return False

    