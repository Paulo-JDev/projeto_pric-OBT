import os
import json
import sqlite3
import requests
import sys
from pathlib import Path

# Adiciona o diretório do script ao sys.path (caminho absoluto)
def resource_path(relative_path):
    """Retorna o caminho absoluto para um recurso, funcionando tanto no desenvolvimento quanto no empacotamento."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class UASGModel:
    def __init__(self, base_dir):
        self.base_dir = Path(resource_path(base_dir))  # Usa resource_path para garantir o caminho correto
        self.database_dir = self.base_dir / "database"
        self.database_dir.mkdir(parents=True, exist_ok=True)  # Cria a pasta database, se não existir
        print(f"📁 Diretório do banco de dados: {self.database_dir}")

    def load_saved_uasgs(self):
        """Carrega todas as UASGs salvas e seus contratos no banco de dados."""
        uasgs = {}

        # Verifica se o diretório database existe
        if not self.database_dir.exists():
            print("⚠ Diretório 'database' não encontrado. Nenhum dado carregado.")
            return uasgs

        # Itera sobre os diretórios de UASGs
        for uasg_dir in self.database_dir.glob("uasg_*"):
            json_file = uasg_dir / f"{uasg_dir.name}_contratos.json"
            if json_file.exists():
                try:
                    with json_file.open('r', encoding='utf-8') as file:
                        data = json.load(file)
                        if isinstance(data, list):  # Verifica se o JSON é uma lista
                            uasgs[uasg_dir.name.split("_")[1]] = data
                            print(f"✅ UASG {uasg_dir.name.split('_')[1]} carregada com sucesso.")
                        else:
                            print(f"⚠ Formato inválido no arquivo {json_file}: esperado uma lista de dicionários.")
                except json.JSONDecodeError as e:
                    print(f"⚠ Erro ao decodificar JSON no arquivo {json_file}: {e}")
                except Exception as e:
                    print(f"⚠ Erro ao carregar {json_file}: {e}")
            else:
                print(f"⚠ Arquivo {json_file} não encontrado.")

        return uasgs

    def fetch_uasg_data(self, uasg):
        """Faz a requisição para a API e retorna os dados mais recentes."""
        url_api = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"
        try:
            response = requests.get(url_api, timeout=10)  # Adiciona timeout
            response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠ Erro ao buscar dados da UASG {uasg}: {e}")
            return None
    
    def save_uasg_data(self, uasg, data):
        """Salva os dados da UASG em um arquivo JSON e no banco de dados SQLite."""
        # Cria o diretório da UASG (se não existir)
        uasg_dir = self.database_dir / f"uasg_{uasg}"
        uasg_dir.mkdir(parents=True, exist_ok=True)

        # Salva os dados em um arquivo JSON
        json_file = uasg_dir / f"uasg_{uasg}_contratos.json"
        with json_file.open('w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        # Salva os dados no banco de dados SQLite
        db_file = uasg_dir / f"uasg_{uasg}_contratos.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contratos (
                numero INTEGER,
                nome TEXT,
                licitacao_numero TEXT,
                fornecedor_nome TEXT,
                processo INTEGER
            )
        ''')

        for contrato in data:
            cursor.execute('''
                INSERT INTO contratos (numero, nome, licitacao_numero, fornecedor_nome, processo)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                contrato.get("numero"),
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                contrato.get("licitacao_numero"),
                contrato.get("fornecedor", {}).get("nome"),
                contrato.get("processo"),
            ))

        conn.commit()
        conn.close()

    def update_uasg_data(self, uasg):
        """Atualiza os dados da UASG no banco de dados, comparando com os dados antigos."""
        # Cria o diretório da UASG (se não existir)
        uasg_dir = self.database_dir / f"uasg_{uasg}"
        uasg_dir.mkdir(parents=True, exist_ok=True)

        json_file = uasg_dir / f"uasg_{uasg}_contratos.json"
        db_file = uasg_dir / f"uasg_{uasg}_contratos.db"

        # Buscar novos dados da API
        new_data = self.fetch_uasg_data(uasg)
        if new_data is None:
            print(f"⚠ Não foi possível buscar novos dados da UASG {uasg}.")
            return 0, 0

        # Carregar dados antigos do JSON, se existir
        old_data = []
        if json_file.exists():
            with json_file.open("r", encoding="utf-8") as file:
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
                INSERT INTO contratos (nome, numero, licitacao_numero, fornecedor_nome, processo, objeto, vigencia_fim, valor_global)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                contrato.get("numero"),
                contrato.get("licitacao_numero"),
                contrato.get("fornecedor", {}).get("nome"),
                contrato.get("processo"),
                contrato.get("objeto", "Não informado"),
                contrato.get("vigencia_fim", ""),
                contrato.get("valor_global", "0.0")
            ))

        conn.commit()
        conn.close()

        # Substituir o JSON antigo pelo novo
        with json_file.open("w", encoding="utf-8") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)

        print(f"✅ UASG {uasg} atualizada: {len(contracts_to_add)} novos contratos, {len(contracts_to_remove)} removidos.")
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
            "vigencia_fim": "TEXT",
            "valor_global": "TEXT"
        }

        # Adicionar colunas que estão faltando
        for coluna, tipo in colunas_necessarias.items():
            if coluna not in colunas_existentes:
                print(f"🔧 Adicionando a coluna '{coluna}' à tabela contratos...")
                cursor.execute(f"ALTER TABLE contratos ADD COLUMN {coluna} {tipo};")

        conn.commit()
        conn.close()

    def delete_uasg_data(self, uasg):
        """Remove os arquivos e diretório da UASG."""
        uasg_dir = self.database_dir / f"uasg_{uasg}"
        if uasg_dir.exists():
            for file in uasg_dir.iterdir():
                file.unlink()  # Remove arquivos
            uasg_dir.rmdir()  # Remove diretório
            print(f"✅ Dados da UASG {uasg} removidos com sucesso.")
        else:
            print(f"⚠ UASG {uasg} não encontrada.")
