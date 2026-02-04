# integration/model/trello_model.py
import requests

class TrelloModel:
    def __init__(self, api_key=None, token=None):
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"

    def create_card(self, list_id, name, desc):
        """Usa requests para criar um card sem depender de bibliotecas pagas."""
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
                return True, response.json()
            else:
                # Retorna o texto do erro se não for 200
                return False, response.text 
        except Exception as e:
            return False, str(e)
