# integration/controller/trello_individual_controller.py
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

# Importações necessárias para o banco de dados e modelos
from Contratos.model import database
from Contratos.model.models import RegistroStatus

class TrelloIndividualController:
    def __init__(self, trello_model):
        self.trello_model = trello_model
        # Ajuste de caminhos relativos para garantir funcionamento
        self.config_path = Path("utils/json/trello_json.json")
        self.comments_path = Path("utils/json/trello_comments.json")

    def _get_config(self):
        if not self.config_path.exists():
            return {"api_key": "", "token": "", "mappings": {}, "cards_sincronizados": {}}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler config Trello: {e}")
            return {}

    def _get_comment_history(self):
        if not self.comments_path.exists():
            return {} # Estrutura: {"id_contrato": [id_reg1, id_reg2]}
        try:
            with open(self.comments_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def sync_contract(self, contrato_data, status_atual):
        """
        Sincroniza individualmente: Move/Atualiza ou Cria novo.
        Envia registros como comentários individuais.
        """
        config = self._get_config()
        
        # Configura as credenciais no model
        self.trello_model.api_key = config.get("api_key")
        self.trello_model.token = config.get("token")
        
        if not self.trello_model.api_key or not self.trello_model.token:
             return False, "Credenciais do Trello não configuradas."

        list_id = config.get("mappings", {}).get(status_atual)
        if not list_id:
            return False, f"Status '{status_atual}' não mapeado para uma lista no Trello."

        contrato_id_local = str(contrato_data.get('id'))
        historico_cards = config.get("cards_sincronizados", {})
        comment_history = self._get_comment_history()

        # --- COLETA DE DADOS ROBUSTA ---
        fornecedor = contrato_data.get('fornecedor_nome') or contrato_data.get('fornecedor', {}).get('nome', 'N/A')
        cnpj = contrato_data.get('fornecedor_cnpj') or contrato_data.get('fornecedor', {}).get('cnpj_cpf_idgener', 'N/A')
        obj_final = contrato_data.get('objeto_editado') or contrato_data.get('objeto', 'N/A')
        vigencia_fim = contrato_data.get('vigencia_fim')
        
        titulo = f"Contrato: {contrato_data.get('numero', 'S/N')}"
        description = (
            f"### 📋 Dados do Contrato\n"
            f"**🏢 Fornecedor:** {fornecedor}\n"
            f"**🆔 CNPJ:** {cnpj}\n\n"
            f"**🔹 Objeto:**\n> {obj_final}\n\n"
            f"**💰 Valor Global:** R$ {contrato_data.get('valor_global', '0,00')}\n"
            f"**📑 Processo:** {contrato_data.get('processo', 'N/A')}\n"
            f"--- \n*Sincronizado via CA 360 em {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
        )

        card_id_trello = None
        res_final = None

        # --- LÓGICA: ATUALIZAR/MOVER OU CRIAR NOVO ---
        if contrato_id_local in historico_cards:
            card_id_trello = historico_cards[contrato_id_local]
            # Tenta atualizar. Se o card foi deletado no Trello, isso retorna False
            success_up, res_up = self.trello_model.update_card(card_id_trello, list_id, titulo, description)
            if success_up:
                res_final = res_up
            else:
                print(f"Card {card_id_trello} não encontrado ou erro ao atualizar. Criando novo...")
                card_id_trello = None # Força criação de um novo

        if not card_id_trello:
            success_new, res_new = self.trello_model.create_card(list_id, titulo, description)
            if success_new:
                card_id_trello = res_new.get('id')
                res_final = res_new
                
                # Atualiza o arquivo de mapeamento ID Local -> ID Trello
                config = self._get_config() # Recarrega para evitar conflitos
                if "cards_sincronizados" not in config:
                    config["cards_sincronizados"] = {}
                
                config["cards_sincronizados"][contrato_id_local] = card_id_trello

                checklist = self.trello_model.create_checklist(card_id_trello, "Tramitação / Pendências")
                if checklist:
                    # Defina aqui os passos padrão para todo contrato novo
                    tarefas_padrao = [
                        "Verificar Assinaturas",
                        "Publicar no PNCP",
                        "Emitir Nota de Empenho",
                        "Designar Fiscal",
                        "Arquivar Processo Físico"
                    ]

                    for tarefa in tarefas_padrao:
                        self.trello_model.add_checklist_item(checklist['id'], tarefa)
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            else:
                return False, f"Erro ao criar card: {res_new}"
            
        if card_id_trello:
            # A) Data de Entrega (Due Date)
            if vigencia_fim:
                try:
                    # Adiciona horário para garantir que o Trello entenda (final do dia)
                    data_formatada = f"{vigencia_fim}T18:00:00.000Z"
                    self.trello_model.set_due_date(card_id_trello, data_formatada)
                    print(f"📅 Prazo definido para: {vigencia_fim}")
                except Exception as e:
                    print(f"Erro ao definir data: {e}")

            # B) Links como Anexos
            links_para_enviar = {
                "📄 Contrato (Link)": contrato_data.get('link_contrato'),
                "⚓ Portal Marinha": contrato_data.get('link_portal_marinha'),
                "📜 Termo Aditivo": contrato_data.get('link_ta'),
                "🌐 PNCP": contrato_data.get('link_pncp_espc')
            }

            for nome_link, url_link in links_para_enviar.items():
                if url_link and "http" in url_link: # Só envia se tiver link válido
                    self.trello_model.add_attachment(card_id_trello, url_link, nome_link)
                    print(f"📎 Anexo adicionado: {nome_link}")

        # --- ADIÇÃO DOS REGISTROS COMO COMENTÁRIOS ---
        # Busca os registros usando SQLAlchemy Session
        registros_db = self.get_contract_records_with_ids(contrato_id_local)
        
        if registros_db:
            comment_history = self._get_comment_history()
            enviados = comment_history.get(contrato_id_local, [])
            novos_enviados = False

            for reg in registros_db:
                # USA UUID AO INVÉS DE ID SEQUENCIAL
                reg_uuid = reg['uuid']

                if reg_uuid not in enviados:
                    texto_comentario = f"📌 **Registro ({reg_uuid[:8]}...):**\n{reg['texto']}"

                    if self.trello_model.add_comment(card_id_trello, texto_comentario):
                        enviados.append(reg_uuid)
                        novos_enviados = True
                        print(f"✅ Comentário UUID {reg_uuid[:8]} enviado ao Trello")
                    else:
                        print(f"❌ Falha ao enviar comentário UUID {reg_uuid[:8]}")

            # Atualiza histórico
            if novos_enviados:
                comment_history[contrato_id_local] = enviados
                with open(self.comments_path, 'w', encoding='utf-8') as f:
                    json.dump(comment_history, f, indent=4, ensure_ascii=False)

        return True, "Sincronização concluída com sucesso."

    def get_contract_records_with_ids(self, contrato_id):
        """Busca registros trazendo ID e Texto para controle de duplicidade."""
        if database.SessionLocal is None:
            print("❌ Erro: Banco de dados não inicializado. SessionLocal é None.")
            return []
            
        session = database.SessionLocal() # Cria a sessão usando a factory atualizada
        try:
            registros = session.query(RegistroStatus).filter(RegistroStatus.contrato_id == str(contrato_id)).all()
            return [{'uuid': r.uuid, 'texto': r.texto} for r in registros]
        except Exception as e:
            print(f"Erro ao buscar registros: {e}")
            return []
        finally:
            session.close()

# --- CLASSE WORKER (THREAD) PARA NÃO TRAVAR A TELA ---
class TrelloSyncWorker(QThread):
    finished = pyqtSignal(bool, str) # Sinais: Sucesso (True/False), Mensagem

    def __init__(self, controller, contrato_data, status_atual):
        super().__init__()
        self.controller = controller
        self.contrato_data = contrato_data
        self.status_atual = status_atual

    def run(self):
        try:
            success, message = self.controller.sync_contract(self.contrato_data, self.status_atual)
            self.finished.emit(success, str(message))
        except Exception as e:
            self.finished.emit(False, f"Erro interno na thread Trello: {str(e)}")
