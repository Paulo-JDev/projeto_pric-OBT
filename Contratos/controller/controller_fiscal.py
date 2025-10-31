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
        'gestor_substituto': getattr(parent_dialog, 'fiscal_gestor_substituto', None),
        'fiscal_tecnico': getattr(parent_dialog, 'fiscalizacao_tecnico', None),
        'fiscal_tec_substituto': getattr(parent_dialog, 'fiscalizacao_tec_substituto', None),
        'fiscal_administrativo': getattr(parent_dialog, 'fiscalizacao_administrativo', None),
        'fiscal_admin_substituto': getattr(parent_dialog, 'fiscalizacao_admin_substituto', None),
        'observacoes': getattr(parent_dialog, 'fiscal_observacoes', None),

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
        fiscalizacao.gestor_substituto = fiscalizacao_data.get('gestor_substituto', '')
        fiscalizacao.fiscal_tecnico = fiscalizacao_data.get('fiscal_tecnico', '')
        fiscalizacao.fiscal_tec_substituto = fiscalizacao_data.get('fiscal_tec_substituto', '')
        fiscalizacao.fiscal_administrativo = fiscalizacao_data.get('fiscal_administrativo', '')
        fiscalizacao.fiscal_admin_substituto = fiscalizacao_data.get('fiscal_admin_substituto', '')
        fiscalizacao.observacoes = fiscalizacao_data.get('observacoes', '')
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
                'gestor_substituto': fiscalizacao.gestor_substituto or '',
                'fiscal_tecnico': fiscalizacao.fiscal_tecnico or '',
                'fiscal_tec_substituto': fiscalizacao.fiscal_tec_substituto or '',
                'fiscal_administrativo': fiscalizacao.fiscal_administrativo or '',
                'fiscal_admin_substituto': fiscalizacao.fiscal_admin_substituto or '',
                'observacoes': fiscalizacao.observacoes or '',
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
        'fiscal_gestor_substituto': 'gestor_substituto',
        'fiscalizacao_tecnico': 'fiscal_tecnico',            # ✅ CORRIGIDO (invertido)
        'fiscalizacao_tec_substituto': 'fiscal_tec_substituto',  # ✅ CORRIGIDO (invertido)
        'fiscalizacao_administrativo': 'fiscal_administrativo',  # ✅ CORRIGIDO (invertido)
        'fiscalizacao_admin_substituto': 'fiscal_admin_substituto',  # ✅ CORRIGIDO (invertido)
        'fiscal_observacoes': 'observacoes',
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
