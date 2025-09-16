# model/models.py

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Uasg(Base):
    __tablename__ = "uasgs"

    uasg_code = Column(String, primary_key=True, index=True)
    nome_resumido = Column(String)

    # O cascade="all, delete-orphan" garante que ao deletar uma UASG,
    # todos os seus contratos e dados associados sejam deletados juntos.
    contratos = relationship("Contrato", back_populates="uasg", cascade="all, delete-orphan")

class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(String, primary_key=True, index=True)
    
    uasg_code = Column(String, ForeignKey("uasgs.uasg_code"), nullable=False)
    
    numero = Column(String)
    licitacao_numero = Column(String)
    processo = Column(String)
    fornecedor_nome = Column(String)
    fornecedor_cnpj = Column(String)
    objeto = Column(Text)
    valor_global = Column(String)
    vigencia_inicio = Column(String)
    vigencia_fim = Column(String)
    tipo = Column(String)
    modalidade = Column(String)
    contratante_orgao_unidade_gestora_codigo = Column(String)
    contratante_orgao_unidade_gestora_nome_resumido = Column(String)
    raw_json = Column(Text)

    # --- RELACIONAMENTOS ---
    uasg = relationship("Uasg", back_populates="contratos")
    status = relationship("StatusContrato", back_populates="contrato", uselist=False, cascade="all, delete-orphan")
    registros = relationship("RegistroStatus", back_populates="contrato", cascade="all, delete-orphan")
    #comentarios = relationship("ComentarioStatus", back_populates="contrato", cascade="all, delete-orphan")
    
    # Relacionamentos para dados offline
    historicos = relationship("Historico", back_populates="contrato", cascade="all, delete-orphan")
    empenhos = relationship("Empenho", back_populates="contrato", cascade="all, delete-orphan")
    itens = relationship("Item", back_populates="contrato", cascade="all, delete-orphan")
    arquivos = relationship("Arquivo", back_populates="contrato", cascade="all, delete-orphan")

# --- MODELOS PARA DADOS OFFLINE ---
class Historico(Base):
    __tablename__ = "historico"
    id = Column(Integer, primary_key=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    raw_json = Column(Text)
    contrato = relationship("Contrato", back_populates="historicos")

class Empenho(Base):
    __tablename__ = "empenhos"
    id = Column(Integer, primary_key=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    raw_json = Column(Text)
    contrato = relationship("Contrato", back_populates="empenhos")

class Item(Base):
    __tablename__ = "itens"
    id = Column(Integer, primary_key=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    raw_json = Column(Text)
    contrato = relationship("Contrato", back_populates="itens")

class Arquivo(Base):
    __tablename__ = "arquivos"
    id = Column(Integer, primary_key=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    raw_json = Column(Text)
    contrato = relationship("Contrato", back_populates="arquivos")

# --- MODELOS DE STATUS (sem alterações) ---
class StatusContrato(Base):
    __tablename__ = "status_contratos"
    contrato_id = Column(String, ForeignKey("contratos.id"), primary_key=True)
    uasg_code = Column(String)
    status = Column(String)
    objeto_editado = Column(Text)
    portaria_edit = Column(String)
    radio_options_json = Column(Text)
    data_registro = Column(String)
    contrato = relationship("Contrato", back_populates="status")

class RegistroStatus(Base):
    __tablename__ = "registros_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False, index=True)
    uasg_code = Column(String)
    texto = Column(Text, unique=True)
    contrato = relationship("Contrato", back_populates="registros")

"""class ComentarioStatus(Base):
    __tablename__ = "comentarios_status"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    uasg_code = Column(String)
    texto = Column(Text, unique=True)
    contrato = relationship("Contrato", back_populates="comentarios")
"""