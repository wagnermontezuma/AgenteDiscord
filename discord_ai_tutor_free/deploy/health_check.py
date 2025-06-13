import os
import sys
import subprocess
import time
import json
import psutil # Importa psutil
from tools.metrics import ProductionMetrics # Importa ProductionMetrics

def log_info(message):
    print(f"[INFO] {message}")

def log_error(message):
    print(f"[ERROR] {message}", file=sys.stderr)

def check_docker_container_status(container_name):
    """Verifica se o container Docker está em execução."""
    log_info(f"Verificando o status do container Docker '{container_name}'...")
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", container_name],
            capture_output=True, text=True, check=True
        )
        status = result.stdout.strip()
        if status == "running":
            log_info(f"Container '{container_name}' está em execução.")
            return True
        else:
            log_error(f"Container '{container_name}' está no estado: {status}.")
            return False
    except subprocess.CalledProcessError as e:
        log_error(f"Erro ao verificar o status do container '{container_name}': {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        log_error("Comando 'docker' não encontrado. Certifique-se de que o Docker está instalado e no PATH.")
        return False

def check_bot_logs(container_name, keywords=["Logged in as", "ready"]):
    """Verifica os logs do container em busca de palavras-chave de sucesso."""
    log_info(f"Verificando os logs do container '{container_name}' em busca de mensagens de sucesso...")
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", "50"], # Últimas 50 linhas
            capture_output=True, text=True, check=True
        )
        logs = result.stdout
        
        found_keywords = []
        for keyword in keywords:
            if keyword in logs:
                found_keywords.append(keyword)
        
        if found_keywords:
            log_info(f"Palavras-chave de sucesso encontradas nos logs: {', '.join(found_keywords)}")
            return True
        else:
            log_error("Nenhuma palavra-chave de sucesso encontrada nos logs recentes.")
            log_info("Últimas 50 linhas de log:")
            print(logs)
            return False
    except subprocess.CalledProcessError as e:
        log_error(f"Erro ao ler os logs do container '{container_name}': {e.stderr.strip()}")
        return False

def check_response_cache_integrity(cache_file_path):
    """Verifica a integridade do arquivo de cache."""
    log_info(f"Verificando a integridade do arquivo de cache: {cache_file_path}...")
    if not os.path.exists(cache_file_path):
        log_info("Arquivo de cache não encontrado. Isso é normal para a primeira execução.")
        return True
    
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log_info("Arquivo de cache é um JSON válido.")
        # Opcional: Adicionar mais verificações de estrutura do cache aqui
        return True
    except json.JSONDecodeError:
        log_error("Arquivo de cache corrompido (JSON inválido).")
        return False
    except Exception as e:
        log_error(f"Erro ao ler o arquivo de cache: {e}")
        return False

def collect_system_metrics(metrics_collector: ProductionMetrics):
    """Coleta métricas de CPU, memória, disco e rede e as atualiza no coletor."""
    log_info("Coletando métricas de sistema...")
    
    # CPU Usage
    cpu_percent = psutil.cpu_percent(interval=1) # Bloqueia por 1 segundo para obter uma leitura significativa
    metrics_collector.update_metric('cpu_usage', cpu_percent)
    log_info(f"Uso de CPU: {cpu_percent}%")

    # Memory Usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    metrics_collector.update_metric('memory_usage', memory_percent)
    log_info(f"Uso de Memória: {memory_percent}%")

    # Disk Space
    disk = psutil.disk_usage('/') # Assume o diretório raiz, pode ser ajustado para um caminho específico
    disk_percent = disk.percent
    metrics_collector.update_metric('disk_space', disk_percent)
    log_info(f"Espaço em Disco: {disk_percent}% usado")

    # Network I/O (bytes enviados e recebidos)
    net_io_counters = psutil.net_io_counters()
    bytes_sent = net_io_counters.bytes_sent
    bytes_recv = net_io_counters.bytes_recv
    # Para uma métrica mais significativa, seria necessário calcular a taxa de I/O ao longo do tempo
    # Por enquanto, apenas registra os totais ou uma snapshot simples
    metrics_collector.update_metric('network_io', {'bytes_sent': bytes_sent, 'bytes_recv': bytes_recv})
    log_info(f"Network I/O: Enviado={bytes_sent} bytes, Recebido={bytes_recv} bytes")

    log_info("Métricas de sistema coletadas.")


def main():
    container_name = "discord-tutor-bot"
    # O script health_check.py está em discord_ai_tutor_free/deploy
    # O response_cache.json está em discord_ai_tutor_free/
    cache_file_path = os.path.join(os.path.dirname(__file__), '..', 'response_cache.json')
    
    metrics_collector = ProductionMetrics() # Instancia o coletor de métricas

    log_info("Iniciando verificação de saúde pós-deploy...")

    # 1. Verificar status do container Docker
    if not check_docker_container_status(container_name):
        log_error("Verificação de saúde falhou: Container Docker não está em execução ou não existe.")
        sys.exit(1)

    # Dar um pequeno tempo para o bot inicializar dentro do container
    log_info("Aguardando 10 segundos para o bot inicializar...")
    time.sleep(10)

    # 2. Verificar logs do bot
    if not check_bot_logs(container_name):
        log_error("Verificação de saúde falhou: Mensagens de sucesso não encontradas nos logs do bot.")
        sys.exit(1)
    
    # 3. Verificar integridade do cache (se existir)
    # 3. Verificar integridade do cache (se existir)
    if not check_response_cache_integrity(cache_file_path):
        log_error("Verificação de saúde falhou: Arquivo de cache corrompido.")
        sys.exit(1)

    # 4. Coletar métricas de sistema
    collect_system_metrics(metrics_collector)
    log_info(f"Métricas de Produção Coletadas: {metrics_collector.metrics}")

    log_info("Todas as verificações de saúde passaram com sucesso! O bot parece estar funcionando corretamente.")
    sys.exit(0)

if __name__ == "__main__":
    main()
