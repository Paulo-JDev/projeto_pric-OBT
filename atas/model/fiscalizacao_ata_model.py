# atas/model/fiscalizacao_ata_model.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from atas.model.atas_model import Base

class FiscalizacaoAta(Base):
    """
    Tabela para armazenar dados de fiscalização da Ata.
    Relacionamento 1:1 com a tabela de Atas.
    """
    __tablename__ = "fiscalizacao_atas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ata_parecer = Column(String, ForeignKey("atas.contrato_ata_parecer"), nullable=False, unique=True, index=True)

    # ✅ Campos de fiscalização
    gestor = Column(String)
    gestor_substituto = Column(String)
    fiscal_tecnico = Column(String)
    fiscal_tec_substituto = Column(String)
    fiscal_administrativo = Column(String)
    fiscal_admin_substituto = Column(String)
    observacoes = Column(Text)

    # Auditoria
    data_criacao = Column(String)
    data_atualizacao = Column(String)

    # Relacionamento reverso
    ata = relationship("Ata", back_populates="fiscalizacao_info")
