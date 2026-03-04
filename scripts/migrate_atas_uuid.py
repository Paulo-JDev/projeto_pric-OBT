# scripts/migrate_atas_uuid.py
import sqlite3
import uuid
import os
from pathlib import Path

def migrate():
    # Caminho do banco de atas (ajustado para a sua estrutura)
    db_path = Path("database/atas_controle.db")
    
    if not db_path.exists():
        print(f"❌ Banco não encontrado em: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Adiciona a coluna uuid
        cursor.execute("PRAGMA table_info(registros_atas)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'uuid' not in columns:
            print("📝 Adicionando coluna 'uuid' em registros_atas...")
            cursor.execute("ALTER TABLE registros_atas ADD COLUMN uuid TEXT")
            conn.commit()
        
        # 2. Preenche registros que estão sem UUID
        cursor.execute("SELECT id FROM registros_atas WHERE uuid IS NULL OR uuid = ''")
        rows = cursor.fetchall()
        
        for (reg_id,) in rows:
            cursor.execute("UPDATE registros_atas SET uuid = ? WHERE id = ?", (str(uuid.uuid4()), reg_id))
        
        conn.commit()
        print(f"✅ Migração concluída: {len(rows)} registros atualizados.")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
