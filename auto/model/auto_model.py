# auto/model/auto_model.py

import os
import shutil
from pathlib import Path

class AutoModel:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.temp_dir = Path(base_dir) / "auto" / "temp_auto"

    def create_temp_folder(self):
        """Cria a pasta temporária para os JSONs."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return str(self.temp_dir)

    def clean_temp_folder(self):
        """Remove a pasta temporária e todo o seu conteúdo."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def replace_database(self, new_db_path, current_db_path):
        """Substitui o arquivo .db atual pelo novo selecionado."""
        import gc
        # Força o coletor de lixo a limpar objetos de conexão perdidos
        gc.collect() 
        
        if os.path.exists(current_db_path):
            os.remove(current_db_path)
        shutil.copy2(new_db_path, current_db_path)
