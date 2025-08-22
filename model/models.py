# Aqui vamos definir as classes Python que representarão as suas tabelas (Contratos, StatusContratos, RegistrosStatus, etc.).
# model/models.py

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Base é uma classe que nossas classes de modelo herdarão.
Base = declarative_base()

class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(String, primary_key=True, index=True)
    uasg_code = Column(String, nullable=False)
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

    # Relacionamentos (informam ao SQLAlchemy como as tabelas se conectam)
    status = relationship("StatusContrato", back_populates="contrato", uselist=False)
    registros = relationship("RegistroStatus", back_populates="contrato")
    comentarios = relationship("ComentarioStatus", back_populates="contrato")

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
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    uasg_code = Column(String)
    texto = Column(Text, unique=True)

    contrato = relationship("Contrato", back_populates="registros")

class ComentarioStatus(Base):
    __tablename__ = "comentarios_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contrato_id = Column(String, ForeignKey("contratos.id"), nullable=False)
    uasg_code = Column(String)
    texto = Column(Text, unique=True)
    
    contrato = relationship("Contrato", back_populates="comentarios")

# UASG e outras tabelas podem ser adicionadas aqui se necessário