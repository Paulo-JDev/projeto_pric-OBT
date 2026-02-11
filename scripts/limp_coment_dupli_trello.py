# scripts/limpar_comentarios_duplicados_trello.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integration.model.trello_model import TrelloModel

def limpar_comentarios_duplicados():
    """Remove comentários duplicados de todos os cards do Trello."""
    trello = TrelloModel()

    if not trello.api_key or not trello.token:
        print("❌ Credenciais do Trello não configuradas!")
        return

    # Busca todos os cards do board
    cards = trello.get_all_cards()

    for card in cards:
        card_id = card['id']
        card_name = card['name']

        # Busca comentários do card
        comments = trello.get_card_comments(card_id)

        # Agrupa por texto (ignora UUID)
        textos_vistos = {}
        duplicados = []

        for comment in comments:
            texto = comment['data']['text']
            # Remove o UUID do início (📌 **Registro (abc12345...):**)
            texto_limpo = texto.split(':\n', 1)[-1] if ':\n' in texto else texto

            if texto_limpo in textos_vistos:
                # Comentário duplicado encontrado
                duplicados.append(comment['id'])
                print(f"🗑️ Duplicata encontrada em '{card_name}': {texto_limpo[:50]}...")
            else:
                textos_vistos[texto_limpo] = comment['id']

        # Deleta duplicados
        for comment_id in duplicados:
            if trello.delete_comment(card_id, comment_id):
                print(f"✅ Comentário duplicado removido")
            else:
                print(f"❌ Falha ao remover comentário {comment_id}")

    print(f"\n🎉 Limpeza concluída!")

if __name__ == "__main__":
    limpar_comentarios_duplicados()
