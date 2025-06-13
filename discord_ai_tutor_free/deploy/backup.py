import os
import shutil
import datetime
import sys

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}", file=sys.stderr)

def create_backup_directory(base_backup_path):
    """Cria o diretório de backup se não existir."""
    if not os.path.exists(base_backup_path):
        try:
            os.makedirs(base_backup_path)
            log_info(f"Diretório de backup criado: {base_backup_path}")
        except OSError as e:
            log_error(f"Erro ao criar diretório de backup '{base_backup_path}': {e}")
            sys.exit(1)
    else:
        log_info(f"Diretório de backup já existe: {base_backup_path}")

def backup_file(source_path, destination_dir):
    """Copia um arquivo para o diretório de backup."""
    if not os.path.exists(source_path):
        log_info(f"Arquivo não encontrado, pulando backup: {source_path}")
        return False
    
    file_name = os.path.basename(source_path)
    destination_path = os.path.join(destination_dir, file_name)
    
    try:
        shutil.copy2(source_path, destination_path)
        log_info(f"Backup de '{file_name}' criado em '{destination_dir}'")
        return True
    except Exception as e:
        log_error(f"Erro ao fazer backup de '{file_name}': {e}")
        return False

def main():
    # O script backup.py está em discord_ai_tutor_free/deploy
    # Os arquivos a serem backupeados estão em discord_ai_tutor_free/
    project_root = os.path.join(os.path.dirname(__file__), '..')

    response_cache_path = os.path.join(project_root, 'response_cache.json')
    env_path = os.path.join(project_root, '.env')
    config_path = os.path.join(project_root, 'config.py')

    # Diretório base para backups (pode ser configurável)
    # Ex: backups/2025-06-13_16-30-00/
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_backup_dir = os.path.join(project_root, 'backups')
    current_backup_dir = os.path.join(base_backup_dir, timestamp)

    log_info("Iniciando o script de backup...")

    create_backup_directory(current_backup_dir)

    files_to_backup = [
        response_cache_path,
        env_path,
        config_path
    ]

    all_backed_up = True
    for file_path in files_to_backup:
        if not backup_file(file_path, current_backup_dir):
            all_backed_up = False

    if all_backed_up:
        log_info(f"Backup completo criado em: {current_backup_dir}")
        sys.exit(0)
    else:
        log_error("O backup foi concluído com alguns erros. Verifique os logs acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
