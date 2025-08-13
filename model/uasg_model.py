import os
import sys
import json
import time
import requests
import sqlite3
from datetime import datetime # Adicionado para comparação de datas

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
        self.base_dir = Path(resource_path(base_dir))
        self.database_dir = self.base_dir / "database"
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.database_dir / "gerenciador_uasg.db"
        self.config_path = self.base_dir / "config.json"
        print(f"📁 Caminho do banco de dados SQLite: {self.db_path}")
        self._create_tables()  # Cria as tabelas no banco de dados

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        # Tabela para UASGs (apenas para referência, os contratos são o foco)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uasgs (
                uasg_code TEXT PRIMARY KEY,
                nome_resumido TEXT
            )
        ''')
        # Tabela para Contratos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contratos (
                id TEXT PRIMARY KEY,
                uasg_code TEXT NOT NULL,
                numero TEXT,
                licitacao_numero TEXT,
                processo TEXT,
                fornecedor_nome TEXT,
                fornecedor_cnpj TEXT,
                objeto TEXT,
                valor_global TEXT,
                vigencia_inicio TEXT,
                vigencia_fim TEXT,
                tipo TEXT,
                modalidade TEXT,
                contratante_orgao_unidade_gestora_codigo TEXT, -- Para buscar o status
                contratante_orgao_unidade_gestora_nome_resumido TEXT,
                raw_json TEXT, -- Armazena o JSON completo do contrato
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code)
            )
        ''')
        # Tabela para Status, Registros e Comentários (anteriormente em status_glob)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_contratos (
                contrato_id TEXT PRIMARY KEY,
                uasg_code TEXT, -- Adicionado para facilitar a busca de status por UASG
                status TEXT,
                objeto_editado TEXT,
                portaria_edit TEXT,
                radio_options_json TEXT, -- Armazena o JSON das opções de rádio
                data_registro TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uasg_code TEXT, -- Adicionado para referência direta
                contrato_id TEXT NOT NULL,
                texto TEXT UNIQUE,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code), -- Opcional, mas bom para integridade
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        # Adiciona um índice na coluna contrato_id para otimizar buscas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_status_contrato_id ON registros_status (contrato_id)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comentarios_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uasg_code TEXT, -- Adicionado para referência direta
                contrato_id TEXT NOT NULL,
                texto TEXT UNIQUE,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code), -- Opcional, mas bom para integridade
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        # Adiciona um índice na coluna contrato_id para otimizar buscas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comentarios_status_contrato_id ON comentarios_status (contrato_id)
        ''')
        try:
            cursor.execute("SELECT portaria_edit FROM status_contratos LIMIT 1")
        except sqlite3.OperationalError:
            print("Atualizando schema: Adicionando coluna 'portaria_edit' à tabela 'status_contratos'.")
            cursor.execute("ALTER TABLE status_contratos ADD COLUMN portaria_edit TEXT")

        conn.commit()
        conn.close()

    def load_saved_uasgs(self):
        """Carrega todas as UASGs salvas e seus contratos no banco de dados."""
        uasgs = {}
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT uasg_code FROM contratos")
        uasg_codes = [row['uasg_code'] for row in cursor.fetchall()]

        for uasg_code in uasg_codes:
            cursor.execute("SELECT raw_json FROM contratos WHERE uasg_code = ?", (uasg_code,))
            contratos_raw = cursor.fetchall()
            contratos_list = []
            for contrato_row in contratos_raw:
                try:
                    contratos_list.append(json.loads(contrato_row['raw_json']))
                except json.JSONDecodeError as e:
                    print(f"Erro ao decodificar raw_json para contrato na UASG {uasg_code}: {e}")
            uasgs[uasg_code] = contratos_list
        
        conn.close()
        return uasgs

    def fetch_uasg_data(self, uasg, local_api_host="http://192.168.0.10:8000"):
        """
        Busca os dados de contratos de uma UASG.
        1. Primeiro tenta usar a API local (sua API FastAPI).
        2. Se a API local não responder ou não tiver dados, faz a requisição para a API pública.
        """
        mode = self.load_setting("data_mode", "Online")

        # URL da sua API local
        url_local = f"{local_api_host}/api/contratos/raw/{uasg}"
        # URL da API pública original
        url_publica = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"

        tentativas_maximas = 3

        """# ------------- 1️⃣ Tentar API Local -------------
        for tentativa in range(1, tentativas_maximas + 1):
            try:
                print(f"Tentativa {tentativa}/{tentativas_maximas} - Buscando dados da UASG {uasg} via API LOCAL...")
                response = requests.get(url_local, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data:  # Se tiver dados no seu servidor local
                        print("✅ Dados obtidos da API local com sucesso!")
                        return data
                    else:
                        print("⚠ API local respondeu, mas sem dados para essa UASG.")
                        break
                else:
                    print(f"⚠ API local retornou status {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"⚠ Falha ao conectar à API local: {e}")
                time.sleep(2)"""

        # ------------- 2️⃣ Se falhar, tentar API Pública -------------
        if mode == "Offline":
            print(f"🔄 Modo Offline: Carregando contratos da UASG {uasg} do banco de dados.")
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM contratos WHERE uasg_code = ?", (uasg,))
            contratos_raw = cursor.fetchall()
            conn.close()
            return [json.loads(row['raw_json']) for row in contratos_raw]
        else:
            print(f"☁️ Modo Online: Buscando contratos da UASG {uasg} via API.")
            for tentativa in range(1, tentativas_maximas + 1):
                try:
                    print(f"Tentativa {tentativa}/{tentativas_maximas} - Buscando dados da UASG {uasg} via API PÚBLICA...")
                    response = requests.get(url_publica, timeout=10)
                    response.raise_for_status()
                    print("✅ Dados obtidos da API pública com sucesso!")
                    return response.json()
                except requests.exceptions.RequestException as e:
                    print(f"⚠ Erro na tentativa {tentativa}/{tentativas_maximas} ao buscar dados da UASG {uasg} na API pública: {e}")
                    if tentativa < tentativas_maximas:
                        time.sleep(2)
                    else:
                        raise requests.exceptions.RequestException(f"Falha ao buscar dados da UASG {uasg} após {tentativas_maximas} tentativas.")
                    
    def get_sub_data_for_contract(self, contrato_id, data_type):
        """
        Busca dados de sub-tabelas (ex: 'empenhos', 'arquivos').
        'data_type' deve ser o nome da tabela no DB e o nome no link da API.
        """
        mode = self.load_setting("data_mode", "Online")
        
        if mode == "Offline":
            print(f"🔄 Modo Offline: Carregando '{data_type}' do contrato {contrato_id} do DB.")
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                # O nome da tabela é o mesmo que o 'data_type'
                cursor.execute(f"SELECT raw_json FROM {data_type} WHERE contrato_id = ?", (str(contrato_id),))
                data_raw = cursor.fetchall()
                conn.close()
                return [json.loads(row['raw_json']) for row in data_raw], None
            except sqlite3.Error as e:
                print(f"❌ Erro ao consultar a tabela '{data_type}' no modo offline: {e}")
                conn.close()
                return None, f"Tabela '{data_type}' não encontrada ou erro no DB."
        else:
            print(f"☁️ Modo Online: Buscando '{data_type}' do contrato {contrato_id} via API.")
            api_url = f"https://contratos.comprasnet.gov.br/api/contrato/{contrato_id}/{data_type}"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return response.json(), None
                else:
                    return None, f"Erro na API: Status {response.status_code}"
            except requests.RequestException as e:
                return None, f"Erro de rede: {e}"
        
    def save_uasg_data(self, uasg, data):
        """Salva os dados da UASG no banco de dados SQLite."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Adiciona ou atualiza a UASG na tabela uasgs (opcional, mas bom para referência)
        nome_resumido_uasg = ""
        if data and len(data) > 0:
            nome_resumido_uasg = data[0].get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
        cursor.execute("INSERT OR IGNORE INTO uasgs (uasg_code, nome_resumido) VALUES (?, ?)", (uasg, nome_resumido_uasg))

        for contrato_data in data:
            cursor.execute('''
                INSERT OR REPLACE INTO contratos (
                    id, uasg_code, numero, licitacao_numero, processo, 
                    fornecedor_nome, fornecedor_cnpj, objeto, valor_global, 
                    vigencia_inicio, vigencia_fim, tipo, modalidade,
                    contratante_orgao_unidade_gestora_codigo,
                    contratante_orgao_unidade_gestora_nome_resumido,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contrato_data.get("id"), uasg, contrato_data.get("numero"),
                contrato_data.get("licitacao_numero"), contrato_data.get("processo"),
                contrato_data.get("fornecedor", {}).get("nome"),
                contrato_data.get("fornecedor", {}).get("cnpj_cpf_idgener"),
                contrato_data.get("objeto"), contrato_data.get("valor_global"),
                contrato_data.get("vigencia_inicio"), contrato_data.get("vigencia_fim"),
                contrato_data.get("tipo"), contrato_data.get("modalidade"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                json.dumps(contrato_data) # Salva o JSON completo
            ))
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} salvos no banco de dados.")

    def update_uasg_data(self, uasg):
        """Atualiza os dados da UASG no banco de dados, comparando com os dados antigos."""
        # Buscar novos dados da API
        new_data = self.fetch_uasg_data(uasg)
        if new_data is None:
            print(f"⚠ Não foi possível buscar novos dados da UASG {uasg}.")
            return 0, 0

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Obter IDs dos contratos existentes (eles já são TEXTO/string no DB)
        cursor.execute("SELECT id FROM contratos WHERE uasg_code = ?", (uasg,))
        old_contract_ids = {row['id'] for row in cursor.fetchall()}
        
        # --- CORREÇÃO APLICADA AQUI ---
        # Converte os IDs da API para string para a comparação funcionar corretamente
        new_contract_ids = {str(c_data.get("id")) for c_data in new_data}

        contracts_to_add_count = 0
        contracts_to_remove_count = 0

        # Adicionar/Atualizar contratos
        for contrato_data in new_data:
            # --- CORREÇÃO APLICADA AQUI ---
            # Usa o ID como string em todas as operações
            contrato_id = str(contrato_data.get("id"))

            if contrato_id not in old_contract_ids:
                contracts_to_add_count += 1
            
            # Usar INSERT OR REPLACE para simplificar (atualiza se existir, insere se não)
            cursor.execute('''
                INSERT OR REPLACE INTO contratos (
                    id, uasg_code, numero, licitacao_numero, processo, 
                    fornecedor_nome, fornecedor_cnpj, objeto, valor_global, 
                    vigencia_inicio, vigencia_fim, tipo, modalidade,
                    contratante_orgao_unidade_gestora_codigo,
                    contratante_orgao_unidade_gestora_nome_resumido,
                    raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contrato_id, uasg, contrato_data.get("numero"),
                contrato_data.get("licitacao_numero"), contrato_data.get("processo"),
                contrato_data.get("fornecedor", {}).get("nome"),
                contrato_data.get("fornecedor", {}).get("cnpj_cpf_idgener"),
                contrato_data.get("objeto"), contrato_data.get("valor_global"),
                contrato_data.get("vigencia_inicio"), contrato_data.get("vigencia_fim"),
                contrato_data.get("tipo"), contrato_data.get("modalidade"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                json.dumps(contrato_data)
            ))

        # Remover contratos que não existem mais
        for old_id in old_contract_ids:
            # A comparação agora funciona porque é string vs string
            if old_id not in new_contract_ids:
                cursor.execute("DELETE FROM contratos WHERE id = ?", (old_id,))
                # Limpa também as tabelas relacionadas
                cursor.execute("DELETE FROM status_contratos WHERE contrato_id = ?", (old_id,))
                cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (old_id,))
                cursor.execute("DELETE FROM comentarios_status WHERE contrato_id = ?", (old_id,))
                contracts_to_remove_count += 1
        
        conn.commit()
        conn.close()
        print(f"✅ UASG {uasg} atualizada: {contracts_to_add_count} novos/atualizados, {contracts_to_remove_count} removidos.")
        return contracts_to_add_count, contracts_to_remove_count

    def delete_uasg_data(self, uasg):
        """Remove os dados da UASG do banco de dados."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Primeiro, obter os IDs dos contratos associados a esta UASG para limpar tabelas relacionadas
        cursor.execute("SELECT id FROM contratos WHERE uasg_code = ?", (uasg,))
        contrato_ids = [row['id'] for row in cursor.fetchall()]

        for contrato_id in contrato_ids:
            cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (contrato_id,))
            cursor.execute("DELETE FROM comentarios_status WHERE contrato_id = ?", (contrato_id,))
            cursor.execute("DELETE FROM status_contratos WHERE contrato_id = ?", (contrato_id,))

        # Deletar os contratos da UASG
        cursor.execute("DELETE FROM contratos WHERE uasg_code = ?", (uasg,))
        # Opcionalmente, deletar a própria UASG da tabela uasgs
        cursor.execute("DELETE FROM uasgs WHERE uasg_code = ?", (uasg,))
        
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} removidos do banco de dados.")
        # self.load_saved_uasgs() # O controller chamará isso

    def get_all_status_data(self):
        """Busca todos os dados de status, registros e comentários do banco de dados."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        all_data = []

        try:
            # Buscar todos os status_contratos
            cursor.execute("SELECT contrato_id, uasg_code, status, objeto_editado, portaria_edit, radio_options_json, data_registro FROM status_contratos")
            status_rows = cursor.fetchall()

            for status_row in status_rows:
                contrato_id = status_row['contrato_id']
                data_entry = dict(status_row) # Converte a linha do DB para um dicionário

                # Buscar registros para este contrato_id
                cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (contrato_id,))
                data_entry['registros'] = [row['texto'] for row in cursor.fetchall()]

                # Buscar comentários para este contrato_id
                cursor.execute("SELECT texto FROM comentarios_status WHERE contrato_id = ?", (contrato_id,))
                data_entry['comentarios'] = [row['texto'] for row in cursor.fetchall()]
                
                all_data.append(data_entry)
            
        except sqlite3.Error as e:
            print(f"Erro ao buscar todos os dados de status: {e}")
            return [] # Retorna lista vazia em caso de erro
        finally:
            conn.close()
        
        return all_data

    def import_statuses(self, data_to_import):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            for entry in data_to_import:
                contrato_id = entry.get('contrato_id')
                uasg_code = entry.get('uasg_code')

                if not contrato_id or not uasg_code:
                    print(f"Aviso: Entrada ignorada por falta de 'contrato_id' ou 'uasg_code': {entry}")
                    continue

                data_registro_import_str = entry.get('data_registro')
                if not data_registro_import_str:
                    print(f"Aviso: 'data_registro' não encontrada para o contrato {contrato_id}. A entrada de status será ignorada.")
                    continue

                # --- LÓGICA DE COMPARAÇÃO DE DATAS ---
                cursor.execute("SELECT data_registro FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
                existing_row = cursor.fetchone()

                should_update = True
                if existing_row and existing_row['data_registro']:
                    try:
                        datetime_db = datetime.strptime(existing_row['data_registro'], "%d/%m/%Y %H:%M:%S")
                        datetime_import = datetime.strptime(data_registro_import_str, "%d/%m/%Y %H:%M:%S")
                        if datetime_db >= datetime_import:
                            should_update = False
                            print(f"Info: Dados para o contrato {contrato_id} no banco de dados são mais recentes. Importação ignorada.")
                    except (ValueError, TypeError):
                        pass # Se as datas forem inválidas, permite a atualização para corrigir o dado.
                
                if should_update:
                    # Prepara um dicionário com todos os dados, usando valores padrão para campos que podem não existir no JSON
                    status_data = {
                        "contrato_id": contrato_id,
                        "uasg_code": uasg_code,
                        "status": entry.get('status'),
                        "objeto_editado": entry.get('objeto_editado'),
                        "portaria_edit": entry.get('portaria_edit', ''), # <<< PONTO CHAVE: Usa '' se 'portaria_edit' não existir
                        "radio_options_json": entry.get('radio_options_json'),
                        "data_registro": data_registro_import_str
                    }

                    # Usa INSERT OR REPLACE para inserir ou atualizar o registro de uma só vez
                    cursor.execute('''
                        INSERT OR REPLACE INTO status_contratos 
                        (contrato_id, uasg_code, status, objeto_editado, portaria_edit, radio_options_json, data_registro) 
                        VALUES (:contrato_id, :uasg_code, :status, :objeto_editado, :portaria_edit, :radio_options_json, :data_registro)
                    ''', status_data)
                    print(f"Info: Dados do contrato {contrato_id} foram inseridos/atualizados.")

                # A lógica para registros e comentários permanece, pois é independente da atualização do status
                # Deleta os antigos para evitar duplicatas
                for texto_reg in entry.get('registros', []):
                    cursor.execute("INSERT INTO registros_status (contrato_id, uasg_code, texto) VALUES (?, ?, ?)", (contrato_id, uasg_code, texto_reg))

                cursor.execute("DELETE FROM comentarios_status WHERE contrato_id = ?", (contrato_id,))
                for texto_com in entry.get('comentarios', []):
                    cursor.execute("INSERT INTO comentarios_status (contrato_id, uasg_code, texto) VALUES (?, ?, ?)", (contrato_id, uasg_code, texto_com))
            
            conn.commit()
            print("Importação de dados de status concluída com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao importar dados de status para o banco de dados: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_setting(self, key, value):
        """Salva uma configuração no arquivo config.json."""
        config_data = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError: pass # Ignora se o arquivo estiver corrompido
        
        config_data[key] = value
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)

    def load_setting(self, key, default_value=None):
        """Carrega uma configuração do arquivo config.json."""
        if not self.config_path.exists():
            return default_value
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data.get(key, default_value)
        except (json.JSONDecodeError, IOError):
            return default_value
