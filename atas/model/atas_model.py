# atas/model/atas_model.py
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# Define o caminho base para encontrar a pasta 'database'
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

# Modelo da Tabela 'Atas'
class Ata(Base):
    __tablename__ = "atas"
    id = Column(Integer, primary_key=True, index=True)
    setor = Column(String)
    modalidade = Column(String)
    numero = Column(String)
    ano = Column(String)
    empresa = Column(String)
    contrato_ata_parecer = Column(String)
    objeto = Column(Text)
    celebracao = Column(String)
    termino = Column(Date)
    observacoes = Column(Text)
    termo_aditivo = Column(String)
    portaria_fiscalizacao = Column(String)

class AtasModel:
    def __init__(self):
        Base.metadata.create_all(bind=engine)
        print(f"✅ Banco de dados de Atas inicializado em: {DB_PATH}")

    def _get_session(self):
        return SessionLocal()

    def get_all_atas(self):
        session = self._get_session()
        try:
            atas = session.query(Ata).order_by(Ata.termino.asc()).all() # Ordena por data de término
            return atas
        finally:
            session.close()

    def import_from_spreadsheet(self, file_path: str):
        try:
            engine = 'odf' if file_path.lower().endswith('.ods') else 'openpyxl'
            
            # --- CORREÇÃO APLICADA AQUI ---
            # Removemos header=8. O padrão (header=0) lê a primeira linha como cabeçalho.
            df = pd.read_excel(file_path, engine=engine)

            # Renomeia as colunas
            column_mapping = {
                'SETOR': 'setor', 'MODALIDADE': 'modalidade', 'N°': 'numero', 'ANO': 'ano',
                'EMPRESA': 'empresa', 'CONTRATO - ATA PARECER': 'contrato_ata_parecer',
                'OBJETO': 'objeto', 'CELEBRAÇÃO': 'celebracao', 'TERMO ADITIVO': 'termo_aditivo',
                'PORTARIA DE FISCALIZAÇÃO': 'portaria_fiscalizacao', 
                'TERMINO': 'termino', # Nome da coluna atualizado
                'OBSERVAÇÕES': 'observacoes'
            }
            df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
            
            # Converte a coluna 'termino' para datetime
            if 'termino' in df.columns:
                df['termino'] = pd.to_datetime(df['termino'], dayfirst=True, errors='coerce').dt.date

            session = self._get_session()
            try:
                session.query(Ata).delete()
                
                for record in df.to_dict(orient='records'):
                    valid_record = {key: value for key, value in record.items() if hasattr(Ata, key)}
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

    def add_ata(self, ata_data: dict):
        session = self._get_session()
        try:
            nova_ata = Ata(**ata_data)
            session.add(nova_ata)
            session.commit()
            return nova_ata.id
        finally:
            session.close()

    def delete_ata(self, ata_id: int):
        session = self._get_session()
        try:
            ata_to_delete = session.query(Ata).filter(Ata.id == ata_id).first()
            if ata_to_delete:
                session.delete(ata_to_delete)
                session.commit()
                return True
            return False
        finally:
            session.close()
