# Contratos/controller/detalhe_controller.py

import uuid
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTextEdit, QListWidgetItem, QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
import json
import sqlite3 # Adicionado
from datetime import datetime
from utils.icon_loader import icon_manager
from Contratos.model.uasg_model import UASGModel # Para _get_db_connection se necessário, ou usar o model passado
from Contratos.controller.controller_fiscal import load_fiscalizacao, save_fiscalizacao

from integration.model.trello_model import TrelloModel
from integration.controller.trello_individual_controller import TrelloIndividualController, TrelloSyncWorker

SUCCESS_MSG_TIMEOUT_MS = 300

def registro_def(parent, registro_list, status_dropdown):
    """Abre uma mini janela para adicionar um comentário com data, hora e status selecionado."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Adicionar Registro")
    layout = QVBoxLayout()
    
    text_edit = QTextEdit()
    layout.addWidget(text_edit)
    
    add_button = QPushButton("Fechar e Adicionar Registro")
    add_button.setIcon(icon_manager.get_icon("registrar_status"))
    layout.addWidget(add_button)
    
    dialog.setLayout(layout)
    
    def add_registro():
        comment_text = text_edit.toPlainText().strip()
        if comment_text:
            timestamp = datetime.now().strftime("%d/%m/%Y")  # Formato da data
            status = status_dropdown.currentText()
            full_comment = f"{timestamp} - {comment_text} - {status}"
            item = QListWidgetItem(full_comment)
            item.setCheckState(Qt.CheckState.Unchecked)
            registro_list.addItem(item)  # Adiciona à lista de registros
            print(f"✅ Registro adicionado: {full_comment}")
        dialog.accept()
    
    add_button.clicked.connect(add_registro)
    dialog.exec()

def delete_registro(registro_list):
    """Remove os registros selecionados"""
    for i in range(registro_list.count() - 1, -1, -1):
        item = registro_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            registro_list.takeItem(i)

def save_status(parent, data, model: UASGModel, status_dropdown, registro_list, objeto_edit, portaria_edit, termo_aditivo_edit, radio_buttons):
    """Salva o status, registros e comentários no banco de dados SQLite."""

    id_contrato = data.get("id")
    uasg_nested = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")
    uasg = uasg_nested or data.get("uasg_code", "")

    # Se é contrato MANUAL e está sem id, tenta descobrir no banco
    if data.get("manual") and not id_contrato and uasg:
        try:
            conn_tmp = model._get_db_connection()
            cursor_tmp = conn_tmp.cursor()
            numero = data.get("numero")
            if numero:
                cursor_tmp.execute(
                    "SELECT id FROM contratos WHERE numero = ? AND uasg_code = ?",
                    (numero, uasg)
                )
                row = cursor_tmp.fetchone()
                if row:
                    id_contrato = row["id"]
                    data["id"] = id_contrato
                    print(f"[save_status] ID manual recuperado do DB: {id_contrato}")
            conn_tmp.close()
        except Exception as e:
            print(f"[save_status] Erro ao recuperar ID manual: {e}")

    # Validação única
    if not id_contrato or not uasg:
        print("[save_status] ERRO: ID ou UASG vazios. data =", data)
        QMessageBox.critical(
            parent,
            "Erro ao salvar",
            "ID do contrato ou UASG não encontrados."
        )
        return None, None

    id_contrato = str(id_contrato)

    # Salva os links
    link_data = {
        "link_contrato": parent.link_contrato_le.text(),
        "link_ta": parent.link_ta_le.text(),
        "link_portaria": parent.link_portaria_le.text(),
        "link_pncp_espc": parent.link_pncp_espc_le.text(),
        "link_portal_marinha": parent.link_portal_marinha_le.text()
    }
    model.save_contract_links(id_contrato, link_data)

    # Prepara os dados para o JSON e para as colunas
    data_registro_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    radio_options_data = {
        title: next(
            (option for option, button in radio_buttons[title].items() if button.isChecked()),
            "Não selecionado"
        ) for title in radio_buttons
    }
    radio_options_json = json.dumps(radio_options_data)

    # Tratamento seguro dos campos de texto
    txt_objeto = objeto_edit.text() if objeto_edit is not None else ""
    txt_portaria = portaria_edit.text() if portaria_edit is not None else ""
    txt_ta = termo_aditivo_edit.text() if termo_aditivo_edit is not None else ""
    status_atual = status_dropdown.currentText()

    conn = model._get_db_connection()
    cursor = conn.cursor()

    try:
        # Salva/atualiza status_contratos
        cursor.execute("SELECT 1 FROM status_contratos WHERE contrato_id = ?", (id_contrato,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('''
                UPDATE status_contratos
                SET uasg_code = ?, 
                    status = ?, 
                    objeto_editado = ?, 
                    portaria_edit = ?, 
                    termo_aditivo_edit = ?, 
                    radio_options_json = ?, 
                    data_registro = ?
                WHERE contrato_id = ?
            ''', (uasg, status_atual, txt_objeto, txt_portaria, txt_ta, radio_options_json, data_registro_atual, id_contrato))
        else:
            cursor.execute('''
                INSERT INTO status_contratos
                (contrato_id, uasg_code, status, objeto_editado, portaria_edit, termo_aditivo_edit, radio_options_json, data_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_contrato, uasg, status_atual, txt_objeto, txt_portaria, txt_ta, radio_options_json, data_registro_atual))

        # ==================== SALVAMENTO DE REGISTROS (COM PRESERVAÇÃO DE UUID) ====================
        # 1. Busca UUIDs existentes antes de deletar
        cursor.execute("SELECT uuid, texto FROM registros_status WHERE contrato_id = ?", (id_contrato,))
        registros_existentes = {row['texto']: row['uuid'] for row in cursor.fetchall()}

        # 2. Deleta todos os registros antigos
        cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (id_contrato,))

        # 3. Pega os textos atuais da interface
        registros_texts = [registro_list.item(i).text() for i in range(registro_list.count())]

        # 4. Reinsere preservando UUIDs de textos iguais
        for texto in registros_texts:
            if texto in registros_existentes:
                # Texto já existia → reutiliza UUID
                registro_uuid = registros_existentes[texto]
            else:
                # Texto novo → gera novo UUID
                registro_uuid = str(uuid.uuid4())

            cursor.execute(
                "INSERT INTO registros_status (uuid, contrato_id, uasg_code, texto) VALUES (?, ?, ?, ?)",
                (registro_uuid, id_contrato, uasg, texto)
            )

        # ==================== SALVAMENTO DE DADOS DE CONTRATO MANUAL ====================
        if data.get("manual") and hasattr(parent, "line_edits"):
            print(f"🔄 Salvando dados manuais para o contrato {id_contrato}...")

            def get_field_text(key):
                widget = parent.line_edits.get(key)
                if widget:
                    if hasattr(widget, "date"):
                        return widget.date().toString("yyyy-MM-dd")
                    return widget.text().strip()
                return ""

            novo_valor = get_field_text("valor_global")
            nova_empresa = get_field_text("empresa")
            novo_cnpj = get_field_text("cnpj")
            nova_licitacao = get_field_text("licitacao_numero")
            novo_nup = get_field_text("processo")
            nova_vig_inicio = get_field_text("vigencia_inicio")
            nova_vig_fim = get_field_text("vigencia_fim")

            nova_sigla = getattr(parent, "manual_sigla_om", None)
            nova_sigla = nova_sigla.text().strip() if nova_sigla else ""
            novo_orgao = getattr(parent, "manual_orgao", None)
            novo_orgao = novo_orgao.text().strip() if novo_orgao else ""
            novo_tipo = getattr(parent, "manual_tipo", None)
            novo_tipo = novo_tipo.text().strip() if novo_tipo else ""
            nova_modalidade = getattr(parent, "manual_modalidade", None)
            nova_modalidade = nova_modalidade.text().strip() if nova_modalidade else ""

            try:
                raw_json_str = data.get("raw_json", "{}")
                if isinstance(raw_json_str, str) and raw_json_str:
                    current_json = json.loads(raw_json_str)
                else:
                    current_json = {}

                # GARANTE campos críticos intactos
                current_json["id"] = id_contrato
                current_json["manual"] = True

                # Garante estrutura contratante/orgao/unidade_gestora
                if "contratante" not in current_json:
                    current_json["contratante"] = {"orgao": {"unidade_gestora": {}}}
                if "orgao" not in current_json["contratante"]:
                    current_json["contratante"]["orgao"] = {"unidade_gestora": {}}
                if "unidade_gestora" not in current_json["contratante"]["orgao"]:
                    current_json["contratante"]["orgao"]["unidade_gestora"] = {}

                ug = current_json["contratante"]["orgao"]["unidade_gestora"]
                ug["codigo"] = uasg
                ug["nome_resumido"] = nova_sigla or ug.get("nome_resumido", "")

                # Atualiza os campos que o usuário pode editar
                current_json["numero"] = data.get("numero")
                current_json["valor_global"] = novo_valor
                current_json["licitacao_numero"] = nova_licitacao
                current_json["processo"] = novo_nup
                current_json["vigencia_inicio"] = nova_vig_inicio
                current_json["vigencia_fim"] = nova_vig_fim
                current_json["tipo"] = novo_tipo
                current_json["modalidade"] = nova_modalidade
                current_json["sigla_om"] = nova_sigla
                current_json["orgao_responsavel"] = novo_orgao
                current_json["objeto"] = txt_objeto
                current_json["contratante_orgao_unidade_gestora_nome_resumido"] = nova_sigla

                if "fornecedor" not in current_json or not isinstance(current_json["fornecedor"], dict):
                    current_json["fornecedor"] = {}
                current_json["fornecedor"]["nome"] = nova_empresa
                current_json["fornecedor"]["cnpj_cpf_idgener"] = novo_cnpj

                new_raw_json = json.dumps(current_json, ensure_ascii=False)

                cursor.execute("""
                    UPDATE contratos
                    SET 
                        valor_global = ?,
                        fornecedor_nome = ?,
                        fornecedor_cnpj = ?,
                        licitacao_numero = ?,
                        processo = ?,
                        vigencia_inicio = ?,
                        vigencia_fim = ?,
                        tipo = ?,
                        modalidade = ?,
                        objeto = ?,
                        contratante_orgao_unidade_gestora_nome_resumido = ?,
                        raw_json = ?
                    WHERE id = ?
                """, (
                    novo_valor, nova_empresa, novo_cnpj,
                    nova_licitacao, novo_nup,
                    nova_vig_inicio, nova_vig_fim,
                    novo_tipo, nova_modalidade,
                    txt_objeto, nova_sigla, new_raw_json,
                    id_contrato
                ))
                print(f"✅ Dados manuais atualizados para o contrato {id_contrato}")
            except Exception as e_json:
                print(f"❌ Erro ao atualizar JSON/colunas manuais: {e_json}")

        conn.commit()
        print(f"✅ Status salvo com sucesso para contrato {id_contrato}.")

    except sqlite3.Error as e:
        print(f"❌ Erro ao salvar status no banco de dados: {e}")
        conn.rollback()
    finally:
        conn.close()

    save_fiscalizacao(model, id_contrato, parent)

    return id_contrato, uasg

def show_success_message(parent):
    """Mostra uma mensagem de sucesso que se fecha automaticamente"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle("Concluído")
    msg_box.setText("Dados salvos com sucesso!")
    msg_box.open()
    
    # Fechar a mensagem automaticamente depois de 300ms
    QTimer.singleShot(SUCCESS_MSG_TIMEOUT_MS, msg_box.close)

def load_status(data, model: UASGModel, status_dropdown, objeto_edit, portaria_edit, termo_aditivo_edit, radio_buttons, registro_list, parent_dialog):
    """Carrega os dados de status, registros e comentários do banco de dados SQLite."""
    id_contrato = data.get("id", "")
    uasg = data.get("contratante", {}).get("orgao", {}).get("unidade_gestora", {}).get("codigo", "")

    if not id_contrato:
        print("ID do contrato não encontrado para carregar o status.")
        return

    conn = model._get_db_connection()
    cursor = conn.cursor()

    # Carrega os links
    links = model.get_contract_links(id_contrato)
    if links:
        parent_dialog.link_contrato_le.setText(links.get("link_contrato", ""))
        parent_dialog.link_ta_le.setText(links.get("link_ta", ""))
        parent_dialog.link_portaria_le.setText(links.get("link_portaria", ""))
        parent_dialog.link_pncp_espc_le.setText(links.get("link_pncp_espc", ""))
        parent_dialog.link_portal_marinha_le.setText(links.get("link_portal_marinha", ""))

    try:
        # Carregar status_contratos
        cursor.execute("SELECT status, objeto_editado, portaria_edit, termo_aditivo_edit, radio_options_json FROM status_contratos WHERE contrato_id = ?", (id_contrato,))
        status_row = cursor.fetchone()

        objeto_original = data.get("objeto", "Não informado")

        if status_row:
            status_dropdown.setCurrentText(status_row['status'] or "")

            if objeto_edit is not None:
                texto_salvo = status_row['objeto_editado']
                if texto_salvo:
                    objeto_edit.setText(texto_salvo)
                else:
                    objeto_edit.setText(objeto_original)

            if portaria_edit is not None:
                portaria_edit.setText(status_row['portaria_edit'] or "")

            if termo_aditivo_edit is not None:
                termo_aditivo_edit.setText(status_row['termo_aditivo_edit'] or "")

            if status_row['radio_options_json']:
                try:
                    radio_options = json.loads(status_row['radio_options_json'])
                    for title, selected_value in radio_options.items():
                        if title in radio_buttons and selected_value in radio_buttons[title]:
                            radio_buttons[title][selected_value].setChecked(True)
                except json.JSONDecodeError:
                    print(f"Erro ao decodificar radio_options_json para contrato {id_contrato}")
        else:
            if objeto_edit is not None:
                objeto_edit.setText(objeto_original)

        # Carregar registros_status
        if registro_list is not None:
            registro_list.clear()
            cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (id_contrato,))
            registros_encontrados = cursor.fetchall()
            for row in registros_encontrados:
                item = QListWidgetItem(row['texto'])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                registro_list.addItem(item)
            registro_list.clearSelection()

        # ==================== CARREGAMENTO DE DADOS DE CONTRATO MANUAL ====================
        if data.get("manual") and hasattr(parent_dialog, "line_edits"):
            print(f"🔄 Carregando dados do contrato manual {id_contrato}...")

            # Busca os dados atualizados diretamente do banco
            cursor.execute("""
                SELECT valor_global, fornecedor_nome, fornecedor_cnpj, 
                       licitacao_numero, processo, vigencia_inicio, vigencia_fim,
                       tipo, modalidade, contratante_orgao_unidade_gestora_nome_resumido, 
                       objeto, raw_json
                FROM contratos WHERE id = ?
            """, (id_contrato,))
            contract_row = cursor.fetchone()

            if contract_row:
                def set_manual_field(key, val):
                    widget = parent_dialog.line_edits.get(key)
                    if widget and val:
                        if hasattr(widget, "setDate"):
                            from PyQt6.QtCore import QDate
                            try:
                                parts = str(val).split('-')
                                if len(parts) == 3:
                                    widget.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
                            except:
                                pass
                        elif hasattr(widget, "setText"):
                            widget.setText(str(val))

                # Preenche os campos da interface
                set_manual_field("valor_global", contract_row['valor_global'])
                set_manual_field("empresa", contract_row['fornecedor_nome'])
                set_manual_field("cnpj", contract_row['fornecedor_cnpj'])
                set_manual_field("licitacao_numero", contract_row['licitacao_numero'])
                set_manual_field("processo", contract_row['processo'])
                set_manual_field("vigencia_inicio", contract_row['vigencia_inicio'])
                set_manual_field("vigencia_fim", contract_row['vigencia_fim'])

                # Preenche campos de gestão
                if getattr(parent_dialog, "manual_tipo", None):
                    parent_dialog.manual_tipo.setText(contract_row['tipo'] or "")
                if getattr(parent_dialog, "manual_modalidade", None):
                    parent_dialog.manual_modalidade.setText(contract_row['modalidade'] or "")
                if getattr(parent_dialog, "manual_sigla_om", None):
                    parent_dialog.manual_sigla_om.setText(contract_row['contratante_orgao_unidade_gestora_nome_resumido'] or "")

                # Tenta recuperar Órgão Responsável do raw_json
                if getattr(parent_dialog, "manual_orgao", None) and contract_row['raw_json']:
                    try:
                        json_data = json.loads(contract_row['raw_json'])
                        orgao_resp = json_data.get("orgao_responsavel", "")
                        parent_dialog.manual_orgao.setText(orgao_resp)
                    except:
                        pass

                # IMPORTANTE: Atualiza o dicionário data com os valores do banco
                # mas SEM sobrescrever o ID e a estrutura principal
                data["valor_global"] = contract_row['valor_global'] or ""
                data["objeto"] = contract_row['objeto'] or objeto_original

                if "fornecedor" not in data:
                    data["fornecedor"] = {}
                data["fornecedor"]["nome"] = contract_row['fornecedor_nome'] or ""
                data["fornecedor"]["cnpj_cpf_idgener"] = contract_row['fornecedor_cnpj'] or ""

                data["licitacao_numero"] = contract_row['licitacao_numero'] or ""
                data["processo"] = contract_row['processo'] or ""
                data["vigencia_inicio"] = contract_row['vigencia_inicio'] or ""
                data["vigencia_fim"] = contract_row['vigencia_fim'] or ""
                data["tipo"] = contract_row['tipo'] or ""
                data["modalidade"] = contract_row['modalidade'] or ""

                if "contratante" not in data:
                    data["contratante"] = {"orgao": {"unidade_gestora": {}}}
                data["contratante"]["orgao"]["unidade_gestora"]["nome_resumido"] = contract_row['contratante_orgao_unidade_gestora_nome_resumido'] or ""

                print(f"✅ Dados do contrato manual {id_contrato} carregados e sincronizados com o dicionário data!")

        if status_row:
            print(f"Status, registros e comentários para o contrato {id_contrato} carregados do banco de dados.")
        else:
            print(f"Nenhum status salvo encontrado para o contrato {id_contrato} no banco de dados. Usando valores padrão/originais.")

    except sqlite3.Error as e:
        print(f"Erro ao carregar status do banco de dados para contrato {id_contrato}: {e}")
    except Exception as e:
        print(f"Erro inesperado ao carregar status para contrato {id_contrato}, UASG {uasg}: {e}")
    finally:
        conn.close()

    load_fiscalizacao(model, id_contrato, parent_dialog)

def copy_to_clipboard(line_edit):
    """Copia o texto do campo para a área de transferência"""
    clipboard = QApplication.clipboard()
    clipboard.setText(line_edit.text())

def copy_registros(parent_view, registro_list):
    """Copia o texto de todos os registros com a checkbox marcada."""
    selected_texts = []
    for i in range(registro_list.count()):
        item = registro_list.item(i)
        if item.checkState() == Qt.CheckState.Checked:
            selected_texts.append(item.text())
    
    if not selected_texts:
        QMessageBox.information(parent_view, "Nada a Copiar", "Nenhum registro foi selecionado.")
        return

    # Junta os textos com uma quebra de linha entre eles
    text_to_copy = "\n".join(selected_texts)
    clipboard = QApplication.clipboard()
    clipboard.setText(text_to_copy)
    
    #Mantenha essa mensgame comentaada ate eu descobrir pq ela esta sendo duplicada
    #QMessageBox.information(parent_view, "Copiado", "O(s) registro(s) selecionado(s) foi/foram copiado(s) para a área de transferência.")
