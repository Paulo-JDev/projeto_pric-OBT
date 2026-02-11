# scripts/add_uuid_migration.py
import sys
import os
import uuid
import sqlite3

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def add_uuid_to_existing_records():
    """Adiciona UUID a todos os registros usando SQLite direto (sem SQLAlchemy)."""
    print("🔄 Iniciando migração de UUID...")

    # Caminho do banco de dados (ajuste se necessário)
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'gerenciador_uasg.db')

    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Verifica se a coluna uuid já existe
        cursor.execute("PRAGMA table_info(registros_status)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'uuid' not in columns:
            print("📝 Adicionando coluna 'uuid' na tabela registros_status...")
            cursor.execute("ALTER TABLE registros_status ADD COLUMN uuid TEXT")
            conn.commit()
            print("✅ Coluna 'uuid' adicionada!")
        else:
            print("ℹ️ Coluna 'uuid' já existe")

        # 2. Busca registros sem UUID
        cursor.execute("SELECT id FROM registros_status WHERE uuid IS NULL OR uuid = ''")
        registros_sem_uuid = cursor.fetchall()

        if not registros_sem_uuid:
            print("✅ Todos os registros já possuem UUID!")
            return

        print(f"📊 Encontrados {len(registros_sem_uuid)} registros sem UUID")

        # 3. Adiciona UUID a cada registro
        for i, (registro_id,) in enumerate(registros_sem_uuid, 1):
            novo_uuid = str(uuid.uuid4())
            cursor.execute(
                "UPDATE registros_status SET uuid = ? WHERE id = ?",
                (novo_uuid, registro_id)
            )

            if i % 100 == 0:  # Progresso a cada 100
                print(f"   Processados {i}/{len(registros_sem_uuid)}...")

        conn.commit()
        print(f"✅ {len(registros_sem_uuid)} registros atualizados com UUID com sucesso!")

        # 4. Verifica resultado
        cursor.execute("SELECT COUNT(*) FROM registros_status WHERE uuid IS NULL OR uuid = ''")
        restantes = cursor.fetchone()[0]

        if restantes == 0:
            print("🎉 Migração concluída! Todos os registros têm UUID.")
        else:
            print(f"⚠️ Ainda restam {restantes} registros sem UUID")

    except Exception as e:
        conn.rollback()
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("🔒 Conexão com banco fechada")

if __name__ == "__main__":
    add_uuid_to_existing_records()
    print("✅ Migração concluida!")
