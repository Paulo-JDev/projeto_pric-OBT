# backup/model/backup_model.py

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import zipfile
# from utils.utils import resource_path # ✅ Removido, pois base_dir já lida com isso de forma mais robusta
from Contratos.controller.email_controller import EmailController

try:
    base_dir = Path(os.environ.get("_MEIPASS", Path.cwd()))
except Exception:
    base_dir = Path.cwd()

# Arquivo de configuração
CONFIG_FILE = base_dir / "utils" / "json" / "config.json"

class BackupModel:
    """
    Lida com a lógica de ler a configuração e executar a cópia dos arquivos
    de banco de dados para o backup.
    """
    def __init__(self):
        """
        Inicializa o BackupModel e garante que os caminhos padrão dos DBs
        estejam no config.json se ainda não estiverem definidos.
        """
        self._ensure_default_db_paths_in_config() # ✅ NOVO MÉTODO CHAMADO AQUI

    def _load_config(self):
        """Carrega o arquivo config.json."""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Se o arquivo não existe, retorna um dicionário vazio
            return {}
        except Exception as e:
            print(f"Erro ao carregar config.json: {e}")
            return {}

    def _save_config(self, config_data):
        """Salva os dados de volta no config.json."""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")
            return False

    def _ensure_default_db_paths_in_config(self):
        """
        ✅ NOVO MÉTODO: Garante que os caminhos padrão dos bancos de dados
        (Contratos e Atas) estejam definidos no config.json.
        Se não existirem, os define para a pasta 'database' dentro de base_dir.
        """
        config = self._load_config()

        # Caminho padrão para a pasta 'database'
        default_db_folder = base_dir / "database"

        # Verifica e define o caminho padrão para Contratos
        if "db_path_contratos" not in config or not config["db_path_contratos"]:
            config["db_path_contratos"] = str(default_db_folder)
            print(f"ℹ️ Configurando caminho padrão para DB Contratos: {default_db_folder}")

        # Verifica e define o caminho padrão para Atas
        if "db_path_atas" not in config or not config["db_path_atas"]:
            config["db_path_atas"] = str(default_db_folder)
            print(f"ℹ️ Configurando caminho padrão para DB Atas: {default_db_folder}")

        # Salva as alterações se houveram
        self._save_config(config)

    def get_db_paths(self):
        """
        Lê o config.json e retorna os caminhos *completos* para os
        arquivos de banco de dados de Contratos e Atas.
        """
        config = self._load_config()

        # ✅ Agora, o _ensure_default_db_paths_in_config já garantiu que esses campos existam.
        # Se o usuário mudou, pegamos o que ele mudou. Se não, pegamos o padrão.
        path_contratos_folder = config.get("db_path_contratos")
        path_atas_folder = config.get("db_path_atas")

        db_contratos_path = None
        db_atas_path = None

        if path_contratos_folder:
            # ✅ Verifica se o caminho é um arquivo .db direto ou uma pasta
            path_obj = Path(path_contratos_folder)
            if path_obj.suffix == '.db':
                db_contratos_path = path_obj
            else:
                db_contratos_path = path_obj / "gerenciador_uasg.db"

        if path_atas_folder:
            # ✅ Verifica se o caminho é um arquivo .db direto ou uma pasta
            path_obj = Path(path_atas_folder)
            if path_obj.suffix == '.db':
                db_atas_path = path_obj
            else:
                db_atas_path = path_obj / "atas_controle.db"

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
        folders_created = [] # Para armazenar as pastas criadas e removê-las em caso de erro

        try:
            # Garante que a pasta de destino exista
            dest_path.mkdir(parents=True, exist_ok=True)

            # Backup Contratos
            if backup_contratos and db_contratos and db_contratos.exists():
                # Cria uma subpasta para contratos dentro do destino
                contratos_backup_folder = dest_path / f"Contratos_{today_str}"
                contratos_backup_folder.mkdir(parents=True, exist_ok=True)
                folders_created.append(contratos_backup_folder)

                # Copia o arquivo do banco de dados
                shutil.copy2(db_contratos, contratos_backup_folder / db_contratos.name)
                print(f"✅ Backup de Contratos salvo em: {contratos_backup_folder / db_contratos.name}")
            elif backup_contratos:
                print(f"⚠️ Aviso: Banco de dados de Contratos não encontrado em {db_contratos}. Backup ignorado.")

            # Backup Atas
            if backup_atas and db_atas and db_atas.exists():
                # Cria uma subpasta para atas dentro do destino
                atas_backup_folder = dest_path / f"Atas_{today_str}"
                atas_backup_folder.mkdir(parents=True, exist_ok=True)
                folders_created.append(atas_backup_folder)

                # Copia o arquivo do banco de dados
                shutil.copy2(db_atas, atas_backup_folder / db_atas.name)
                print(f"✅ Backup de Atas salvo em: {atas_backup_folder / db_atas.name}")
            elif backup_atas:
                print(f"⚠️ Aviso: Banco de dados de Atas não encontrado em {db_atas}. Backup ignorado.")

            return True, "Backup local realizado com sucesso!"

        except FileNotFoundError as e:
            # Tenta limpar pastas criadas se o erro for FileNotFoundError
            for folder in folders_created:
                if folder.exists():
                    shutil.rmtree(folder)
            return False, f"Erro: Arquivo não encontrado durante o backup. Verifique os caminhos configurados. Detalhes: {e}"
        except Exception as e:
            # Tenta limpar pastas criadas em caso de qualquer outro erro
            for folder in folders_created:
                if folder.exists():
                    shutil.rmtree(folder)
            return False, f"Erro inesperado ao realizar backup local: {e}"

    # --- Funções de Backup Online (E-mail) ---
    def get_backup_email(self):
        """
        Lê o e-mail de destino para backup.
        Prioridade 1: E-mail customizado no config.json
        Prioridade 2: E-mail padrão do .env
        """
        config = self._load_config()
        # Prioridade 1: E-mail customizado pelo usuário
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
            if not zip_path.exists() or zip_path.stat().st_size == 0:
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
