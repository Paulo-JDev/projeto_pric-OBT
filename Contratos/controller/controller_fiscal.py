# Contratos/controller/controller_fiscal.py

"""
Controller para gerenciar dados de fiscalização de contratos.
Responsável por salvar e carregar informações de fiscalização do banco de dados.
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def save_fiscalizacao(model, contrato_id: str, parent_dialog) -> bool:
    """
    Salva dados de fiscalização de um contrato no banco de dados.
    
    Args:
        model: Instância do UASGModel para acesso ao banco
        contrato_id: ID do contrato
        parent_dialog: Instância do DetailsDialog contendo os campos de fiscalização
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
        
    Raises:
        ValueError: Se contrato_id for inválido
    """
    if not contrato_id:
        logger.error("ID do contrato não pode ser vazio ao salvar fiscalização")
        return False
    
    # Coleta dados dos campos do dialog
    fiscalizacao_data = {
        'gestor': getattr(parent_dialog, 'fiscal_gestor', None),
        'fiscal_titular': getattr(parent_dialog, 'fiscal_titular', None),
        'fiscal_substituto': getattr(parent_dialog, 'fiscal_substituto', None),
        'setor_responsavel': getattr(parent_dialog, 'fiscal_setor', None),
        'data_fiscalizacao' : getattr(parent_dialog, 'fiscal_data', None),
        'observacoes': getattr(parent_dialog, 'fiscal_observacoes', None),
        'acoes_corretivas': getattr(parent_dialog, 'fiscal_acoes_corretivas', None)

    }
    
    # Extrai texto dos widgets (QLineEdit ou QTextEdit)
    data_to_save = {}
    for key, widget in fiscalizacao_data.items():
        if widget is None:
            data_to_save[key] = ''
        elif hasattr(widget, 'text'):  # QLineEdit
            data_to_save[key] = widget.text().strip()
        elif hasattr(widget, 'toPlainText'):  # QTextEdit
            data_to_save[key] = widget.toPlainText().strip()
        else:
            data_to_save[key] = ''
    
    try:
        # Chama o método do model para salvar
        _save_fiscalizacao_to_db(model, contrato_id, data_to_save)
        logger.info(f"✅ Dados Gerais salvos para o contrato {contrato_id}")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Erro ao salvar fiscalização do contrato {contrato_id}")
        return False


def load_fiscalizacao(model, contrato_id: str, parent_dialog) -> bool:
    """
    Carrega dados de fiscalização do banco de dados e preenche os campos do dialog.
    
    Args:
        model: Instância do UASGModel para acesso ao banco
        contrato_id: ID do contrato
        parent_dialog: Instância do DetailsDialog contendo os campos de fiscalização
        
    Returns:
        bool: True se carregou dados, False se não havia dados salvos
    """
    if not contrato_id:
        logger.warning("ID do contrato não encontrado para carregar fiscalização")
        return False
    
    try:
        # Busca dados do banco
        fiscalizacao_data = _get_fiscalizacao_from_db(model, contrato_id)
        
        if not fiscalizacao_data:
            logger.debug(f"Nenhum dado de fiscalização encontrado para o contrato {contrato_id}")
            return False
        
        # Preenche os campos do dialog
        _populate_fiscal_fields(parent_dialog, fiscalizacao_data)
        
        logger.info(f"✅ Dados de fiscalização carregados para o contrato {contrato_id}")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar fiscalização do contrato {contrato_id}")
        return False


def _save_fiscalizacao_to_db(model, contrato_id: str, fiscalizacao_data: Dict[str, str]) -> None:
    """
    Salva ou atualiza dados de fiscalização no banco de dados (método interno).
    
    Args:
        model: Instância do UASGModel
        contrato_id: ID do contrato
        fiscalizacao_data: Dicionário com os dados de fiscalização
    """
    from Contratos.model.models import Fiscalizacao
    
    db = model._get_db_session()
    
    try:
        # Busca registro existente ou cria novo
        fiscalizacao = db.query(Fiscalizacao).filter(
            Fiscalizacao.contrato_id == contrato_id
        ).first()
        
        if not fiscalizacao:
            fiscalizacao = Fiscalizacao(contrato_id=contrato_id)
            fiscalizacao.data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            db.add(fiscalizacao)
            logger.debug(f"Criando novo registro de fiscalização para contrato {contrato_id}")
        else:
            logger.debug(f"Atualizando registro de fiscalização existente para contrato {contrato_id}")
        
        # Atualiza os campos
        fiscalizacao.gestor = fiscalizacao_data.get('gestor', '')
        fiscalizacao.fiscal_titular = fiscalizacao_data.get('fiscal_titular', '')
        fiscalizacao.fiscal_substituto = fiscalizacao_data.get('fiscal_substituto', '')
        fiscalizacao.setor_responsavel = fiscalizacao_data.get('setor_responsavel', '')
        fiscalizacao.data_fiscalizacao = fiscalizacao_data.get('data_fiscalizacao', '')
        fiscalizacao.observacoes = fiscalizacao_data.get('observacoes', '')
        fiscalizacao.acoes_corretivas = fiscalizacao_data.get('acoes_corretivas', '')
        fiscalizacao.data_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Erro ao salvar fiscalização no banco: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _get_fiscalizacao_from_db(model, contrato_id: str) -> Optional[Dict[str, str]]:
    """
    Busca dados de fiscalização do banco de dados (método interno).
    
    Args:
        model: Instância do UASGModel
        contrato_id: ID do contrato
        
    Returns:
        Dicionário com os dados ou None se não existir
    """
    from Contratos.model.models import Fiscalizacao
    
    db = model._get_db_session()
    
    try:
        fiscalizacao = db.query(Fiscalizacao).filter(
            Fiscalizacao.contrato_id == contrato_id
        ).first()
        
        if fiscalizacao:
            return {
                'gestor': fiscalizacao.gestor or '',
                'fiscal_titular': fiscalizacao.fiscal_titular or '',
                'fiscal_substituto': fiscalizacao.fiscal_substituto or '',
                'setor_responsavel': fiscalizacao.setor_responsavel or '',
                'data_fiscalizacao': fiscalizacao.data_fiscalizacao or '',
                'observacoes': fiscalizacao.observacoes or '',
                'acoes_corretivas': fiscalizacao.acoes_corretivas or '',
                'data_criacao': fiscalizacao.data_criacao,
                'data_atualizacao': fiscalizacao.data_atualizacao
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar fiscalização do banco: {e}")
        return None
    finally:
        db.close()


def _populate_fiscal_fields(parent_dialog, fiscalizacao_data: Dict[str, str]) -> None:
    """
    Preenche os campos de fiscalização no dialog (método interno).
    
    Args:
        parent_dialog: Instância do DetailsDialog
        fiscalizacao_data: Dicionário com os dados de fiscalização
    """
    # Mapeamento de campos: nome_atributo -> chave_dados
    field_mapping = {
        'fiscal_gestor': 'gestor',
        'fiscal_titular': 'fiscal_titular',
        'fiscal_substituto': 'fiscal_substituto',
        'fiscal_setor': 'setor_responsavel',
        'fiscal_data': 'data_fiscalizacao',
        'fiscal_observacoes': 'observacoes',
        'fiscal_acoes_corretivas': 'acoes_corretivas'
    }
    
    for attr_name, data_key in field_mapping.items():
        widget = getattr(parent_dialog, attr_name, None)
        value = fiscalizacao_data.get(data_key, '')
        
        if widget is None:
            continue
        
        # Preenche conforme o tipo de widget
        if hasattr(widget, 'setText'):  # QLineEdit
            widget.setText(value)
        elif hasattr(widget, 'setPlainText'):  # QTextEdit
            widget.setPlainText(value)
