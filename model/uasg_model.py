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
        """Carrega todas as UASGs salvas e seus contratos no banco de dados."""
        uasgs = {}

        if not os.path.exists(self.database_dir):
            return uasgs

        for uasg_dir in os.listdir(self.database_dir):
            if uasg_dir.startswith("uasg_"):
                json_file = os.path.join(self.database_dir, uasg_dir, f"{uasg_dir}_contratos.json")
                if os.path.isfile(json_file):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as file:
                            uasgs[uasg_dir.split("_")[1]] = json.load(file)
                    except Exception as e:
                        print(f"⚠ Erro ao carregar {json_file}: {e}")

        return uasgs

    def fetch_uasg_data(self, uasg):
        """Faz a requisição para a API e retorna os dados mais recentes."""
        url_api = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"
        response = requests.get(url_api)
        response.raise_for_status()
        return response.json()

    def update_uasg_data(self, uasg):
        """Atualiza os dados da UASG no banco de dados, comparando com os dados antigos."""
        uasg_dir = os.path.join(self.database_dir, f"uasg_{uasg}")
        json_file = os.path.join(uasg_dir, f"uasg_{uasg}_contratos.json")
        db_file = os.path.join(uasg_dir, f"uasg_{uasg}_contratos.db")

        # Buscar novos dados da API
        new_data = self.fetch_uasg_data(uasg)

        # Carregar dados antigos do JSON, se existir
        old_data = []
        if os.path.exists(json_file):
            with open(json_file, "r", encoding="utf-8") as file:
                old_data = json.load(file)

        # Criar dicionários para comparar contratos antigos e novos
        old_contracts = {c["numero"]: c for c in old_data}
        new_contracts = {c["numero"]: c for c in new_data}

        contracts_to_add = {num: c for num, c in new_contracts.items() if num not in old_contracts}
        contracts_to_remove = {num: c for num, c in old_contracts.items() if num not in new_contracts}

        # Atualizar banco de dados
        self._check_and_update_table(db_file)  # Garante que a tabela tem todas as colunas necessárias

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Remover contratos que não existem mais
        for numero in contracts_to_remove:
            cursor.execute("DELETE FROM contratos WHERE numero = ?", (numero,))

        # Adicionar novos contratos
        for contrato in contracts_to_add.values():
            cursor.execute('''
                INSERT INTO contratos (nome, numero, licitacao_numero, fornecedor_nome, processo, objeto, vigencia_fim)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                contrato.get("numero"),
                contrato.get("licitacao_numero"),
                contrato.get("fornecedor", {}).get("nome"),
                contrato.get("processo"),
                contrato.get("objeto", "Não informado"),
                contrato.get("vigencia_fim", "")
            ))

        conn.commit()
        conn.close()

        # Substituir o JSON antigo pelo novo
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)

        return len(contracts_to_add), len(contracts_to_remove)

    def _check_and_update_table(self, db_file):
        """Verifica se a tabela 'contratos' tem todas as colunas e atualiza se necessário."""
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Verificar as colunas existentes
        cursor.execute("PRAGMA table_info(contratos);")
        colunas_existentes = {coluna[1] for coluna in cursor.fetchall()}  # Converte para conjunto para busca rápida

        colunas_necessarias = {
            "nome": "TEXT",
            "numero": "INTEGER PRIMARY KEY",
            "licitacao_numero": "TEXT",
            "fornecedor_nome": "TEXT",
            "processo": "INTEGER",
            "objeto": "TEXT",
            "vigencia_fim": "TEXT"
        }

        # Adicionar colunas que estão faltando
        for coluna, tipo in colunas_necessarias.items():
            if coluna not in colunas_existentes:
                print(f"🔧 Adicionando a coluna '{coluna}' à tabela contratos...")
                cursor.execute(f"ALTER TABLE contratos ADD COLUMN {coluna} {tipo};")

        conn.commit()
        conn.close()
