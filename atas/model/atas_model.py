# atas/model/atas_model.py

import os
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from datetime import datetime

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
    # ✨ NOVA COLUNA ADICIONADA ✨
    portal_licitacoes_link = Column(String) 
    ata = relationship("Ata", back_populates="links")

# Modelo da Tabela 'Atas' com o relacionamento
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
    # ✨ NOVA COLUNA ADICIONADA ✨
    nup = Column(String) 
    status_info = relationship("StatusAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")
    links = relationship("LinksAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")
    registros = relationship("RegistroAta", back_populates="ata", cascade="all, delete-orphan")

# Classe de dados para transferência de informações
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
        # ✨ NOVA COLUNA ADICIONADA ✨
        self.nup = ata_db_object.nup 
        self.status = ata_db_object.status_info.status if ata_db_object.status_info else "SEÇÃO ATAS"
        self.registros = [reg.texto for reg in ata_db_object.registros] if ata_db_object.registros else []
        self.serie_ata_link = ata_db_object.links.serie_ata_link if ata_db_object.links else ""
        self.portaria_link = ata_db_object.links.portaria_link if ata_db_object.links else ""
        self.ta_link = ata_db_object.links.ta_link if ata_db_object.links else ""
        # ✨ NOVA COLUNA ADICIONADA ✨
        self.portal_licitacoes_link = ata_db_object.links.portal_licitacoes_link if ata_db_object.links else ""

class AtasModel:
    def __init__(self):
        self.db_initialized = False # Flag para indicar se o DB foi inicializado com sucesso
        self._initialize_db()
        
    def _initialize_db(self):
        """Inicializa o banco de dados, verificando e criando o schema."""
        global engine, SessionLocal, DB_PATH, DATABASE_URL

        # Se o arquivo do DB não existe, ele será criado com o schema mais recente
        if not DB_PATH.exists():
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            Base.metadata.create_all(bind=engine)
            print(f"✅ Novo banco de dados criado em: {DB_PATH}")
            self.db_initialized = True
            return

        # Se o DB existe, verifica o schema
        try:
            # Tenta criar todas as tabelas. SQLAlchemy não recria se já existem,
            # mas pode adicionar colunas se o DB for SQLite e a engine for configurada para isso
            # (o que não é o caso padrão para colunas novas, apenas para tabelas novas)
            Base.metadata.create_all(bind=engine) 

            # Agora, verificamos se as colunas esperadas existem
            inspector = inspect(engine)

            # Verificar tabela 'atas'
            if 'atas' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('atas')]
                if 'nup' not in columns:
                    raise ValueError("Coluna 'nup' ausente na tabela 'atas'. Schema desatualizado.")
            else:
                raise ValueError("Tabela 'atas' ausente. Schema desatualizado.")

            # Verificar tabela 'links_ata'
            if 'links_ata' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('links_ata')]
                if 'portal_licitacoes_link' not in columns:
                    raise ValueError("Coluna 'portal_licitacoes_link' ausente na tabela 'links_ata'. Schema desatualizado.")
            else:
                # Se a tabela links_ata não existe, o schema está desatualizado
                raise ValueError("Tabela 'links_ata' ausente. Schema desatualizado.")

            print(f"✅ Banco de dados de Atas inicializado em: {DB_PATH} (Schema OK)")
            self.db_initialized = True

        except ValueError as ve:
            print(f"❌ Erro de schema: {ve}")
            print("⚠️ O banco de dados está desatualizado. É necessário migrar os dados.")
            self.db_initialized = False # Indica que o DB não está pronto para uso direto
            # Não chamamos QMessageBox aqui, o Controller fará isso.
        except Exception as e:
            print(f"❌ Erro inesperado ao inicializar o DB: {e}")
            self.db_initialized = False

    def _get_session(self):
        if not self.db_initialized:
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

            # Ao mudar o DB, sempre tentamos criar o schema mais recente
            Base.metadata.create_all(bind=engine) 

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
        """Exporta os dados da tabela principal (Atas) para JSON."""
        session = self._get_session()
        try:
            atas = session.query(Ata).all()
            data = []
            for ata in atas:
                ata_dict = {
                    "setor": ata.setor,
                    "modalidade": ata.modalidade,
                    "numero": ata.numero,
                    "ano": ata.ano,
                    "empresa": ata.empresa,
                    "contrato_ata_parecer": ata.contrato_ata_parecer,
                    "objeto": ata.objeto,
                    "celebracao": ata.celebracao,
                    "termino": ata.termino,
                    "observacoes": ata.observacoes,
                    "termo_aditivo": ata.termo_aditivo,
                    "portaria_fiscalizacao": ata.portaria_fiscalizacao,
                    "nup": ata.nup # ✨ Exporta a nova coluna
                }
                data.append(ata_dict)
            return True, data
        except Exception as e:
            print(f"Erro ao exportar dados principais: {e}")
            return False, str(e)
        finally:
            session.close()

    def import_main_data_from_json(self, file_path: str):
        """Importa os dados da tabela principal (Atas) de um arquivo JSON."""
        session = self._get_session()
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

    def export_complementary_data_to_json(self):
        """Exporta dados complementares (Status, Registros, Links) para JSON."""
        session = self._get_session()
        try:
            complementary_data = {
                "status_atas": [],
                "registros_atas": [],
                "links_ata": []
            }

            # Exportar StatusAta
            for status_obj in session.query(StatusAta).all():
                complementary_data["status_atas"].append({
                    "ata_parecer": status_obj.ata_parecer,
                    "status": status_obj.status
                })

            # Exportar RegistroAta
            for registro_obj in session.query(RegistroAta).all():
                complementary_data["registros_atas"].append({
                    "ata_parecer": registro_obj.ata_parecer,
                    "texto": registro_obj.texto
                })

            # Exportar LinksAta
            for link_obj in session.query(LinksAta).all():
                complementary_data["links_ata"].append({
                    "ata_parecer": link_obj.ata_parecer,
                    "serie_ata_link": link_obj.serie_ata_link,
                    "portaria_link": link_obj.portaria_link,
                    "ta_link": link_obj.ta_link,
                    "portal_licitacoes_link": link_obj.portal_licitacoes_link # ✨ Exporta a nova coluna
                })

            return True, complementary_data
        except Exception as e:
            print(f"Erro ao exportar dados complementares: {e}")
            return False, str(e)
        finally:
            session.close()

    def import_complementary_data_from_json(self, file_path: str):
        """Importa dados complementares (Status, Registros, Links) de um arquivo JSON."""
        session = self._get_session()
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
                # Verifica se a ata principal existe antes de adicionar o status
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
                        portal_licitacoes_link=record.get("portal_licitacoes_link", "") # ✨ Importa a nova coluna
                    )
                    session.add(new_links)
                    imported_count += 1
                else:
                    print(f"Aviso: Ata principal '{record['ata_parecer']}' não encontrada para links. Ignorando.")

            session.commit()
            return True, f"{imported_count} dados complementares importados com sucesso."
        except Exception as e:
            session.rollback()
            print(f"Erro ao importar dados complementares: {e}")
            return False, f"Erro ao importar dados complementares: {e}"
        finally:
            session.close()


    def get_all_atas(self):
        # Este método agora chamará _get_session(), que verificará self.db_initialized
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
                for key, value in updated_data.items():
                    if hasattr(ata, key):
                        setattr(ata, key, str(value) if value is not None else '')

                ata.nup = updated_data.get('nup', '')

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
        session = self._get_session() # Agora checa db_initialized
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
        session = self._get_session() # Agora checa db_initialized
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
