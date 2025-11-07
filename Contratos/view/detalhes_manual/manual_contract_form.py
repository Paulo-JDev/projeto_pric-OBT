# Contratos/view/manual_contract_form.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import QSize
from utils.icon_loader import icon_manager


class ManualContractForm(QDialog):
    """
    Formulário para adicionar contrato manual.
    
    ✅ ATUALIZADO: Validação de duplicidade em tempo real
    """
    
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Contrato Manual")
        self.setFixedSize(500, 350)  # Aumentado para caber aviso
        
        self.model = model  # ✅ Recebe model para validação
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ==================== TÍTULO ====================
        title = QLabel("Preencha os dados do contrato manual:")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(title)
        
        # ==================== FORMULÁRIO ====================
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        
        # Campo 1: Número (obrigatório)
        self.numero_le = QLineEdit()
        self.numero_le.setPlaceholderText("Ex: 001/2025 (obrigatório)")
        self.numero_le.textChanged.connect(self._check_duplicate)  # ✅ Validação em tempo real
        form_layout.addRow("Número *:", self.numero_le)
        
        # Campo 2: Número Licitação
        self.licitacao_le = QLineEdit()
        self.licitacao_le.setPlaceholderText("Ex: 12345/2025")
        form_layout.addRow("Número Licitação:", self.licitacao_le)
        
        # Campo 3: NUP
        self.nup_le = QLineEdit()
        self.nup_le.setPlaceholderText("Ex: 12345.123456/2025-12")
        form_layout.addRow("NUP:", self.nup_le)
        
        # Campo 4: CNPJ
        self.cnpj_le = QLineEdit()
        self.cnpj_le.setPlaceholderText("Ex: 12.345.678/0001-90")
        form_layout.addRow("CNPJ:", self.cnpj_le)
        
        # Campo 5: UASG (obrigatório)
        self.uasg_le = QLineEdit()
        self.uasg_le.setPlaceholderText("Ex: 787010 (obrigatório)")
        self.uasg_le.textChanged.connect(self._check_duplicate)  # ✅ Validação em tempo real
        form_layout.addRow("UASG *:", self.uasg_le)
        
        main_layout.addLayout(form_layout)
        
        # ==================== ✅ LABEL DE AVISO ====================
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet(
            "color: red; font-weight: bold; padding: 5px; "
            "background-color: #ffe6e6; border: 1px solid red; border-radius: 3px;"
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        main_layout.addWidget(self.warning_label)
        
        # ==================== BOTÕES ====================
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Botão Salvar
        self.btn_save = QPushButton("Salvar")
        self.btn_save.setIcon(icon_manager.get_icon("concluido"))
        self.btn_save.setIconSize(QSize(20, 20))
        self.btn_save.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_save)
        
        # Botão Cancelar
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setIcon(icon_manager.get_icon("close"))
        self.btn_cancel.setIconSize(QSize(20, 20))
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        main_layout.addLayout(button_layout)
    
    def _check_duplicate(self):
        """
        ✅ CORRIGIDO: Verifica duplicidade usando novo formato de ID
        """
        if not self.model:
            return
        
        numero = self.numero_le.text().strip()
        uasg = self.uasg_le.text().strip()
        
        if not numero or not uasg:
            self.warning_label.setVisible(False)
            self.btn_save.setEnabled(True)
            return
        
        # ✅ Novo formato de ID
        contrato_id = f"MANUAL-{uasg}-{numero}"
        
        # Verifica se existe
        from Contratos.model.models import Contrato
        db = self.model._get_db_session()
        
        try:
            existe = db.query(Contrato).filter(
                Contrato.id == contrato_id,
                Contrato.uasg_code == uasg
            ).first()
            
            if existe:
                self.warning_label.setText(
                    f"⚠️ Contrato {numero} já cadastrado na UASG {uasg}!"
                )
                self.warning_label.setVisible(True)
                self.btn_save.setEnabled(False)
            else:
                self.warning_label.setVisible(False)
                self.btn_save.setEnabled(True)
        except:
            pass
        finally:
            db.close()
    
    def get_data(self):
        """Retorna os dados preenchidos no formulário"""
        return {
            "numero": self.numero_le.text().strip(),
            "licitacao_numero": self.licitacao_le.text().strip(),
            "nup": self.nup_le.text().strip(),
            "cnpj": self.cnpj_le.text().strip(),
            "uasg": self.uasg_le.text().strip()
        }
