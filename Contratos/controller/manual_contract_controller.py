# Contratos/controller/manual_contract_controller.py

"""
Controller para gerenciar contratos manuais.
Responsável por adicionar, exportar e importar contratos manuais.
"""

import json
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog
from Contratos.view.manual_contract_dialog import ManualContractDialog
from Contratos.view.manual_contract_form import ManualContractForm


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
        """Abre formulário e adiciona contrato manual"""
        form = ManualContractForm(self.main_window)
        
        if form.exec() != QDialog.DialogCode.Accepted:
            return
        
        data = form.get_data()
        
        # Validação de campos obrigatórios
        if not data["numero"] or not data["uasg"]:
            QMessageBox.warning(
                self.main_window,
                "Campos Obrigatórios",
                "Os campos 'Número' e 'UASG' são obrigatórios!"
            )
            return
        
        # Cria ID único para contrato manual
        contrato_id = f"MANUAL-{data['numero']}"
        
        # Monta estrutura do contrato
        contrato_dict = {
            "id": contrato_id,
            "numero": data["numero"],
            "licitacao_numero": data["licitacao_numero"],
            "processo": data["nup"],  # NUP vai para o campo processo
            "fornecedor": {
                "nome": "",  # Será preenchido depois
                "cnpj_cpf_idgener": data["cnpj"]
            },
            "objeto": "",  # Será preenchido depois
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
            "manual": True,  # ✅ MARCA COMO MANUAL
            "raw_json": json.dumps(data)
        }
        
        try:
            # Salva no banco
            self.model.save_uasg_data(data["uasg"], [contrato_dict])
            
            QMessageBox.information(
                self.main_window,
                "Sucesso",
                f"Contrato {data['numero']} adicionado com sucesso!\n\n"
                f"ID: {contrato_id}\n"
                f"UASG: {data['uasg']}"
            )
            
            # Atualiza a tabela se a UASG já estiver carregada
            current_uasg = self.main_window.uasg_input.text().strip()
            if current_uasg == data["uasg"]:
                self.main_window.controller.fetch_and_create_table()
                
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao adicionar contrato manual:\n{str(e)}"
            )
    
    # ==================== EXPORTAR CONTRATOS ====================
    def export_manual_contracts(self):
        """Exporta apenas contratos manuais para JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Exportar Contratos Manuais",
            "contratos_manuais.json",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # Busca apenas contratos manuais
            conn = self.model._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM contratos WHERE manual = 1")
            rows = cursor.fetchall()
            conn.close()
            
            # Converte para lista de dicionários
            contratos = [json.loads(row["raw_json"]) for row in rows]
            
            # Salva no arquivo
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(contratos, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(
                self.main_window,
                "Exportação Concluída",
                f"{len(contratos)} contratos manuais exportados para:\n{file_path}"
            )
            
        except Exception as e:
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
