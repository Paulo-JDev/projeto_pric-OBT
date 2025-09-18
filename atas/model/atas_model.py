# atas/model/atas_model.py - VERSÃO CORRIGIDA

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

class AtaData:
    """Classe para representar os dados de uma ata."""
    def __init__(self, id, numero, ano, empresa, objeto, contrato_ata_parecer, inicio=None, termino=None, observacoes=None):
        self.id = id
        self.numero = numero
        self.ano = ano
        self.empresa = empresa
        self.objeto = objeto
        self.contrato_ata_parecer = contrato_ata_parecer
        self.inicio = inicio
        self.termino = termino
        self.observacoes = observacoes or ""

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

    def add_ata(self, ata_data):
        """Adiciona uma nova ata ao banco de dados usando SQLAlchemy."""
        session = self._get_session()
        try:
            # Cria um novo objeto Ata
            nova_ata = Ata(
                numero=str(ata_data['numero']),
                ano=str(ata_data['ano']),
                empresa=str(ata_data['empresa']),
                objeto=str(ata_data['objeto']),
                contrato_ata_parecer=str(ata_data['contrato_ata_parecer']),
                celebracao=ata_data.get('inicio', ''),  # celebracao = inicio
                termino=ata_data.get('termino', ''),
                observacoes=str(ata_data.get('observacoes', '')),
                # Campos opcionais que podem ser preenchidos depois
                setor='',
                modalidade='',
                termo_aditivo='',
                portaria_fiscalizacao=''
            )
            
            session.add(nova_ata)
            session.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar ata: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_ata_by_id(self, ata_id):
        """Busca uma ata específica pelo ID usando SQLAlchemy."""
        session = self._get_session()
        try:
            ata = session.query(Ata).filter(Ata.id == ata_id).first()
            
            if ata:
                return AtaData(
                    id=ata.id,
                    numero=ata.numero,
                    ano=ata.ano,
                    empresa=ata.empresa,
                    objeto=ata.objeto,
                    contrato_ata_parecer=ata.contrato_ata_parecer,
                    inicio=ata.celebracao,  # celebracao = inicio
                    termino=ata.termino,
                    observacoes=ata.observacoes
                )
            return None
            
        except Exception as e:
            print(f"Erro ao buscar ata por ID: {e}")
            return None
        finally:
            session.close()

    def get_ata_by_parecer(self, parecer_value):
        """Busca uma ata específica pelo valor do campo contrato_ata_parecer."""
        session = self._get_session()
        try:
            ata = session.query(Ata).filter(Ata.contrato_ata_parecer == parecer_value).first()
            if ata:
                return AtaData(
                    id=ata.id, numero=ata.numero, ano=ata.ano, empresa=ata.empresa,
                    objeto=ata.objeto, contrato_ata_parecer=ata.contrato_ata_parecer,
                    inicio=ata.celebracao, termino=ata.termino, observacoes=ata.observacoes
                )
            return None
        except Exception as e:
            print(f"Erro ao buscar ata por parecer: {e}")
            return None
        finally:
            session.close()


    def delete_ata(self, ata_id: int):
        """Exclui uma ata do banco de dados usando SQLAlchemy."""
        session = self._get_session()
        try:
            # Busca a ata pelo ID
            ata = session.query(Ata).filter(Ata.id == ata_id).first()
            
            if ata:
                session.delete(ata)
                session.commit()
                return True
            else:
                print(f"Ata com ID {ata_id} não encontrada")
                return False
                
        except Exception as e:
            print(f"Erro ao excluir ata: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_ata(self, ata_id, updated_data):
        """Atualiza uma ata existente no banco de dados."""
        session = self._get_session()
        try:
            ata = session.query(Ata).filter(Ata.id == ata_id).first()
            
            if ata:
                # Atualiza apenas os campos fornecidos
                for key, value in updated_data.items():
                    if hasattr(ata, key):
                        setattr(ata, key, str(value) if value is not None else '')
                
                session.commit()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Erro ao atualizar ata: {e}")
            session.rollback()
            return False
        finally:
            session.close()