# model/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Inicializamos as variáveis como None. Elas serão criadas depois.
engine = None
SessionLocal = None

def init_database(db_path: str):
    """
    Inicializa o engine e a sessão do SQLAlchemy com o caminho do banco de dados fornecido.
    Também cria as tabelas se elas não existirem.
    """
    global engine, SessionLocal

    # Se já foi inicializado, não faz nada.
    if engine is not None:
        return

    DATABASE_URL = f"sqlite:///{db_path}"
    
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Importamos os modelos aqui dentro para evitar outros ciclos de importação
    from .models import Base
    print("Verificando e criando tabelas com SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas prontas.")
