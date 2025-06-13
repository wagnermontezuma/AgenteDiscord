import os
import shutil
import datetime
import sys

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}", file=sys.stderr)

def list_backups(base_backup_path):
    """Lista os diretórios de backup disponíveis."""
    if not os.path.exists(base_backup_path):
        log_error(f"Diretório de backups não encontrado: {base_backup_path}")
        return []
    
    backups = sorted([d for d in os.listdir(base_backup_path) if os.path.isdir(os.path.join(base_backup_path, d))], reverse=True)
    return backups

def restore_backup(backup_path, project_root):
    """Restaura os arquivos de um backup para o diretório raiz do projeto."""
    log_info(f"Iniciando restauração do backup de: {backup_path}")
    
    files_to_restore = [
        'response_cache.json',
        '.env',
        'config.py'
    ]

    all_restored = True
    for file_name in files_to_restore:
        source_file_path = os.path.join(backup_path, file_name)
        destination_file_path = os.path.join(project_root, file_name)

        if not os.path.exists(source_file_path):
            log_warning(f"Arquivo '{file_name}' não encontrado no backup. Pulando.")
            continue
        
        try:
            shutil.copy2(source_file_path, destination_file_path)
            log_info(f"Arquivo '{file_name}' restaurado para '{destination_file_path}'")
        except Exception as e:
            log_error(f"Erro ao restaurar '{file_name}': {e}")
            all_restored = False
    
    if all_restored:
        log_info("Restauração de backup concluída com sucesso!")
        return True
    else:
        log_error("A restauração do backup foi concluída com alguns erros. Verifique os logs acima.")
        return False

def log_warning(message):
    print(f"[WARNING] {message}", file=sys.stderr)

def main():
    project_root = os.path.join(os.path.dirname(__file__), '..')
    base_backup_dir = os.path.join(project_root, 'backups')

    log_info("Iniciando o script de recovery...")

    backups = list_backups(base_backup_dir)

    if not backups:
        log_info("Nenhum backup encontrado para restaurar.")
        sys.exit(0)

    log_info("Backups disponíveis (mais recente primeiro):")
    for i, backup in enumerate(backups):
        print(f"{i + 1}. {backup}")

    while True:
        try:
            choice = input("Digite o número do backup que deseja restaurar (ou 'q' para sair): ").strip().lower()
            if choice == 'q':
                log_info("Saindo do script de recovery.")
                sys.exit(0)
            
            index = int(choice) - 1
            if 0 <= index < len(backups):
                selected_backup_dir = os.path.join(base_backup_dir, backups[index])
                
                confirm = input(f"Tem certeza que deseja restaurar o backup '{backups[index]}' (s/n)? ").strip().lower()
                if confirm == 's':
                    if restore_backup(selected_backup_dir, project_root):
                        sys.exit(0)
                    else:
                        sys.exit(1)
                else:
                    log_info("Restauração cancelada.")
            else:
                log_error("Escolha inválida. Por favor, digite um número válido.")
        except ValueError:
            log_error("Entrada inválida. Por favor, digite um número.")
        except Exception as e:
            log_error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()
