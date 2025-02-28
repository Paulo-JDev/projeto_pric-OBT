import os
import json
import sqlite3
import requests

class UASGModel:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.database_dir = os.path.join(base_dir, "database")
        os.makedirs(self.database_dir, exist_ok=True)

    def load_saved_uasgs(self):
        uasgs = {}
        for uasg_dir in os.listdir(self.database_dir):
            if uasg_dir.startswith("uasg_"):
                json_file = os.path.join(self.database_dir, uasg_dir, f"{uasg_dir}_contratos.json")
                if os.path.isfile(json_file):
                    with open(json_file, 'r', encoding='utf-8') as file:
                        uasgs[uasg_dir.split("_")[1]] = json.load(file)
        return uasgs

    def fetch_uasg_data(self, uasg):
        url_api = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"
        response = requests.get(url_api)
        response.raise_for_status()
        return response.json()

    def save_uasg_data(self, uasg, data):
        uasg_dir = os.path.join(self.database_dir, f"uasg_{uasg}")
        os.makedirs(uasg_dir, exist_ok=True)

        json_file = os.path.join(uasg_dir, f"uasg_{uasg}_contratos.json")
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        db_file = os.path.join(uasg_dir, f"uasg_{uasg}_contratos.db")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contratos (
                nome TEXT,
                numero INTEGER,
                licitacao_numero TEXT,
                fornecedor_nome TEXT,
                processo INTEGER,
                objeto TEXT
            )
        ''')

        for contrato in data:
            cursor.execute('''
                INSERT INTO contratos (nome, numero, licitacao_numero, fornecedor_nome, processo, objeto)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                # status (na janela do detalhe do contrato, vai ter ujma aba e dentro dessa aba vai ter um butão anonde mostra algumas opçoes de status)
                # cont... ( vai ter por hora 5 opcões, e quando vc muda alguma coisa, vai aparecer uma janela de confirmação)
                # cont..2 (e quando confirmar vai mudar la no tabela de visualização)
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"), # colocar como "Sigla OM"
                contrato.get("numero"),
                # modalidade 
                # adicionar coluna interrativa que tem duas opções: sim ou não
                contrato.get("licitacao_numero"), # deois analisar e deixar so um numero
                contrato.get("fornecedor", {}).get("nome"), # empresa
                #valor
                contrato.get("processo"),
                contrato.get("objeto", "Não informado")
            ))
        conn.commit()
        conn.close()

    def delete_uasg_data(self, uasg):
        uasg_dir = os.path.join(self.database_dir, f"uasg_{uasg}")
        if os.path.exists(uasg_dir):
            for file in os.listdir(uasg_dir):
                os.remove(os.path.join(uasg_dir, file))
            os.rmdir(uasg_dir)
