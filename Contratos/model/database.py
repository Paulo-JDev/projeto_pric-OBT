# model/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

Base = declarative_base()

# 1. Inicializamos as variáveis como None. Elas serão criadas depois.
engine = None
SessionLocal = None

def init_database(db_path: Path):
    """
    Inicializa ou reinicializa o banco de dados.
    
    ✅ ATUALIZADO: Permite reconfiguração dinâmica do caminho
    """
    global engine, SessionLocal
    
    DATABASE_URL = f"sqlite:///{db_path}"
    
    # Fecha engine anterior se existir
    if engine:
        engine.dispose()
    
    # Cria nova engine
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Cria nova session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Importa os modelos e cria as tabelas
    from .models import Base
    Base.metadata.create_all(bind=engine)
    
    #print(f"📦 Database inicializado: {db_path}")
