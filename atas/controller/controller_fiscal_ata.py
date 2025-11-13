# atas/controller/controller_fiscal_ata.py
"""
Controller para gerenciamento da aba de Fiscalização da Ata.
Responsável por salvar e carregar dados completos de fiscalização.
"""

from datetime import datetime
from typing import Dict, Optional
import logging
from atas.model.atas_model import FiscalizacaoAta

logger = logging.getLogger(__name__)

def save_fiscalizacao_ata(model, parecer_value: str, parent_dialog) -> bool:
    """Salva dados de fiscalização da Ata no banco de dados."""
    if not parecer_value:
        logger.error("Valor de parecer da Ata está vazio ao salvar fiscalização.")
        return False

    fields = {
        'gestor': getattr(parent_dialog, 'fiscal_gestor', None),
        'gestor_substituto': getattr(parent_dialog, 'fiscal_gestor_substituto', None),
        'fiscal_tecnico': getattr(parent_dialog, 'fiscalizacao_tecnico', None),
        'fiscal_tec_substituto': getattr(parent_dialog, 'fiscalizacao_tec_substituto', None),
        'fiscal_administrativo': getattr(parent_dialog, 'fiscalizacao_administrativo', None),
        'fiscal_admin_substituto': getattr(parent_dialog, 'fiscalizacao_admin_substituto', None),
        'observacoes': getattr(parent_dialog, 'fiscal_observacoes', None),
    }

    data_to_save = {}
    for key, widget in fields.items():
        if widget is None:
            data_to_save[key] = ''
        elif hasattr(widget, 'text'):
            data_to_save[key] = widget.text().strip()
        elif hasattr(widget, 'toPlainText'):
            data_to_save[key] = widget.toPlainText().strip()
        else:
            data_to_save[key] = ''

    try:
        _save_fiscalizacao_to_db(model, parecer_value, data_to_save)
        logger.info(f"✅ Fiscalização salva para a Ata {parecer_value}")
        return True
    except Exception as e:
        logger.exception(f"❌ Erro ao salvar fiscalização da Ata {parecer_value}: {e}")
        return False


def load_fiscalizacao_ata(model, parecer_value: str, parent_dialog) -> bool:
    """Carrega dados de fiscalização da Ata e preenche o diálogo."""
    if not parecer_value:
        return False
    try:
        data = _get_fiscalizacao_from_db(model, parecer_value)
        if not data:
            return False
        _populate_fields(parent_dialog, data)
        return True
    except Exception as e:
        logger.exception(f"❌ Erro ao carregar fiscalização da Ata {parecer_value}: {e}")
        return False


def _save_fiscalizacao_to_db(model, parecer_value: str, data: Dict[str, str]):
    db = model._get_session()
    try:
        record = db.query(FiscalizacaoAta).filter(
            FiscalizacaoAta.ata_parecer == parecer_value
        ).first()
        
        if not record:
            # Se não existir, cria um NOVO registro
            record = FiscalizacaoAta(
                ata_parecer=parecer_value, 
                data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            )
            db.add(record)
        
        # Atualiza os campos com os dados do dict 'data'
        record.gestor = data.get('gestor', '')
        record.gestor_substituto = data.get('gestor_substituto', '')
        record.fiscal_tecnico = data.get('fiscal_tecnico', '')
        record.fiscal_tec_substituto = data.get('fiscal_tec_substituto', '')
        record.fiscal_administrativo = data.get('fiscal_administrativo', '')
        record.fiscal_admin_substituto = data.get('fiscal_admin_substituto', '')
        record.observacoes = data.get('observacoes', '')
        record.data_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _get_fiscalizacao_from_db(model, parecer_value: str) -> Optional[Dict[str, str]]:
    db = model._get_session()
    try:
        row = db.query(FiscalizacaoAta).filter(
            FiscalizacaoAta.ata_parecer == parecer_value
        ).first()
        if row:
            return {
                'gestor': row.gestor or '',
                'gestor_substituto': row.gestor_substituto or '',
                'fiscal_tecnico': row.fiscal_tecnico or '',
                'fiscal_tec_substituto': row.fiscal_tec_substituto or '',
                'fiscal_administrativo': row.fiscal_administrativo or '',
                'fiscal_admin_substituto': row.fiscal_admin_substituto or '',
                'observacoes': row.observacoes or '',
                'data_criacao': row.data_criacao,
                'data_atualizacao': row.data_atualizacao,
            }
        return None
    finally:
        db.close()


def _populate_fields(parent_dialog, data: Dict[str, str]):
    mapping = {
        'fiscal_gestor': 'gestor',
        'fiscal_gestor_substituto': 'gestor_substituto',
        'fiscalizacao_tecnico': 'fiscal_tecnico',
        'fiscalizacao_tec_substituto': 'fiscal_tec_substituto',
        'fiscalizacao_administrativo': 'fiscal_administrativo',
        'fiscalizacao_admin_substituto': 'fiscal_admin_substituto',
        'fiscal_observacoes': 'observacoes',
    }
    for attr, key in mapping.items():
        widget = getattr(parent_dialog, attr, None)
        value = data.get(key, '')
        if not widget:
            continue
        if hasattr(widget, 'setText'):
            widget.setText(value)
        elif hasattr(widget, 'setPlainText'):
            widget.setPlainText(value)
