# app.py
# Pra rodar o app.py, rode o seguinte comando no terminal:
# uvicorn app:app --reload

import sqlite3
import json
from typing import List, Optional
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# --- 1. Lógica de Caminho Portátil (Seu código) ---
# Esta função garante que a aplicação encontre seus arquivos,
# seja rodando como script ou como um executável (PyInstaller).

def resource_path(relative_path: str) -> str:
    """Retorna o caminho absoluto para um recurso."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver empacotado, use o diretório do script atual
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- 2. Configuração do Caminho do Banco de Dados ---
# Usando sua lógica para definir o DB_PATH de forma robusta

# Define o diretório 'database' dentro da pasta da aplicação
DATABASE_DIR = Path(resource_path("database"))
DATABASE_DIR.mkdir(parents=True, exist_ok=True) # Garante que o diretório exista

# Define o caminho completo para o arquivo do banco de dados
DB_PATH = DATABASE_DIR / "gerenciador_uasg.db"
print(f"API irá usar o banco de dados em: {DB_PATH}")


# --- 3. Lógica de Acesso ao Banco de Dados ---
# Usando sua lógica para o DB_PATH dinâmico

def _get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_status_data_from_db():
    """Busca todos os dados de status, registros e comentários do banco de dados."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    all_data = []
    try:
        cursor.execute("SELECT contrato_id, uasg_code, status, objeto_editado, radio_options_json FROM status_contratos")
        status_rows = cursor.fetchall()
        for status_row in status_rows:
            data_entry = dict(status_row)
            contrato_id = data_entry['contrato_id']
            
            cursor.execute("SELECT texto FROM registros_status WHERE contrato_id = ?", (contrato_id,))
            data_entry['registros'] = [row['texto'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT texto FROM comentarios_status WHERE contrato_id = ?", (contrato_id,))
            data_entry['comentarios'] = [row['texto'] for row in cursor.fetchall()]
            
            all_data.append(data_entry)
            
    except sqlite3.Error as e:
        print(f"Erro ao buscar todos os dados de status: {e}")
        return None
    finally:
        conn.close()
    return all_data

def get_all_contratos_raw_from_db():
    """Retorna todos os contratos com o JSON bruto (dados completos da API pública)."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    contratos = []
    try:
        cursor.execute("SELECT raw_json FROM contratos")
        rows = cursor.fetchall()
        for row in rows:
            try:
                contratos.append(json.loads(row['raw_json']))
            except json.JSONDecodeError:
                print("Erro ao decodificar JSON de um contrato.")
    except sqlite3.Error as e:
        print(f"Erro ao buscar contratos: {e}")
        return None
    finally:
        conn.close()
    return contratos

# --- 4. Modelos de Dados Pydantic ---

class StatusContrato(BaseModel):
    contrato_id: str
    uasg_code: str
    status: str
    objeto_editado: str
    radio_options_json: str
    registros: List[str]
    comentarios: List[str]

# Modelo para atualização (PATCH), onde todos os campos são opcionais
class StatusContratoUpdate(BaseModel):
    status: Optional[str] = None
    objeto_editado: Optional[str] = None
    radio_options_json: Optional[str] = None

# --- 5. Configuração do Servidor FastAPI ---

app = FastAPI(
    title="API de Status de Contratos",
    version="1.0.0",
    description="Uma API para consultar o status de contratos, registros e comentários."
)

@app.get("/api/status", 
         response_model=List[StatusContrato],
         tags=["Status"],
         summary="Lista todos os status de contratos")
def get_status_data():
    """
    Este endpoint retorna uma lista completa de todos os status de contratos,
    incluindo seus registros e comentários associados.
    """
    data = get_all_status_data_from_db()
    if data is None:
        raise HTTPException(status_code=500, detail="Não foi possível buscar os dados do banco de dados.")
    return data


# GET para um status específico por ID
@app.get("/api/status/{contrato_id}", response_model=StatusContrato, tags=["Status"])
def get_status_by_id(contrato_id: str):
    # Você precisará criar uma função no seu model para buscar por ID
    # Ex: data = get_one_status_from_db(contrato_id)
    # Por enquanto, vamos simular:
    all_data = get_all_status_data_from_db()
    for item in all_data:
        if item['contrato_id'] == contrato_id:
            return item
    raise HTTPException(status_code=404, detail="Contrato não encontrado")

# PUT para atualizar um status (substituição completa)
@app.put("/api/status/{contrato_id}", response_model=StatusContrato, tags=["Status"])
def update_status(contrato_id: str, updated_data: StatusContrato):
    # Aqui iria a lógica para atualizar o registro completo no banco
    # Ex: update_status_in_db(contrato_id, updated_data)
    print(f"Atualizando contrato {contrato_id} com dados: {updated_data.dict()}")
    # Retorna os dados atualizados para confirmar
    return updated_data

# PATCH para atualizar parcialmente um status
@app.patch("/api/status/{contrato_id}", response_model=StatusContrato, tags=["Status"])
def partial_update_status(contrato_id: str, partial_data: StatusContratoUpdate):
    # Lógica para atualizar apenas os campos fornecidos
    # Ex: partial_update_in_db(contrato_id, partial_data)
    print(f"Atualizando parcialmente contrato {contrato_id} com dados: {partial_data.dict(exclude_unset=True)}")
    # Retorna o recurso completo após a atualização
    # (aqui você buscaria do banco o estado final)
    raise HTTPException(status_code=501, detail="Funcionalidade não implementada")

# DELETE para remover um status
@app.delete("/api/status/{contrato_id}", status_code=204, tags=["Status"])
def delete_status(contrato_id: str):
    """Deleta um status de contrato pelo seu ID."""
    success = delete_status_from_db(contrato_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contrato não encontrado para exclusão.")
    # Se der certo, não retorna corpo, apenas o status 204
    return
def delete_status_from_db(contrato_id: str) -> bool:
    """Deleta um status e seus registros/comentários associados."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    try:
        # Deleta de todas as tabelas relacionadas para manter a integridade
        cursor.execute("DELETE FROM comentarios_status WHERE contrato_id = ?", (contrato_id,))
        cursor.execute("DELETE FROM registros_status WHERE contrato_id = ?", (contrato_id,))
        cursor.execute("DELETE FROM status_contratos WHERE contrato_id = ?", (contrato_id,))
        
        conn.commit()
        
        # Verifica se alguma linha foi realmente deletada
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Erro ao deletar status do contrato {contrato_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
# ------------------------------------------- Parte das Informaçoes do Contrato -----------------------------------------------------------
def get_contratos_raw_by_uasg_from_db(uasg_code: str):
    """Retorna apenas os contratos de uma UASG específica, com JSON bruto completo."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    contratos = []
    try:
        cursor.execute("SELECT raw_json FROM contratos WHERE uasg_code = ?", (uasg_code,))
        rows = cursor.fetchall()
        for row in rows:
            try:
                contratos.append(json.loads(row['raw_json']))
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON para UASG {uasg_code}")
    except sqlite3.Error as e:
        print(f"Erro ao buscar contratos da UASG {uasg_code}: {e}")
        return None
    finally:
        conn.close()
    return contratos

@app.get("/api/contratos/raw/{uasg_code}",
         tags=["Contratos"],
         summary="Lista contratos completos (raw_json) filtrados por código UASG")
def get_contratos_raw_by_uasg(uasg_code: str):
    """
    Retorna apenas os contratos da UASG informada (dados crus da API pública),
    a partir dos dados salvos localmente no campo raw_json.
    """
    data = get_contratos_raw_by_uasg_from_db(uasg_code)
    if data is None or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"Nenhum contrato encontrado para a UASG {uasg_code}")
    return data

# --- 6. Ponto de Entrada para Executar o Servidor ---

if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# --- 7. Resumo de como usar a API ---
"""
Resumo
Acesse http://127.0.0.1:8000/api/status para ver seus dados.
Acesse http://127.0.0.1:8000/api/contratos/raw/{uasg_code} para ver seus dados.
Acesse http://127.0.0.1:8000/docs para ver a documentação interativa e testar a API.
O próximo passo para seu portfólio é aprender a publicar (fazer o deploy) essa API em um serviço como a AWS.

"""
# # --- 8. Explicação do Código ---
"""
Explicação dos Novos Endpoints
# GET /api/status/{contrato_id}:

O {contrato_id} na URL é um parâmetro de caminho.
A função get_status_by_id(contrato_id: str) recebe esse valor como argumento.
Isso permite buscar um recurso específico. Se não for encontrado, retorna 404 Not Found,
 uma prática padrão em APIs REST.


# PUT /api/status/{contrato_id}:

Usado para substituir completamente um recurso existente.
Recebe o ID pela URL e os novos dados completos no corpo da requisição (updated_data: StatusContrato).



# PATCH /api/status/{contrato_id}:

Usado para atualizar parcialmente um recurso.
Criamos um novo modelo Pydantic, StatusContratoUpdate, onde todos os campos são Optional. 
Isso significa que o cliente pode enviar apenas os campos que deseja alterar.



# DELETE /api/status/{contrato_id}:

Usado para remover um recurso.
Retorna o código 204 No Content para indicar que a operação foi bem-sucedida, 
mas não há conteúdo para retornar, conforme recomendado pelas boas práticas REST.

"""