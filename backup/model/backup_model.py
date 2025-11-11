import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from utils.utils import resource_path # Usamos para encontrar o config.json

# Caminho para o arquivo de configuração
CONFIG_FILE = resource_path("utils/json/config.json")

class BackupModel:
    """
    Lida com a lógica de ler a configuração e executar a cópia dos arquivos
    de banco de dados para o backup.
    """

    def _load_config(self):
        """Carrega o arquivo config.json."""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar config.json: {e}")
            return {}

    def _save_config(self, config_data):
        """Salva os dados de volta no config.json."""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")
            return False

    def get_db_paths(self):
        """
        Lê o config.json e retorna os caminhos *completos* para os
        arquivos de banco de dados de Contratos e Atas.
        """
        config = self._load_config()
        path_contratos_folder = config.get("db_path_contratos")
        path_atas_folder = config.get("db_path_atas")

        db_contratos_path = None
        db_atas_path = None

        if path_contratos_folder:
            db_contratos_path = Path(path_contratos_folder) / "gerenciador_uasg.db"
        if path_atas_folder:
            db_atas_path = Path(path_atas_folder) / "atas_controle.db"

        return db_contratos_path, db_atas_path

    def get_backup_location(self):
        """Lê o local de backup salvo no config.json."""
        config = self._load_config()
        return config.get("local_backup", "") # Retorna "" se não estiver definido

    def save_backup_location(self, path):
        """Salva o local de backup escolhido pelo usuário no config.json."""
        config = self._load_config()
        config["local_backup"] = path
        self._save_config(config)

    def perform_backup(self, dest_folder_str, backup_contratos, backup_atas):
        """
        Executa a operação de cópia dos bancos de dados para o destino.
        """
        db_contratos, db_atas = self.get_db_paths()
        today_str = datetime.now().strftime("%d-%m-%Y")
        dest_path = Path(dest_folder_str)
        
        folders_created = []

        try:
            # Backup de Contratos
            if backup_contratos and db_contratos and db_contratos.exists():
                backup_dir_contratos = dest_path / "Contratos" / f"{today_str}-Contratos"
                os.makedirs(backup_dir_contratos, exist_ok=True)
                shutil.copy2(db_contratos, backup_dir_contratos / "gerenciador_uasg.db")
                folders_created.append(str(backup_dir_contratos))
            
            # Backup de Atas
            if backup_atas and db_atas and db_atas.exists():
                backup_dir_atas = dest_path / "Atas" / f"{today_str}-Atas"
                os.makedirs(backup_dir_atas, exist_ok=True)
                shutil.copy2(db_atas, backup_dir_atas / "atas_controle.db")
                folders_created.append(str(backup_dir_atas))
                
            if not folders_created:
                return False, "Nenhum arquivo de banco de dados foi encontrado para fazer backup."

            return True, f"Backup concluído com sucesso para:\n" + "\n".join(folders_created)

        except Exception as e:
            return False, f"Ocorreu um erro durante o backup: {e}"
