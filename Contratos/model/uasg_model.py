import os
import sys
import json
import time
import requests
import sqlite3
from datetime import datetime # Adicionado para comparação de datas
from pathlib import Path

from .database import init_database
from .models import Base, Contrato, StatusContrato, RegistroStatus, RegistroMensagem, Uasg

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
        
        config_dir = self.base_dir / "utils" / "json"
        config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = config_dir / "config.json"
       
        # Carrega o caminho do BD do config.json ou usa o padrão
        default_db_dir = self.base_dir / "database"
        db_directory_str = self.load_setting("db_path", str(default_db_dir))
        
        self.database_dir = Path(db_directory_str) # Converte a string de volta para Path
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.database_dir / "gerenciador_uasg.db"

        init_database(self.db_path)

        print(f"📁 Caminho do banco de dados SQLite: {self.db_path}")

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_db_session(self):
        from .database import SessionLocal
        return SessionLocal()

    def load_saved_uasgs(self):
        """
        REFATORADO: Carrega todas as UASGs e seus contratos usando SQLAlchemy.
        """
        db = self._get_db_session()
        uasgs = {}
        try:
            # 1. Pega todos os códigos de UASG distintos
            uasg_codes_result = db.query(Contrato.uasg_code).distinct().all()
            uasg_codes = [code for (code,) in uasg_codes_result]

            # 2. Para cada UASG, busca todos os seus contratos
            for uasg_code in uasg_codes:
                contratos = db.query(Contrato).filter(Contrato.uasg_code == uasg_code).all()
                # Converte os objetos Contrato de volta para dicionários (JSON)
                contratos_list = [json.loads(c.raw_json) for c in contratos]
                uasgs[uasg_code] = contratos_list
        except Exception as e:
            print(f"❌ Erro ao carregar UASGs salvas com SQLAlchemy: {e}")
        finally:
            db.close()
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
        db = self._get_db_session()
        try:
            # --- LÓGICA CORRETA COM SQLALCHEMY ---
            # 1. Cria ou atualiza a informação da UASG
            if data:
                nome_resumido = data[0].get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido", "")
                
                # Cria um objeto Uasg e usa merge para fazer um "INSERT OR IGNORE"
                nova_uasg = Uasg(uasg_code=uasg, nome_resumido=nome_resumido)
                db.merge(nova_uasg)

            # 2. Cria ou atualiza cada contrato associado
            for contrato_data in data:
                novo_contrato = Contrato(
                    id=str(contrato_data.get("id")),
                    uasg_code=uasg,
                    numero=contrato_data.get("numero"),
                    licitacao_numero=contrato_data.get("licitacao_numero"),
                    processo=contrato_data.get("processo"),
                    fornecedor_nome=contrato_data.get("fornecedor", {}).get("nome"),
                    fornecedor_cnpj=contrato_data.get("fornecedor", {}).get("cnpj_cpf_idgener"),
                    objeto=contrato_data.get("objeto"),
                    valor_global=contrato_data.get("valor_global"),
                    vigencia_inicio=contrato_data.get("vigencia_inicio"),
                    vigencia_fim=contrato_data.get("vigencia_fim"),
                    tipo=contrato_data.get("tipo"),
                    modalidade=contrato_data.get("modalidade"),
                    contratante_orgao_unidade_gestora_codigo=contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo"),
                    contratante_orgao_unidade_gestora_nome_resumido=contrato_data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("nome_resumido"),
                    raw_json=json.dumps(contrato_data)
                )
                db.merge(novo_contrato)
            
            # 3. Salva todas as alterações no banco de dados de uma só vez
            db.commit()
            print(f"✅ Dados da UASG {uasg} salvos com SQLAlchemy.")

        except Exception as e:
            print(f"❌ Erro ao salvar dados com SQLAlchemy: {e}")
            db.rollback() # Desfaz tudo em caso de erro
        finally:
            db.close() # Fecha a sessão

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
        
        new_contract_ids = {str(c_data.get("id")) for c_data in new_data}

        contracts_to_add_count = 0
        contracts_to_remove_count = 0

        # Adicionar/Atualizar contratos
        for contrato_data in new_data:
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

    def delete_uasg_data(self, uasg_code):
        db = self._get_db_session()
        try:
            # Esta linha agora funcionará porque 'Uasg' foi importado
            uasg_to_delete = db.query(Uasg).filter(Uasg.uasg_code == uasg_code).first()
            
            if uasg_to_delete:
                print(f"Deletando dados da UASG {uasg_code} com SQLAlchemy...")
                
                # Graças ao 'cascade' que definimos nos modelos, o SQLAlchemy irá deletar
                # automaticamente todos os contratos e seus dados relacionados.
                db.delete(uasg_to_delete)
                db.commit()
                print(f"✅ Dados da UASG {uasg_code} removidos com sucesso.")
            else:
                print(f"⚠ UASG {uasg_code} não encontrada no banco de dados para exclusão.")
                
        except Exception as e:
            print(f"❌ Erro ao deletar dados com SQLAlchemy: {e}")
            db.rollback()
        finally:
            db.close()

    def get_all_status_data(self):
        """
        Busca todos os contratos e seus dados de status associados (status, registros, links, etc.)
        para exportação. Inclui contratos mesmo que não tenham status explicitamente salvo.
        """
        from .models import StatusContrato, RegistroStatus, LinksContrato, RegistroMensagem, Contrato,  Fiscalizacao # Reimporta localmente se necessário
        
        db = self._get_db_session()
        all_export_data = []

        try:
            # 1. Busca TODOS os contratos primeiro
            all_contracts = db.query(Contrato).all()
            print(f"[get_all_status_data] Encontrados {len(all_contracts)} contratos no total.") # Depuração

            for contrato in all_contracts:
                contrato_id = contrato.id
                uasg_code = contrato.uasg_code
               
                status_info = db.query(StatusContrato).filter(StatusContrato.contrato_id == contrato_id).first()
                registros_status = db.query(RegistroStatus.texto).filter(RegistroStatus.contrato_id == contrato_id).all()
                lista_registros_status = [reg[0] for reg in registros_status]
                registros_msg = db.query(RegistroMensagem.texto).filter(RegistroMensagem.contrato_id == contrato_id).all()
                lista_registros_msg = [reg[0] for reg in registros_msg]

                # 5. Busca os Links
                links_info = db.query(LinksContrato).filter(LinksContrato.contrato_id == contrato_id).first()
                links_dict = {}
                if links_info:
                    links_dict = {
                        "link_contrato": links_info.link_contrato,
                        "link_ta": links_info.link_ta,
                        "link_portaria": links_info.link_portaria,
                        "link_pncp_espc": links_info.link_pncp_espc,
                        "link_portal_marinha": links_info.link_portal_marinha
                    }

                fiscalizacao_info = db.query(Fiscalizacao).filter(Fiscalizacao.contrato_id == contrato_id).first()
                fiscalizacao_dict = {}
                if fiscalizacao_info:
                    fiscalizacao_dict = {
                        "fiscal_gestor": fiscalizacao_info.gestor or "",
                        "fiscal_titular": fiscalizacao_info.fiscal_titular or "",
                        "fiscal_substituto": fiscalizacao_info.fiscal_substituto or "",
                        "fiscal_setor_responsavel": fiscalizacao_info.setor_responsavel or "",
                        "fiscal_data": fiscalizacao_info.data_fiscalizacao or "",
                        "fiscal_observacoes": fiscalizacao_info.observacoes or "",
                        "fiscal_acoes_corretivas": fiscalizacao_info.acoes_corretivas or "",
                        "fiscal_data_criacao": fiscalizacao_info.data_criacao or "",
                        "fiscal_data_atualizacao": fiscalizacao_info.data_atualizacao or ""
                    }

                # 6. Monta a entrada de dados para este contrato
                data_entry = {
                    "contrato_id": contrato_id,
                    "uasg_code": uasg_code,
                    # Usa dados do status_info se existir, senão usa defaults
                    "status": status_info.status if status_info else "SEÇÃO CONTRATOS", # Default
                    "objeto_editado": status_info.objeto_editado if status_info else contrato.objeto, # Default: objeto original
                    "portaria_edit": status_info.portaria_edit if status_info else "",
                    "termo_aditivo_edit": status_info.termo_aditivo_edit if status_info else "",
                    "radio_options_json": status_info.radio_options_json if status_info else "{}", # Default: JSON vazio
                    "data_registro": status_info.data_registro if status_info else "",
                    # Adiciona listas de registros e links
                    "registros": lista_registros_status,
                    "registros_mensagem": lista_registros_msg,
                    **links_dict, # Adiciona os links ao dicionário principal
                    **fiscalizacao_dict
                }
                
                # Só adiciona à exportação se houver alguma informação de status relevante
                # (status diferente do padrão, registros, links, objeto editado, etc.)
                is_relevant = (
                    data_entry["status"] != "SEÇÃO CONTRATOS" or
                    data_entry["registros"] or
                    data_entry["registros_mensagem"] or
                    links_dict or
                    fiscalizacao_dict or
                    (status_info and (status_info.objeto_editado or status_info.portaria_edit or status_info.termo_aditivo_edit))
                )
                
                if is_relevant:
                    all_export_data.append(data_entry)
            
            print(f"[get_all_status_data] {len(all_export_data)} contratos com dados relevantes encontrados para exportação.") # Depuração
                
        except Exception as e:
            print(f"Erro ao buscar todos os dados de status com SQLAlchemy: {e}")
            return [] # Retorna lista vazia em caso de erro grave
        finally:
            db.close()
        
        # Retorna a lista de dados relevantes
        return all_export_data

    def import_statuses(self, data_to_import):
        """REFATORADO COM SQLALCHEMY: Importa status, registros e links de um JSON usando uma única sessão."""
        # Importa os modelos e datetime
        # --- CORREÇÃO AQUI ---
        from .models import StatusContrato, RegistroStatus, RegistroMensagem, Fiscalizacao # Alterado de RegistrosStatus para RegistroStatus
        from datetime import datetime
        
        db = self._get_db_session() # Inicia a sessão SQLAlchemy UMA ÚNICA VEZ para toda a operação

        try:
            for entry in data_to_import:
                contrato_id = entry.get('contrato_id')
                uasg_code = entry.get('uasg_code')
                data_registro_import_str = entry.get('data_registro')

                if not all([contrato_id, uasg_code, data_registro_import_str]):
                    print(f"Aviso: Entrada ignorada por falta de dados essenciais: {entry}")
                    continue

                # --- LÓGICA DE COMPARAÇÃO DE DATAS USANDO SQLAlchemy ---
                existing_status = db.query(StatusContrato).filter(StatusContrato.contrato_id == contrato_id).first()
                
                should_update = True
                if existing_status and existing_status.data_registro:
                    try:
                        datetime_db = datetime.strptime(existing_status.data_registro, "%d/%m/%Y %H:%M:%S")
                        datetime_import = datetime.strptime(data_registro_import_str, "%d/%m/%Y %H:%M:%S")
                        if datetime_db >= datetime_import:
                            should_update = False
                            print(f"Info: Dados para o contrato {contrato_id} no DB são mais recentes. Ignorando.")
                    except (ValueError, TypeError):
                        pass
                
                if should_update:
                    if not existing_status:
                        existing_status = StatusContrato(contrato_id=contrato_id)
                        db.add(existing_status)
                    
                    existing_status.uasg_code = uasg_code
                    existing_status.status = entry.get('status')
                    existing_status.objeto_editado = entry.get('objeto_editado')
                    existing_status.portaria_edit = entry.get('portaria_edit', '')
                    existing_status.termo_aditivo_edit = entry.get('termo_aditivo_edit', '')
                    existing_status.radio_options_json = entry.get('radio_options_json')
                    existing_status.data_registro = data_registro_import_str
                    print(f"Info: Dados do contrato {contrato_id} preparados para atualização.")

                    link_data = {
                        "link_contrato": entry.get('link_contrato', ''),
                        "link_ta": entry.get('link_ta', ''),
                        "link_portaria": entry.get('link_portaria', ''),
                        "link_pncp_espc": entry.get('link_pncp_espc', ''),
                        "link_portal_marinha": entry.get('link_portal_marinha', '')
                    }
                    self.save_contract_links(contrato_id, link_data, db_session=db)
                    print(f"Info: Links para o contrato {contrato_id} preparados para importação.")

                    fiscalizacao_existing = db.query(Fiscalizacao).filter(Fiscalizacao.contrato_id == contrato_id).first()
                
                    # Verifica se há dados de fiscalização no JSON importado
                    has_fiscal_data = any([
                        entry.get('fiscal_gestor'),
                        entry.get('fiscal_titular'),
                        entry.get('fiscal_substituto'),
                        entry.get('fiscal_data'),
                        entry.get('fiscal_setor_responsavel'),
                        entry.get('fiscal_observacoes'),
                        entry.get('fiscal_acoes_corretivas')
                    ])

                    if has_fiscal_data:
                        if not fiscalizacao_existing:
                            fiscalizacao_existing = Fiscalizacao(contrato_id=contrato_id)
                            fiscalizacao_existing.data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            db.add(fiscalizacao_existing)
                        
                        # Atualiza os campos
                        fiscalizacao_existing.gestor = entry.get('fiscal_gestor', '')
                        fiscalizacao_existing.fiscal_titular = entry.get('fiscal_titular', '')
                        fiscalizacao_existing.fiscal_substituto = entry.get('fiscal_substituto', '')
                        fiscalizacao_existing.setor_responsavel = entry.get('fiscal_setor_responsavel', '')
                        fiscalizacao_existing.data_fiscalizacao = entry.get('fiscal_data', '')
                        fiscalizacao_existing.observacoes = entry.get('fiscal_observacoes', '')
                        fiscalizacao_existing.acoes_corretivas = entry.get('fiscal_acoes_corretivas', '')
                        fiscalizacao_existing.data_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        
                        print(f"Info: Dados de fiscalização para o contrato {contrato_id} preparados para importação.")

                    # --- CORREÇÃO AQUI ---
                    # Deleta registros antigos e insere os novos
                    db.query(RegistroStatus).filter(RegistroStatus.contrato_id == contrato_id).delete(synchronize_session=False) # Alterado de RegistrosStatus para RegistroStatus
                    for texto_reg in entry.get('registros', []):
                        # --- CORREÇÃO AQUI ---
                        novo_registro = RegistroStatus(contrato_id=contrato_id, uasg_code=uasg_code, texto=texto_reg) # Alterado de RegistrosStatus para RegistroStatus
                        db.add(novo_registro)

                    db.query(RegistroMensagem).filter(RegistroMensagem.contrato_id == contrato_id).delete(synchronize_session=False)
                    for texto_msg in entry.get('registros_mensagem', []):
                        novo_registro_msg = RegistroMensagem(contrato_id=contrato_id, texto=texto_msg)
                        db.add(novo_registro_msg)

            db.commit()
            print("Importação de dados concluída com sucesso.")

        except Exception as e:
            print(f"ERRO CRÍTICO ao importar dados. Nenhuma alteração foi salva. Erro: {e}")
            db.rollback()
        finally:
            db.close()


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
        
    def get_contracts_with_status_not_default(self):
        """
        Busca todos os contratos do banco de dados que possuem um status definido
        e que não seja 'SEÇÃO CONTRATOS'.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        contracts_data = []

        try:
            # Consulta contratos que têm status diferente de "SEÇÃO CONTRATOS"
            cursor.execute('''
                SELECT 
                    c.id,
                    c.uasg_code,
                    c.numero,
                    c.processo,
                    c.fornecedor_nome,
                    sc.status,
                    c.vigencia_fim
                FROM contratos c
                JOIN status_contratos sc ON c.id = sc.contrato_id
                WHERE sc.status <> 'SEÇÃO CONTRATOS'
            ''')
            rows = cursor.fetchall()

            for row in rows:
                contracts_data.append({
                    "id": row['id'],
                    "uasg_code": row['uasg_code'],
                    "numero": row['numero'],
                    "processo": row['processo'],
                    "fornecedor_nome": row['fornecedor_nome'],
                    "status": row['status'],
                    "vigencia_fim": row['vigencia_fim']
                })
        except sqlite3.Error as e:
            print(f"Erro ao buscar contratos com status personalizado: {e}")
            return []
        finally:
            conn.close()

        return contracts_data
    
    # =============================== Novos métodos para salvar e buscar links de contratos =============================
    def save_contract_links(self, contrato_id, link_data, db_session=None):
        from .models import LinksContrato
        db = db_session if db_session else self._get_db_session()
        try:
            links = db.query(LinksContrato).filter(LinksContrato.contrato_id == contrato_id).first()
            if not links:
                links = LinksContrato(contrato_id=contrato_id)
                db.add(links)
            
            links.link_contrato = link_data.get('link_contrato')
            links.link_ta = link_data.get('link_ta')
            links.link_portaria = link_data.get('link_portaria')
            links.link_pncp_espc = link_data.get('link_pncp_espc')
            links.link_portal_marinha = link_data.get('link_portal_marinha')
            
            if not db_session:
                db.commit()
        except Exception as e:
            print(f"Erro ao salvar links do contrato {contrato_id}: {e}")
            if not db_session:
                db.rollback()
        finally:
            if not db_session:
                db.close()

    def get_contract_links(self, contrato_id):
        """Busca os links de um contrato específico."""
        from .models import LinksContrato # Importação local
        db = self._get_db_session()
        try:
            links = db.query(LinksContrato).filter(LinksContrato.contrato_id == contrato_id).first()
            if links:
                return {
                    "link_contrato": links.link_contrato,
                    "link_ta": links.link_ta,
                    "link_portaria": links.link_portaria,
                    "link_pncp_espc": links.link_pncp_espc,
                    "link_portal_marinha": links.link_portal_marinha
                }
            return None
        finally:
            db.close()

    # Importação da tabela para links
    def save_status_field(self, contrato_id, field_name, value):
        """Atualiza um campo específico na tabela status_contratos."""
        db = self._get_db_session()
        try:
            status = db.query(StatusContrato).filter(StatusContrato.contrato_id == contrato_id).first()
            if not status:
                # Se não existir, cria um novo status para não perder a informação
                status = StatusContrato(contrato_id=contrato_id)
                db.add(status)
            
            # Define o valor do campo dinamicamente
            setattr(status, field_name, value)
            db.commit()
        except Exception as e:
            print(f"Erro ao salvar o campo '{field_name}' para o contrato {contrato_id}: {e}")
            db.rollback()
        finally:
            db.close()
