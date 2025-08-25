# model/offline_db_model.py

import os
import sqlite3
import requests
import time
import json
from datetime import datetime
from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import Qt

# Importa o UASGModel para descobrir o caminho correto do banco de dados
from .uasg_model import UASGModel

class OfflineDBController:
    """
    Controlador refatorado para popular o banco de dados principal com
    dados detalhados para uso offline.
    """
    def __init__(self, parent_view=None):
        self.parent_view = parent_view
        # PONTO CHAVE 1: Pega o caminho do banco de dados do modelo principal
        # para garantir que estamos escrevendo no arquivo correto.
        main_model = UASGModel(base_dir=os.path.abspath("."))
        self.db_path = main_model.db_path
        print(f"OfflineDBController usará o banco de dados em: {self.db_path}")

    def _get_db_connection(self):
        """Cria e retorna uma conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """
        Cria todas as tabelas no banco de dados SQLite, se não existirem.
        Isso é importante para garantir que as tabelas de detalhes (histórico, empenhos, etc.)
        sejam criadas, já que o modelo principal não as conhece.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # As definições de tabela permanecem as mesmas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS uasgs (
            uasg_code TEXT PRIMARY KEY, nome_resumido TEXT
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contratos (
                id TEXT PRIMARY KEY, uasg_code TEXT NOT NULL, numero TEXT, licitacao_numero TEXT,
                processo TEXT, fornecedor_nome TEXT, fornecedor_cnpj TEXT, objeto TEXT,
                valor_global TEXT, vigencia_inicio TEXT, vigencia_fim TEXT, tipo TEXT,
                modalidade TEXT, contratante_orgao_unidade_gestora_codigo TEXT,
                contratante_orgao_unidade_gestora_nome_resumido TEXT, raw_json TEXT,
                FOREIGN KEY (uasg_code) REFERENCES uasgs (uasg_code)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY, contrato_id TEXT NOT NULL, receita_despesa TEXT,
                numero TEXT, observacao TEXT, ug TEXT, gestao TEXT, fornecedor_cnpj TEXT,
                fornecedor_nome TEXT, tipo TEXT, categoria TEXT, processo TEXT, objeto TEXT,
                modalidade TEXT, licitacao_numero TEXT, data_assinatura TEXT,
                data_publicacao TEXT, vigencia_inicio TEXT, vigencia_fim TEXT,
                valor_global TEXT, raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empenhos (
                id INTEGER PRIMARY KEY, contrato_id TEXT NOT NULL, unidade_gestora TEXT,
                gestao TEXT, numero TEXT, data_emissao TEXT, credor_cnpj TEXT,
                credor_nome TEXT, empenhado TEXT, liquidado TEXT, pago TEXT,
                informacao_complementar TEXT, raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY, contrato_id TEXT NOT NULL, tipo_id TEXT, tipo_material TEXT,
                grupo_id TEXT, catmatseritem_id TEXT, descricao_complementar TEXT, quantidade TEXT,
                valorunitario TEXT, valortotal TEXT, numero_item_compra TEXT, raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arquivos (
                id INTEGER PRIMARY KEY, contrato_id TEXT NOT NULL, tipo TEXT, descricao TEXT,
                path_arquivo TEXT, origem TEXT, link_sei TEXT, raw_json TEXT,
                FOREIGN KEY (contrato_id) REFERENCES contratos (id)
            )''')
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
                if tentativa < tentativas_maximas: time.sleep(2)
                else: return []
        return []

    def _save_sub_table_data(self, conn, table_name, contrato_id, data_list):
        """
        PONTO CHAVE 2: Função genérica refatorada para salvar todos os dados
        recebidos da API em tabelas de sub-itens.
        """
        if not data_list: return

        cursor = conn.cursor()
        
        # Pega as colunas da tabela no banco de dados para garantir que só tentemos
        # inserir dados que correspondam a colunas existentes.
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns = {row['name'] for row in cursor.fetchall()}

        for item_data in data_list:
            # Prepara um dicionário apenas com os dados que têm uma coluna correspondente na tabela
            values_to_insert = {key: value for key, value in item_data.items() if key in table_columns}
            
            # Adiciona as colunas fixas
            values_to_insert['contrato_id'] = contrato_id
            values_to_insert['raw_json'] = json.dumps(item_data)
            
            columns = ', '.join(values_to_insert.keys())
            placeholders = ', '.join('?' for _ in values_to_insert)
            
            query = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(values_to_insert.values()))

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
                    # --- LÓGICA DO FILTRO DE -100 DIAS APLICADA AQUI ---
                    if (hoje - vigencia_fim).days <= 100: # Contratos vencidos há no máximo 100 dias ou ainda vigentes
                        contratos_a_processar.append(contrato_data)
                except (ValueError, TypeError):
                    print(f"⚠ Aviso: Data de vigência inválida para o contrato {contrato_data.get('id')}. Será ignorado.")
            else:
                print(f"⚠ Aviso: Data de vigência não encontrada para o contrato {contrato_data.get('id')}. Será ignorado.")
        
        print(f"Filtro concluído. Serão processados {len(contratos_a_processar)} contratos.")
        if not contratos_a_processar:
            conn.close()
            return

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

            # --- LÓGICA PARA SALVAR O CONTRATO PRINCIPAL ADICIONADA AQUI ---
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
            
            # A busca e salvamento das sub-tabelas continua a mesma
            if "historico" in links: self._save_sub_table_data(conn, 'historico', contrato_id, self._fetch_api_data(links["historico"]))
            if "empenhos" in links: self._save_sub_table_data(conn, 'empenhos', contrato_id, self._fetch_api_data(links["empenhos"]))
            if "itens" in links: self._save_sub_table_data(conn, 'itens', contrato_id, self._fetch_api_data(links["itens"]))
            if "arquivos" in links: self._save_sub_table_data(conn, 'arquivos', contrato_id, self._fetch_api_data(links["arquivos"]))

        progress.setValue(len(contratos_a_processar))
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} salvos com sucesso no banco de dados offline.")

    def delete_uasg_from_db(self, uasg):
        """Remove todos os dados de uma UASG específica do banco de dados offline."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM contratos WHERE uasg_code = ?", (uasg,))
        contrato_ids = [row['id'] for row in cursor.fetchall()]
        
        if contrato_ids:
            # Transforma a lista de IDs em uma string para a cláusula IN
            placeholders = ', '.join('?' for _ in contrato_ids)
            for table in ['historico', 'empenhos', 'itens', 'arquivos', 'status_contratos', 'registros_status', 'comentarios_status']:
                cursor.execute(f"DELETE FROM {table} WHERE contrato_id IN ({placeholders})", contrato_ids)
        
        cursor.execute("DELETE FROM contratos WHERE uasg_code = ?", (uasg,))
        cursor.execute("DELETE FROM uasgs WHERE uasg_code = ?", (uasg,))
        
        conn.commit()
        conn.close()
        print(f"✅ Dados da UASG {uasg} removidos com sucesso.")