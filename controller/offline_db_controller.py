import os
import sqlite3
import requests
import time
import json
from datetime import datetime
from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import Qt

class OfflineDBController:
    """
    Controlador dedicado para criar, popular e gerenciar
    o banco de dados para uso offline.
    """
    def __init__(self, parent_view=None):
        self.parent_view = parent_view
        self.db_path = self._setup_paths()

    def _setup_paths(self):
        """Define os caminhos para o diretório e o arquivo do banco de dados."""
        # Caminho para a pasta 'utils' a partir da raiz do projeto
        utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
        db_dir = os.path.join(utils_path, 'DB_offline')
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'gerenciador_uasg.db')

    def _get_db_connection(self):
        """Cria e retorna uma conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Cria todas as tabelas no banco de dados SQLite, se não existirem."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS uasgs (
            uasg_code TEXT PRIMARY KEY,
            nome_resumido TEXT
            )
        ''')
        
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
                contratante_orgao_unidade_gestora_codigo TEXT,
                contratante_orgao_unidade_gestora_nome_resumido TEXT,
                raw_json TEXT,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY,
                contrato_id TEXT NOT NULL,
                receita_despesa TEXT,
                numero TEXT,
                observacao TEXT,
                ug TEXT,
                gestao TEXT,
                fornecedor_cnpj TEXT,
                fornecedor_nome TEXT,
                tipo TEXT,
                categoria TEXT,
                processo TEXT,
                objeto TEXT,
                modalidade TEXT,
                licitacao_numero TEXT,
                data_assinatura TEXT,
                data_publicacao TEXT,
                vigencia_inicio TEXT,
                vigencia_fim TEXT,
                valor_global TEXT,
                raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empenhos (
                id INTEGER PRIMARY KEY,
                contrato_id TEXT NOT NULL,
                unidade_gestora TEXT,
                gestao TEXT,
                numero TEXT,
                data_emissao TEXT,
                credor_cnpj TEXT,
                credor_nome TEXT,
                empenhado TEXT,
                liquidado TEXT,
                pago TEXT,
                informacao_complementar TEXT,
                raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY,
                contrato_id TEXT NOT NULL,
                tipo_id TEXT,
                tipo_material TEXT,
                grupo_id TEXT,
                catmatseritem_id TEXT,
                descricao_complementar TEXT,
                quantidade TEXT,
                valorunitario TEXT,
                valortotal TEXT,
                numero_item_compra TEXT,
                raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos (
                id INTEGER PRIMARY KEY,
                contrato_id TEXT NOT NULL,
                tipo TEXT,
                descricao TEXT,
                path_arquivo TEXT,
                origem TEXT,
                link_sei TEXT,
                raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_contratos (
                contrato_id TEXT PRIMARY KEY,
                uasg_code TEXT,
                status TEXT,
                objeto_editado TEXT,
                radio_options_json TEXT,
                data_registro TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uasg_code TEXT,
                contrato_id TEXT NOT NULL,
                texto TEXT UNIQUE,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code),
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_registros_status_contrato_id ON registros_status (contrato_id)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comentarios_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uasg_code TEXT,
                contrato_id TEXT NOT NULL,
                texto TEXT UNIQUE,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code),
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comentarios_status_contrato_id ON comentarios_status (contrato_id)
        ''')
        conn.commit()
        conn.close()
    
    def _fetch_api_data(self, url, tentativas_maximas=3):
        """Busca dados de uma API com retentativas."""
        for tentativa in range(1, tentativas_maximas + 1):
            try:
                print(f" - Buscando dados em {url} (Tentativa {tentativa}/{tentativas_maximas})")
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"   ⚠ Erro na requisição: {e}")
                if tentativa < tentativas_maximas:
                    time.sleep(2)
                else:
                    print(f"   ❌ Falha ao buscar dados após {tentativas_maximas} tentativas.")
                    return []
        return []

    def _save_sub_table_data(self, conn, table_name, contrato_id, data_list, fields_map):
        """Função genérica para salvar dados em tabelas de sub-itens."""
        cursor = conn.cursor()
        for item_data in data_list:
            values = {key: item_data.get(val) for key, val in fields_map.items()}
            values['contrato_id'] = contrato_id
            values['raw_json'] = json.dumps(item_data)
            
            # Adiciona o ID do item se ele existir no JSON
            if 'id' in fields_map and 'id' in item_data:
                values['id'] = item_data.get('id')
            
            columns = ', '.join(values.keys())
            placeholders = ', '.join(':' + key for key in values.keys())
            query = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)

    def process_and_save_all_data(self, uasg):
        """
        Processo principal: busca, filtra por vigência e salva todos os dados de uma UASG.
        """
        self._create_tables()
        conn = self._get_db_connection()
        cursor = conn.cursor()

        url_publica = f"https://contratos.comprasnet.gov.br/api/contrato/ug/{uasg}"
        main_data = self._fetch_api_data(url_publica)
        
        if not main_data:
            print(f"⚠ Não foi possível obter dados para a UASG {uasg}. Operação cancelada.")
            conn.close()
            return

        # Salva info da UASG
        nome_resumido = main_data[0].get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
        cursor.execute("INSERT OR IGNORE INTO uasgs (uasg_code, nome_resumido) VALUES (?, ?)", (uasg, nome_resumido))

        # Passo 1: Filtrar os contratos com base na vigência
        hoje = datetime.now()
        contratos_a_processar = []
        print(f"Iniciando filtro de {len(main_data)} contratos da UASG {uasg}...")
        for contrato_data in main_data:
            vigencia_fim_str = contrato_data.get("vigencia_fim")
            if vigencia_fim_str:
                try:
                    vigencia_fim = datetime.strptime(vigencia_fim_str, '%Y-%m-%d')
                    if (hoje - vigencia_fim).days <= 70: # Contratos vencidos há no máximo 70 dias ou ainda vigentes
                        contratos_a_processar.append(contrato_data)
                except (ValueError, TypeError):
                    print(f"⚠ Aviso: Data de vigência inválida para o contrato {contrato_data.get('id')}. Será ignorado.")
            else:
                 print(f"⚠ Aviso: Data de vigência não encontrada para o contrato {contrato_data.get('id')}. Será ignorado.")
        
        print(f"Filtro concluído. Serão processados {len(contratos_a_processar)} contratos.")
        if not contratos_a_processar:
            conn.close()
            return

        # Barra de Progresso
        progress = QProgressDialog("Buscando e salvando dados...", "Cancelar", 0, len(contratos_a_processar), self.parent_view)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("Criando Banco de Dados Offline")

        # Passo 2: Processar e salvar apenas os contratos filtrados
        for i, contrato_data in enumerate(contratos_a_processar):
            progress.setValue(i)
            if progress.wasCanceled():
                break

            contrato_id = str(contrato_data.get("id"))
            progress.setLabelText(f"Processando Contrato: {contrato_data.get('numero', contrato_id)}")
            QApplication.processEvents()

            # Salva o contrato principal
            cursor.execute('''
                INSERT OR REPLACE INTO contratos (id, uasg_code, numero, licitacao_numero, processo, 
                fornecedor_nome, fornecedor_cnpj, objeto, valor_global, vigencia_inicio, vigencia_fim, 
                tipo, modalidade, contratante_orgao_unidade_gestora_codigo, 
                contratante_orgao_unidade_gestora_nome_resumido, raw_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                contrato_id, uasg, contrato_data.get("numero"), contrato_data.get("licitacao_numero"),
                contrato_data.get("processo"), contrato_data.get("fornecedor", {}).get("nome"),
                contrato_data.get("fornecedor", {}).get("cnpj_cpf_idgener"), contrato_data.get("objeto"),
                contrato_data.get("valor_global"), contrato_data.get("vigencia_inicio"),
                contrato_data.get("vigencia_fim"), contrato_data.get("tipo"), contrato_data.get("modalidade"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo"),
                contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                json.dumps(contrato_data)
            ))

            links = contrato_data.get("links", {})
            
            # Busca e salva dados das sub-tabelas
            if "historico" in links:
                historico_data = self._fetch_api_data(links["historico"])
                self._save_sub_table_data(conn, 'historico', contrato_id, historico_data, {'id': 'id', 'numero': 'numero', 'objeto': 'objeto', 'valor_global': 'valor_global'})
            
            if "empenhos" in links:
                empenhos_data = self._fetch_api_data(links["empenhos"])
                self._save_sub_table_data(conn, 'empenhos', contrato_id, empenhos_data, {'id': 'id', 'numero': 'numero', 'empenhado': 'empenhado', 'pago': 'pago'})
            
            if "itens" in links:
                itens_data = self._fetch_api_data(links["itens"])
                self._save_sub_table_data(conn, 'itens', contrato_id, itens_data, {'id': 'id', 'descricao_complementar': 'descricao_complementar', 'quantidade': 'quantidade', 'valortotal': 'valortotal'})

            if "arquivos" in links:
                arquivos_data = self._fetch_api_data(links["arquivos"])
                self._save_sub_table_data(conn, 'arquivos', contrato_id, arquivos_data, {'id': 'id', 'tipo': 'tipo', 'descricao': 'descricao', 'path_arquivo': 'path_arquivo'})

        progress.setValue(len(contratos_a_processar))
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} salvos com sucesso no banco de dados offline.")

    def delete_uasg_from_db(self, uasg):
        """Remove todos os dados de uma UASG específica do banco de dados offline."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        print(f"Deletando dados da UASG {uasg} do banco de dados offline...")
        
        # Pega todos os contratos da UASG para deletar os dados relacionados
        cursor.execute("SELECT id FROM contratos WHERE uasg_code = ?", (uasg,))
        contrato_ids = [row['id'] for row in cursor.fetchall()]
        
        if contrato_ids:
            # Deleta de todas as tabelas filhas
            for table in ['historico', 'empenhos', 'itens', 'arquivos', 'status_contratos', 'registros_status', 'comentarios_status']:
                cursor.executemany(f"DELETE FROM {table} WHERE contrato_id = ?", [(cid,) for cid in contrato_ids])
        
        # Deleta da tabela de contratos e uasgs
        cursor.execute("DELETE FROM contratos WHERE uasg_code = ?", (uasg,))
        cursor.execute("DELETE FROM uasgs WHERE uasg_code = ?", (uasg,))
        
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} removidos com sucesso.")


