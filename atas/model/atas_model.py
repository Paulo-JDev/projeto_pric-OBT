# atas/model/atas_model.py

import os
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from datetime import datetime
import sqlite3

# Define o caminho base
try:
    base_dir = Path(os.environ.get("_MEIPASS", Path.cwd()))
except Exception:
    base_dir = Path.cwd()

# FUNÇÃO PARA LER/ESCREVER NO CONFIG.JSON
CONFIG_FILE = base_dir / "utils" / "json" / "config.json"

def load_config():
    """Carrega as configurações do arquivo JSON."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config.json: {e}")
    return {}

def save_config(config_data):
    """Salva as configurações no arquivo JSON."""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar config.json: {e}")
        return False

def get_db_path_from_config():
    """Retorna o caminho do banco de dados do config.json ou o padrão."""
    config = load_config()
    db_path_str = config.get("db_path_atas")

    if db_path_str:
        custom_path = Path(db_path_str)
        if custom_path.is_dir():
            return custom_path / "atas_controle.db"
        elif custom_path.suffix == '.db':
            return custom_path
        else:
            return custom_path / "atas_controle.db"

    DATABASE_DIR = base_dir / "database"
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return DATABASE_DIR / "atas_controle.db"

# CARREGA O CAMINHO DO DB DO CONFIG
DB_PATH = get_db_path_from_config()
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuração do SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StatusAta(Base):
    __tablename__ = "status_atas"
    ata_parecer = Column(String, ForeignKey("atas.contrato_ata_parecer"), primary_key=True)
    status = Column(String)
    ata = relationship("Ata", back_populates="status_info")

class RegistroAta(Base):
    __tablename__ = "registros_atas"
    id = Column(Integer, primary_key=True, index=True)
    ata_parecer = Column(String, ForeignKey("atas.contrato_ata_parecer"), nullable=False) 
    texto = Column(Text, nullable=False)
    ata = relationship("Ata", back_populates="registros")

class LinksAta(Base):
    __tablename__ = "links_ata"
    id = Column(Integer, primary_key=True)
    ata_parecer = Column(String, ForeignKey("atas.contrato_ata_parecer"), nullable=False, unique=True)
    serie_ata_link = Column(String)
    portaria_link = Column(String)
    ta_link = Column(String)
    portal_licitacoes_link = Column(String) 
    ata = relationship("Ata", back_populates="links")

class FiscalizacaoAta(Base):
    """Tabela específica para armazenar dados de fiscalização de atas."""
    __tablename__ = "fiscalizacao_atas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ata_parecer = Column(String, ForeignKey("atas.contrato_ata_parecer"), nullable=False, unique=True, index=True)
    gestor = Column(String)
    gestor_substituto = Column(String)
    fiscal_tecnico = Column(String)
    fiscal_tec_substituto = Column(String)
    fiscal_administrativo = Column(String)
    fiscal_admin_substituto = Column(String)
    observacoes = Column(Text)
    data_criacao = Column(String)
    data_atualizacao = Column(String)

    ata = relationship("Ata", back_populates="fiscalizacao_info")

class Ata(Base):
    __tablename__ = "atas"
    id = Column(Integer, primary_key=True, index=True)
    setor = Column(String)
    modalidade = Column(String)
    numero = Column(String)
    ano = Column(String)
    empresa = Column(String)
    contrato_ata_parecer = Column(String, unique=True, index=True)
    objeto = Column(Text)
    celebracao = Column(String)
    termino = Column(String)
    observacoes = Column(Text)
    termo_aditivo = Column(String)
    portaria_fiscalizacao = Column(String)
    nup = Column(String) 
    status_info = relationship("StatusAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")
    links = relationship("LinksAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")
    registros = relationship("RegistroAta", back_populates="ata", cascade="all, delete-orphan")
    fiscalizacao_info = relationship("FiscalizacaoAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")

class AtaData:
    def __init__(self, ata_db_object):
        self.id = ata_db_object.id
        self.setor = ata_db_object.setor
        self.modalidade = ata_db_object.modalidade
        self.numero = ata_db_object.numero
        self.ano = ata_db_object.ano
        self.empresa = ata_db_object.empresa
        self.contrato_ata_parecer = ata_db_object.contrato_ata_parecer
        self.objeto = ata_db_object.objeto
        self.celebracao = ata_db_object.celebracao
        self.termino = ata_db_object.termino
        self.observacoes = ata_db_object.observacoes
        self.portaria_fiscalizacao = ata_db_object.portaria_fiscalizacao
        self.termo_aditivo = ata_db_object.termo_aditivo
        self.nup = ata_db_object.nup 
        self.status = ata_db_object.status_info.status if ata_db_object.status_info else "SEÇÃO ATAS"
        self.registros = [reg.texto for reg in ata_db_object.registros] if ata_db_object.registros else []
        self.serie_ata_link = ata_db_object.links.serie_ata_link if ata_db_object.links else ""
        self.portaria_link = ata_db_object.links.portaria_link if ata_db_object.links else ""
        self.ta_link = ata_db_object.links.ta_link if ata_db_object.links else ""
        self.portal_licitacoes_link = ata_db_object.links.portal_licitacoes_link if ata_db_object.links else ""

        self.fiscalizacao = None
        if ata_db_object.fiscalizacao_info:
            f = ata_db_object.fiscalizacao_info
            self.fiscalizacao = {
                "gestor": f.gestor or "",
                "gestor_substituto": f.gestor_substituto or "",
                "fiscal_tecnico": f.fiscal_tecnico or "",
                "fiscal_tec_substituto": f.fiscal_tec_substituto or "",
                "fiscal_administrativo": f.fiscal_administrativo or "",
                "fiscal_admin_substituto": f.fiscal_admin_substituto or "",
                "observacoes": f.observacoes or "",
                "data_criacao": f.data_criacao or "",
                "data_atualizacao": f.data_atualizacao or ""
            }

class AtasModel:
    def __init__(self):
        self.db_initialized = False # Flag para indicar se o DB foi inicializado com sucesso
        self._initialize_db()

    def _initialize_db(self):
        """Inicializa o banco de dados, verificando e criando o schema."""
        global engine, SessionLocal, DB_PATH, DATABASE_URL

        self.allow_raw_export = False  # nova flag

        if not DB_PATH.exists():
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            Base.metadata.create_all(bind=engine)
            print(f"✅ Novo banco de dados criado em: {DB_PATH}")
            self.db_initialized = True
            self.allow_raw_export = True
            return

        try:
            inspector = inspect(engine)
            if "atas" in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns("atas")]
                if "nup" not in cols:
                    raise ValueError("Coluna 'nup' ausente na tabela 'atas'.")
            else:
                raise ValueError("Tabela 'atas' ausente.")

            if "links_ata" in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns("links_ata")]
                if "portal_licitacoes_link" not in cols:
                    raise ValueError("Coluna 'portal_licitacoes_link' ausente.")
            else:
                raise ValueError("Tabela 'links_ata' ausente.")

            self.db_initialized = True
            self.allow_raw_export = True
            print(f"✅ Schema OK(local do BD de atas) em: {DB_PATH}")

        except Exception as e:
            print(f"⚠️ Schema desatualizado: {e}")
            # DB antigo, mas ainda válido para leitura via sqlite3
            self.db_initialized = False
            self.allow_raw_export = True


    def _get_session(self, allow_uninitialized=False): # ✨ Adicionado parâmetro allow_uninitialized
        if not self.db_initialized and not allow_uninitialized: # ✨ Condição modificada
            raise RuntimeError("Banco de dados não inicializado ou schema desatualizado. Não é possível obter sessão.")
        return SessionLocal()

    def get_current_db_path(self):
        return DB_PATH

    def change_database_path(self, new_folder_path: str):
        global engine, SessionLocal, DB_PATH, DATABASE_URL

        try:
            new_path_obj = Path(new_folder_path) / "atas_controle.db"
            new_path_obj.parent.mkdir(parents=True, exist_ok=True)

            config = load_config()
            config["db_path_atas"] = str(new_folder_path)
            if not save_config(config):
                print("⚠️ Aviso: Não foi possível salvar no config.json")

            engine.dispose()

            DB_PATH = new_path_obj
            DATABASE_URL = f"sqlite:///{DB_PATH}"

            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            Base.metadata.create_all(bind=engine) # Ao mudar o DB, sempre tentamos criar o schema mais recente

            print(f"✅ Banco de dados alterado para: {DB_PATH}")
            print(f"✅ Configuração salva em: {CONFIG_FILE}")
            self.db_initialized = True # Assumimos que o novo DB está com o schema correto
            return True

        except Exception as e:
            print(f"❌ Erro ao alterar o banco de dados: {e}")
            self.db_initialized = False
            return False

    # --- NOVAS FUNÇÕES DE EXPORTAÇÃO/IMPORTAÇÃO JSON ---

    def export_main_data_to_json(self):
        """Exporta os dados principais (tabela 'atas') direto via sqlite3, compatível com bancos antigos."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # --- Obtém colunas disponíveis no banco ---
            cursor.execute("PRAGMA table_info(atas);")
            columns = [col[1] for col in cursor.fetchall()]

            if not columns:
                return False, "Tabela 'atas' não encontrada no banco."

            cursor.execute(f"SELECT * FROM atas;")
            rows = cursor.fetchall()

            # Exporta em formato [{coluna: valor}, ...]
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                data.append(record)

            conn.close()
            print(f"✅ Exportação RAW de {len(data)} atas concluída via sqlite3.")
            return True, data

        except Exception as e:
            print(f"❌ Erro ao exportar dados principais via sqlite3: {e}")
            return False, str(e)

    def export_complementary_data_to_json(self):
        """Exporta as tabelas complementares via sqlite3 (status_atas, registros_atas e links_ata)."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            data = {}

            # --- STATUS_ATAS ---
            try:
                cursor.execute("PRAGMA table_info(status_atas);")
                colunas = [c[1] for c in cursor.fetchall()]
                if colunas:
                    cursor.execute("SELECT * FROM status_atas;")
                    data["status_atas"] = [dict(zip(colunas, r)) for r in cursor.fetchall()]
            except Exception as e:
                print("Tabela status_atas ausente:", e)
                data["status_atas"] = []

            # --- REGISTROS_ATAS ---
            try:
                cursor.execute("PRAGMA table_info(registros_atas);")
                colunas = [c[1] for c in cursor.fetchall()]
                if colunas:
                    cursor.execute("SELECT * FROM registros_atas;")
                    data["registros_atas"] = [dict(zip(colunas, r)) for r in cursor.fetchall()]
            except Exception as e:
                print("Tabela registros_atas ausente:", e)
                data["registros_atas"] = []

            # --- LINKS_ATA ---
            try:
                cursor.execute("PRAGMA table_info(links_ata);")
                colunas = [c[1] for c in cursor.fetchall()]
                if colunas:
                    cursor.execute("SELECT * FROM links_ata;")
                    data["links_ata"] = [dict(zip(colunas, r)) for r in cursor.fetchall()]
            except Exception as e:
                print("Tabela links_ata ausente:", e)
                data["links_ata"] = []

            # --- FISCALIZAÇÃO_ATA ---
            try:
                cursor.execute("PRAGMA table_info(fiscalizacao_atas);")
                columns = [col[1] for col in cursor.fetchall()]
                if columns:
                    cursor.execute("SELECT * FROM fiscalizacao_atas;")
                    rows = cursor.fetchall()
                    data["fiscalizacao_atas"] = [dict(zip(columns, row)) for row in rows]
                else:
                    data["fiscalizacao_atas"] = []
            except Exception as e:
                print(f"[Aviso] Erro ao exportar 'fiscalizacao_atas': {e}")
                data["fiscalizacao_atas"] = []

            conn.close()
            print(f"✅ Exportação RAW das tabelas complementares concluída.")
            return True, data

        except Exception as e:
            print(f"❌ Erro ao exportar dados complementares via sqlite3: {e}")
            return False, str(e)

    def import_main_data_from_json(self, file_path: str):
        """Importa os dados da tabela principal (Atas) de um arquivo JSON."""
        session = self._get_session() # Não permitir sessão se schema desatualizado
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            session.query(Ata).delete() # Limpa a tabela Ata antes de importar

            for record in data:
                # Filtra chaves para corresponder às colunas da Ata
                valid_record = {k: v for k, v in record.items() if hasattr(Ata, k)}
                new_ata = Ata(**valid_record)
                session.add(new_ata)

            session.commit()
            return True, f"{len(data)} atas principais importadas com sucesso."
        except Exception as e:
            session.rollback()
            print(f"Erro ao importar dados principais: {e}")
            return False, f"Erro ao importar dados principais: {e}"
        finally:
            session.close()

    def import_complementary_data_from_json(self, file_path: str):
        """Importa dados complementares (Status, Registros, Links) de um arquivo JSON."""
        session = self._get_session() # Não permitir sessão se schema desatualizado
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Limpa as tabelas complementares antes de importar
            session.query(StatusAta).delete()
            session.query(RegistroAta).delete()
            session.query(LinksAta).delete()

            imported_count = 0

            # Importar StatusAta
            for record in data.get("status_atas", []):
                if session.query(Ata).filter(Ata.contrato_ata_parecer == record["ata_parecer"]).first():
                    new_status = StatusAta(ata_parecer=record["ata_parecer"], status=record["status"])
                    session.add(new_status)
                    imported_count += 1
                else:
                    print(f"Aviso: Ata principal '{record['ata_parecer']}' não encontrada para status. Ignorando.")

            # Importar RegistroAta
            for record in data.get("registros_atas", []):
                if session.query(Ata).filter(Ata.contrato_ata_parecer == record["ata_parecer"]).first():
                    new_registro = RegistroAta(ata_parecer=record["ata_parecer"], texto=record["texto"])
                    session.add(new_registro)
                    imported_count += 1
                else:
                    print(f"Aviso: Ata principal '{record['ata_parecer']}' não encontrada para registro. Ignorando.")

            # Importar LinksAta
            for record in data.get("links_ata", []):
                if session.query(Ata).filter(Ata.contrato_ata_parecer == record["ata_parecer"]).first():
                    new_links = LinksAta(
                        ata_parecer=record["ata_parecer"],
                        serie_ata_link=record.get("serie_ata_link", ""),
                        portaria_link=record.get("portaria_link", ""),
                        ta_link=record.get("ta_link", ""),
                        portal_licitacoes_link=record.get("portal_licitacoes_link", "") 
                    )
                    session.add(new_links)
                    imported_count += 1
                else:
                    print(f"Aviso: Ata principal '{record['ata_parecer']}' não encontrada para links. Ignorando.")
            
            # Importar FiscalizacaoAta
            for record in data.get("fiscalizacao_atas", []):
                if session.query(Ata).filter(Ata.contrato_ata_parecer == record["ata_parecer"]).first():
                    fiscal = FiscalizacaoAta(
                        ata_parecer=record["ata_parecer"],
                        gestor=record.get("gestor", ""),
                        gestor_substituto=record.get("gestor_substituto", ""),
                        fiscal_tecnico=record.get("fiscal_tecnico", ""),
                        fiscal_tec_substituto=record.get("fiscal_tec_substituto", ""),
                        fiscal_administrativo=record.get("fiscal_administrativo", ""),
                        fiscal_admin_substituto=record.get("fiscal_admin_substituto", ""),
                        observacoes=record.get("observacoes", ""),
                        data_criacao=record.get("data_criacao", ""),
                        data_atualizacao=record.get("data_atualizacao", "")
                    )
                    session.add(fiscal)
                    imported_count += 1
                else:
                    print(f"Aviso: Ata '{record['ata_parecer']}' não encontrada para fiscalização. Ignorando.")

            session.commit()
            return True, f"{imported_count} dados complementares importados com sucesso."
        except Exception as e:
            session.rollback()
            print(f"Erro ao importar dados complementares: {e}")
            return False, f"Erro ao importar dados complementares: {e}"
        finally:
            session.close()

    def get_all_atas(self):
        session = self._get_session() 
        try:
            atas = session.query(Ata).options(
                joinedload(Ata.links), 
                joinedload(Ata.status_info)
            ).all()
            atas_ordenadas = sorted(
                atas, 
                key=lambda x: datetime.strptime(x.termino, '%Y-%m-%d') if x.termino else datetime.min
            )
            return atas_ordenadas
        except Exception as e:
            print(f"Erro ao carregar atas: {e}")
            return []
        finally:
            session.close()

    def get_ata_by_parecer(self, parecer_value):
        session = self._get_session() 
        try:
            ata = session.query(Ata).filter(Ata.contrato_ata_parecer == parecer_value).first()
            return AtaData(ata) if ata else None
        finally:
            session.close()

    def add_ata(self, ata_data):
        session = self._get_session() 
        try:
            ata_cols = {c.name for c in Ata.__table__.columns}
            filtered_data = {k: v for k, v in ata_data.items() if k in ata_cols}
            nova_ata = Ata(**filtered_data)
            session.add(nova_ata)
            session.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar ata: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_ata(self, parecer_value: str):
        session = self._get_session() 
        try:
            ata = session.query(Ata).filter(Ata.contrato_ata_parecer == parecer_value).first()
            if ata:
                session.delete(ata)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def update_ata(self, parecer_value, updated_data, registros_list):
        session = self._get_session() 
        try:
            ata = session.query(Ata).filter(Ata.contrato_ata_parecer == parecer_value).first()
            if ata:
                # Define as chaves que são RELACIONAMENTOS e não devem ser salvas por este loop
                relationship_keys = ['status_info', 'links', 'registros', 'fiscalizacao_info', 'registros_mensagem', 'fiscalizacao']
                
                # Este loop agora define APENAS os atributos de coluna simples.
                for key, value in updated_data.items():
                    # Pula chaves que são relacionamentos ou que não existem no modelo Ata
                    if key in relationship_keys or not hasattr(ata, key):
                        continue
                    
                    # Define o valor da coluna
                    setattr(ata, key, str(value) if value is not None else '')

                if not ata.links:
                    ata.links = LinksAta()
                ata.links.serie_ata_link = updated_data.get('serie_ata_link', '')
                ata.links.portaria_link = updated_data.get('portaria_link', '')
                ata.links.ta_link = updated_data.get('ta_link', '')
                ata.links.portal_licitacoes_link = updated_data.get('portal_licitacoes_link', '')

                if not ata.status_info:
                    ata.status_info = StatusAta(ata_parecer=parecer_value)
                ata.status_info.status = updated_data.get('status', 'SEÇÃO ATAS')

                session.query(RegistroAta).filter(RegistroAta.ata_parecer == parecer_value).delete(synchronize_session=False)
                for texto in registros_list:
                    session.add(RegistroAta(ata_parecer=parecer_value, texto=texto))

                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Erro ao atualizar ata: {e}")
            return False
        finally:
            session.close()

    def import_from_spreadsheet(self, file_path: str):
        session = self._get_session() 
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            column_mapping = {
                'SETOR': 'setor', 'MODALIDADE': 'modalidade', 'Nº/': 'numero',
                'ANO': 'ano', 'EMPRESA': 'empresa', 'CONTRATO – ATA PARECER': 'contrato_ata_parecer',
                'OBJETO': 'objeto', 'CELEBRAÇÃO': 'celebracao', 'TERMO ADITIVO': 'termo_aditivo',
                'PORTARIA DE FISCALIZAÇÃO': 'portaria_fiscalizacao', 'TERMINO': 'termino',
                'OBSERVAÇÕES': 'observacoes'
            }
            df.rename(columns=column_mapping, inplace=True)
            for date_col in ['celebracao', 'termino']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
            df = df.fillna('')

            try:
                session.query(Ata).delete()
                df = df[df['empresa'].astype(str).str.strip() != '']
                for record in df.to_dict(orient='records'):
                    valid_record = {key: str(value) if value is not None else '' for key, value in record.items() if hasattr(Ata, key)}
                    ata_obj = Ata(**valid_record)
                    session.add(ata_obj)
                session.commit()
                return True, f"{len(df)} registros importados com sucesso."
            except Exception as e:
                session.rollback()
                return False, f"Erro ao salvar no banco de dados: {e}"
            finally:
                session.close()
        except Exception as e:
            return False, f"Erro ao ler o arquivo: {e}"

    def get_atas_with_status_not_default(self):
        session = self._get_session() 
        try:
            atas_com_status = session.query(Ata).join(Ata.status_info).filter(
                StatusAta.status != 'SEÇÃO ATAS'
            ).options(
                joinedload(Ata.status_info)
            ).all()
            atas_ordenadas = sorted(
                atas_com_status,
                key=lambda x: datetime.strptime(x.termino, '%Y-%m-%d') if x.termino else datetime.min
            )
            return atas_ordenadas
        except Exception as e:
            print(f"Erro ao buscar atas com status: {e}")
            return []
        finally:
            session.close()
