import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import zipfile
from utils.utils import resource_path # Usamos para encontrar o config.json
from Contratos.controller.email_controller import EmailController

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
    
    # --- Funções de Backup Local ---

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
        
    # --- Novas Funções de Backup Online ---

    def get_backup_email(self):
        """
        Retorna o e-mail de destino para backup online.
        Prioridade 1: Salvo no config.json ("email_backup_diferente")
        Prioridade 2: Definido no .env (EMAIL_BACKUP)
        """
        
        # Prioridade 1: Tenta pegar o e-mail salvo no config.json primeiro
        config = self._load_config()
        email_json = config.get("email_backup_diferente")
        if email_json:
            return email_json # Retorna o e-mail customizado pelo usuário

        # Prioridade 2: Se não houver e-mail customizado, pega o padrão do .env
        email_env = os.getenv('EMAIL_BACKUP')
        if email_env:
            return email_env # Retorna o e-mail padrão do sistema
        
        return "" # Retorna vazio se não encontrar em lugar nenhum

    def save_backup_email(self, email):
        """Salva o e-mail de destino no config.json."""
        config = self._load_config()
        config["email_backup_diferente"] = email
        return self._save_config(config)

    def perform_online_backup(self, email_dest, backup_contratos, backup_atas):
        """
        Compacta os bancos de dados selecionados e os envia por e-mail.
        """
        db_contratos, db_atas = self.get_db_paths()
        today_str = datetime.now().strftime("%d-%m-%Y")
        zip_filename = f"Backup_CA360_{today_str}.zip"
        zip_path = Path(zip_filename)

        # Limite de 25MB (em bytes)
        MAX_SIZE = 25 * 1024 * 1024 

        try:
            # 1. Criar o arquivo Zip
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if backup_contratos and db_contratos and db_contratos.exists():
                    # Adiciona ao zip com a estrutura de pasta "Contratos/"
                    zf.write(db_contratos, arcname=f"Contratos/gerenciador_uasg.db")
                
                if backup_atas and db_atas and db_atas.exists():
                    # Adiciona ao zip com a estrutura de pasta "Atas/"
                    zf.write(db_atas, arcname=f"Atas/atas_controle.db")

            # 2. Verificar se algo foi adicionado e o tamanho do arquivo
            if zip_path.stat().st_size == 0:
                return False, "Nenhum arquivo de banco de dados foi encontrado para o backup."
            
            if zip_path.stat().st_size > MAX_SIZE:
                return False, (f"Erro: O arquivo de backup ({zip_path.stat().st_size // (1024*1024)}MB) "
                               f"excede o limite de 25MB para envio por e-mail.")

            # 3. Enviar o e-mail usando o EmailController existente
            email_controller = EmailController()
            subject = f"Backup CA 360 - {today_str}"
            body = "Backup dos bancos de dados (Contratos e/ou Atas) do sistema CA 360 em anexo."
            
            success, message = email_controller.send_email(email_dest, subject, body, str(zip_path))
            
            return success, message

        except Exception as e:
            return False, f"Erro ao criar ou enviar o backup online: {e}"
        finally:
            # 4. Limpar o arquivo .zip temporário
            if zip_path.exists():
                os.remove(zip_path)
