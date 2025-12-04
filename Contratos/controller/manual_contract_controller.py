# Contratos/controller/manual_contract_controller.py

"""
Controller para gerenciar contratos manuais.
Responsável por adicionar, exportar e importar contratos manuais.
"""

import json
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog
from Contratos.view.detalhes_manual.manual_contract_dialog import ManualContractDialog
from Contratos.view.detalhes_manual.manual_contract_form import ManualContractForm

class ManualContractController:
    """Controla operações de contratos manuais"""
    
    def __init__(self, model, main_window):
        self.model = model
        self.main_window = main_window
    
    # ==================== ABRIR MINI JANELA ====================
    def open_manual_contract_window(self):
        """Abre a mini janela com os 3 botões"""
        dialog = ManualContractDialog(self.main_window)
        
        # Conecta os botões
        dialog.btn_add.clicked.connect(self.add_manual_contract)
        dialog.btn_export.clicked.connect(self.export_manual_contracts)
        dialog.btn_import.clicked.connect(self.import_manual_contracts)
        
        dialog.exec()
    
    # ==================== ADICIONAR CONTRATO ====================
    def add_manual_contract(self):
        """
        Abre formulário e adiciona contrato manual.
        
        ✅ CORRIGIDO: ID agora inclui UASG para permitir mesmo número em UASGs diferentes
        """
        form = ManualContractForm(self.main_window, self.model)
        
        if form.exec() != QDialog.DialogCode.Accepted:
            return
        
        data = form.get_data()
        
        # ==================== VALIDAÇÃO: CAMPOS OBRIGATÓRIOS ====================
        if not data["numero"] or not data["uasg"]:
            QMessageBox.warning(
                self.main_window,
                "Campos Obrigatórios",
                "Os campos 'Número' e 'UASG' são obrigatórios!"
            )
            return
        
        # ==================== ✅ CORRIGIDO: ID INCLUI UASG ====================
        # ANTES: contrato_id = f"MANUAL-{data['numero']}"
        # AGORA: Inclui UASG para permitir mesmo número em UASGs diferentes
        contrato_id = f"MANUAL-{data['uasg']}-{data['numero']}"
        
        # ==================== VALIDAÇÃO: CONTRATO DUPLICADO (mesma UASG) ====================
        if self._check_contract_exists(contrato_id, data["uasg"]):
            QMessageBox.warning(
                self.main_window,
                "Contrato já Cadastrado",
                f"⚠️ Já existe um contrato com o número <b>{data['numero']}</b> "
                f"cadastrado na UASG <b>{data['uasg']}</b>.\n\n"
                f"ID do contrato: {contrato_id}\n\n"
                f"Não é possível cadastrar contratos duplicados.\n"
                f"Use um número diferente ou edite o contrato existente."
            )
            return
        
        # Monta estrutura do contrato
        contrato_dict = {
            "id": contrato_id,
            "numero": data["numero"],  # ✅ Número SEM prefixo (ex: "001/2025")
            "licitacao_numero": data["licitacao_numero"],
            "processo": data["nup"],
            "fornecedor": {
                "nome": "",
                "cnpj_cpf_idgener": data["cnpj"]
            },
            "objeto": "",
            "valor_global": "",
            "vigencia_inicio": "",
            "vigencia_fim": "",
            "tipo": "",
            "modalidade": "",
            "contratante": {
                "orgao": {
                    "unidade_gestora": {
                        "codigo": data["uasg"],
                        "nome_resumido": ""
                    }
                }
            },
            "manual": True,
            "sigla_om_resp": "",
            "orgao_responsavel": "",
            "raw_json": json.dumps(data)
        }
        
        try:
            # Salva no banco
            self.model.save_uasg_data(data["uasg"], [contrato_dict])
            
            QMessageBox.information(
                self.main_window,
                "Sucesso",
                f"✅ Contrato <b>{data['numero']}</b> adicionado com sucesso!\n\n"
                f"ID: {contrato_id}\n"
                f"UASG: {data['uasg']}\n\n"
                f"💡 A tabela será atualizada automaticamente."
            )
            
            # Atualiza automaticamente se a UASG já estiver carregada
            uasg_label = self.main_window.uasg_info_label.text()
            if f"UASG: {data['uasg']}" in uasg_label:
                self.main_window.controller.update_table(data["uasg"])
                
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"❌ Erro ao adicionar contrato manual:\n{str(e)}"
            )

    def _check_contract_exists(self, contrato_id: str, uasg_code: str) -> bool:
        """
        Verifica se já existe um contrato com o mesmo ID na mesma UASG.
        
        Args:
            contrato_id: ID do contrato (ex: "MANUAL-001/2025")
            uasg_code: Código da UASG (ex: "787010")
        
        Returns:
            True se o contrato já existe, False caso contrário
        """
        from Contratos.model.models import Contrato
        
        db = self.model._get_db_session()
        
        try:
            # Busca contrato com mesmo ID e mesma UASG
            contrato_existente = db.query(Contrato).filter(
                Contrato.id == contrato_id,
                Contrato.uasg_code == uasg_code
            ).first()
            
            if contrato_existente:
                print(f"⚠️ Contrato duplicado detectado: {contrato_id} na UASG {uasg_code}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro ao verificar duplicidade: {e}")
            return False  # Em caso de erro, permite a inserção
        finally:
            db.close()
    
    # ==================== EXPORTAR CONTRATOS ====================
    def export_manual_contracts(self):
        """
        Exporta contratos manuais para JSON, incluindo dados extras como Portaria 
        que podem estar na tabela de status.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Exportar Contratos Manuais",
            "contratos_manuais.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            conn = self.model._get_db_connection()
            cursor = conn.cursor()
            
            # Busca o JSON base do contrato e a portaria da tabela de status
            query = """
            SELECT 
                c.raw_json,
                s.portaria_edit
            FROM contratos c
            LEFT JOIN status_contratos s ON c.id = s.contrato_id
            WHERE c.manual = 1
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            contratos_exportacao = []
            
            for row in rows:
                # Carrega o JSON base
                contrato_dict = json.loads(row["raw_json"])
                
                contratos_exportacao.append(contrato_dict)
            
            # Salva no arquivo
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(contratos_exportacao, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(
                self.main_window,
                "Exportação Concluída",
                f"{len(contratos_exportacao)} contratos manuais exportados com sucesso!\n(Incluindo Portarias e dados extras)"
            )
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao exportar contratos:\n{str(e)}"
            )
    
    # ==================== IMPORTAR CONTRATOS ====================
    def import_manual_contracts(self):
        """Importa contratos manuais de um JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Importar Contratos Manuais",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # Lê o arquivo
            with open(file_path, "r", encoding="utf-8") as f:
                contratos = json.load(f)
            
            # Agrupa por UASG
            por_uasg = {}
            for contrato in contratos:
                uasg = contrato.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo")
                if not uasg:
                    continue
                
                # Garante que está marcado como manual
                contrato["manual"] = True
                
                por_uasg.setdefault(uasg, []).append(contrato)
            
            # Salva cada grupo
            for uasg, lista in por_uasg.items():
                self.model.save_uasg_data(uasg, lista)
            
            QMessageBox.information(
                self.main_window,
                "Importação Concluída",
                f"{len(contratos)} contratos manuais importados com sucesso!"
            )
            
            # Atualiza a tabela se necessário
            current_uasg = self.main_window.uasg_input.text().strip()
            if current_uasg in por_uasg:
                self.main_window.controller.fetch_and_create_table()
                
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao importar contratos:\n{str(e)}"
            )
