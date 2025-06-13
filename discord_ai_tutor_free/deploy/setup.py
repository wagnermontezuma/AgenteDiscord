import os
import sys
import subprocess

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}", file=sys.stderr)

def check_python_version():
    """Verifica se a versão do Python é 3.9 ou superior."""
    if sys.version_info < (3, 9):
        log_error("Python 3.9 ou superior é necessário. Por favor, atualize sua instalação do Python.")
        sys.exit(1)
    log_info(f"Versão do Python: {sys.version.split(' ')[0]} (OK)")

def create_venv():
    """Cria e ativa um ambiente virtual."""
    venv_path = os.path.join(os.path.dirname(__file__), '..', 'venv')
    if not os.path.exists(venv_path):
        log_info(f"Criando ambiente virtual em '{venv_path}'...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        log_info("Ambiente virtual criado com sucesso.")
    else:
        log_info("Ambiente virtual já existe.")

    # Ativar o ambiente virtual para o subprocesso
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")
    
    # Retorna o comando de ativação para ser usado em subprocessos
    return activate_script

def install_dependencies(activate_script):
    """Instala as dependências do requirements.txt."""
    requirements_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    if not os.path.exists(requirements_path):
        log_error(f"Arquivo requirements.txt não encontrado em '{requirements_path}'.")
        sys.exit(1)

    log_info("Instalando dependências...")
    # Usar o ambiente virtual para instalar as dependências
    if sys.platform == "win32":
        command = [activate_script, "&&", "pip", "install", "-r", requirements_path]
    else:
        command = ["bash", "-c", f"source {activate_script} && pip install -r {requirements_path}"]
    
    try:
        subprocess.run(command, check=True, shell=True) # shell=True é necessário para 'source' e '&&'
        log_info("Dependências instaladas com sucesso.")
    except subprocess.CalledProcessError:
        log_error("Falha ao instalar dependências.")
        sys.exit(1)

def setup_env_file():
    """Cria o arquivo .env se não existir."""
    env_example_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

    if not os.path.exists(env_example_path):
        log_error(f"Arquivo .env.example não encontrado em '{env_example_path}'.")
        sys.exit(1)

    if not os.path.exists(env_path):
        log_info(f"Criando arquivo .env a partir de .env.example em '{env_path}'...")
        try:
            with open(env_example_path, 'r') as f_example:
                content = f_example.read()
            with open(env_path, 'w') as f_env:
                f_env.write(content)
            log_info("Arquivo .env criado. Por favor, edite-o com suas credenciais.")
        except IOError as e:
            log_error(f"Erro ao criar .env: {e}")
            sys.exit(1)
    else:
        log_info("Arquivo .env já existe. Certifique-se de que suas credenciais estão configuradas.")

def main():
    log_info("Iniciando o script de setup automatizado para Discord AI Tutor Free...")
    
    check_python_version()
    activate_script = create_venv()
    install_dependencies(activate_script)
    setup_env_file()
    
    log_info("Setup concluído. Você pode ativar o ambiente virtual e executar o bot:")
    if sys.platform == "win32":
        log_info(f"Para Windows: .\\venv\\Scripts\\activate")
    else:
        log_info(f"Para macOS/Linux: source venv/bin/activate")
    log_info("Em seguida: python main.py")

if __name__ == "__main__":
    main()
