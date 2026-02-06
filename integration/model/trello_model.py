# integration/model/trello_model.py
import requests

class TrelloModel:
    def __init__(self, api_key=None, token=None):
        self.api_key = api_key
        self.token = token
        self.base_url = "https://api.trello.com/1"

    def create_card(self, list_id, name, desc):
        url = f"{self.base_url}/cards"
        query = {'key': self.api_key, 'token': self.token, 'idList': list_id, 'name': name, 'desc': desc}
        try:
            response = requests.post(url, params=query)
            return (True, response.json()) if response.status_code == 200 else (False, response.text)
        except Exception as e:
            return False, str(e)

    def delete_card(self, card_id):
        """Remove um card específico do Trello."""
        url = f"{self.base_url}/cards/{card_id}"
        query = {'key': self.api_key, 'token': self.token}
        try:
            response = requests.delete(url, params=query)
            return response.status_code == 200
        except:
            return False
        
    def update_card(self, card_id, id_list, name, desc):
        """Move o card para uma nova lista e atualiza título/descrição."""
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
            return (True, response.json()) if response.status_code == 200 else (False, response.text)
        except Exception as e:
            return False, str(e)

    def add_comment(self, card_id, text):
        """Adiciona um comentário a um card existente."""
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
