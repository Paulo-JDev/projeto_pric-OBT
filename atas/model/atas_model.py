# atas/model/atas_model.py
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Text, func
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

# Modelo da Tabela 'Atas' - Todas as colunas como String
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
    termino = Column(String)  # Mantido como String
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
            # Ordena convertendo a string de data para o formato correto
            atas = session.query(Ata).all()
            # Ordena manualmente após a consulta
            atas_ordenadas = sorted(
                atas, 
                key=lambda x: datetime.strptime(x.termino, '%Y-%m-%d') if x.termino else datetime.min
            )
            
            return atas_ordenadas
        except Exception as e:
            print(f"Erro ao ordenar atas: {e}")
            # Em caso de erro, retorna sem ordenação
            return session.query(Ata).all()
        finally:
            session.close()

    def import_from_spreadsheet(self, file_path: str):
        """Lê uma planilha .xlsx, apaga os dados antigos e insere os novos."""
        try:
            df = pd.read_excel(file_path)

            # Limpa espaços em branco no início/fim dos nomes das colunas
            df.columns = df.columns.str.strip()

            # Mapeamento de colunas mais preciso, exatamente como na sua planilha
            column_mapping = {
                'SETOR': 'setor',
                'MODALIDADE': 'modalidade',
                'Nº/': 'numero',
                'ANO': 'ano',
                'EMPRESA': 'empresa',
                'CONTRATO – ATA PARECER': 'contrato_ata_parecer',
                'OBJETO': 'objeto',
                'CELEBRAÇÃO': 'celebracao',
                'TERMO ADITIVO': 'termo_aditivo',
                'PORTARIA DE FISCALIZAÇÃO': 'portaria_fiscalizacao',
                'TERMINO': 'termino',
                'OBSERVAÇÕES': 'observacoes'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Verificação para garantir que colunas essenciais foram encontradas
            required_columns = ['termino', 'empresa', 'celebracao']
            for col in required_columns:
                if col not in df.columns:
                    return False, f"Erro: Coluna '{col}' não encontrada. Verifique a planilha."

            # Converte as colunas de data para string (formato YYYY-MM-DD)
            for date_col in ['celebracao', 'termino']:
                if date_col in df.columns:
                    # Converte para datetime e depois para string no formato desejado
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Converte NaN para string vazia
            df = df.fillna('')

            session = self._get_session()
            try:
                # Limpa a tabela antes de importar novos dados
                session.query(Ata).delete()
                
                # Remove linhas onde a coluna 'empresa' está vazia
                df = df[df['empresa'].astype(str).str.strip() != '']

                for record in df.to_dict(orient='records'):
                    # Filtra apenas as colunas que existem no modelo
                    valid_record = {}
                    for key, value in record.items():
                        if hasattr(Ata, key):
                            # Garante que o valor é string
                            if value is None:
                                valid_record[key] = ''
                            else:
                                valid_record[key] = str(value)
                    
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
        # Implementação futura
        pass

    def delete_ata(self, ata_id: int):
        # Implementação futura
        pass
