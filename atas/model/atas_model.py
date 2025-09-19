# atas/model/atas_model.py

import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from datetime import datetime

# Define o caminho base
try:
    base_dir = Path(os.environ.get("_MEIPASS", Path.cwd()))
except Exception:
    base_dir = Path.cwd()

DATABASE_DIR = base_dir / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATABASE_DIR / "atas_controle.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuração do SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- NOVA TABELA PARA REGISTROS ---
class RegistroAta(Base):
    __tablename__ = "registros_atas"
    id = Column(Integer, primary_key=True, index=True)
    # A ligação agora é feita através da coluna de texto, que é única
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
    links = relationship("LinksAta", uselist=False, back_populates="ata", cascade="all, delete-orphan")
    registros = relationship("RegistroAta", back_populates="ata", cascade="all, delete-orphan")

# Classe de dados para transferência de informações
class AtaData:
    def __init__(self, ata_db_object):
        self.id = ata_db_object.id

        # Aba geral
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

        # Aba registros
        self.registros = [reg.texto for reg in ata_db_object.registros] if ata_db_object.registros else []

        # Aba links
        self.serie_ata_link = ata_db_object.links.serie_ata_link if ata_db_object.links else ""
        self.portaria_link = ata_db_object.links.portaria_link if ata_db_object.links else ""
        self.ta_link = ata_db_object.links.ta_link if ata_db_object.links else ""

class AtasModel:
    def __init__(self):
        Base.metadata.create_all(bind=engine)
        print(f"✅ Banco de dados de Atas inicializado em: {DB_PATH}")

    def _get_session(self):
        return SessionLocal()

    def get_all_atas(self):
        session = self._get_session()
        try:
            # --- ALTERAÇÃO AQUI ---
            # options(joinedload(Ata.links)) força o carregamento dos links
            # na mesma consulta, evitando o erro de sessão fechada.
            atas = session.query(Ata).options(joinedload(Ata.links)).all()

            atas_ordenadas = sorted(
                atas, 
                key=lambda x: datetime.strptime(x.termino, '%Y-%m-%d') if x.termino else datetime.min
            )
            return atas_ordenadas
        except Exception as e:
            print(f"Erro ao carregar atas: {e}")
            return [] # Retorna lista vazia em caso de erro
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
                # Atualiza os dados principais da ata
                for key, value in updated_data.items():
                    if hasattr(ata, key):
                        setattr(ata, key, str(value) if value is not None else '')

                # Cria ou atualiza os links
                if not ata.links:
                    ata.links = LinksAta()
                ata.links.serie_ata_link = updated_data.get('serie_ata_link', '')
                ata.links.portaria_link = updated_data.get('portaria_link', '')
                ata.links.ta_link = updated_data.get('ta_link', '')

                # Atualiza os registros
                session.query(RegistroAta).filter(RegistroAta.ata_parecer == parecer_value).delete(synchronize_session=False)
                for texto in registros_list:
                    session.add(RegistroAta(ata_parecer=parecer_value, texto=texto))

                session.commit()
                return True
            return False
        except Exception as e:
            print(f"Erro ao atualizar ata: {e}")
            session.rollback()
            return False
        finally:
            session.close()
                
    def import_from_spreadsheet(self, file_path: str):
        # (Este método permanece igual)
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
            session = self._get_session()
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