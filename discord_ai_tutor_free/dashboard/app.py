from flask import Flask, render_template, jsonify
import sys
import os
import json
import asyncio
import threading
import time
import logging

# Adiciona o diretório raiz do projeto ao sys.path para importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.free_tier_orchestrator import FreeTierOrchestrator
from tools.metrics import ProductionMetrics
from tools.alert_system import AlertSystem
from deploy.health_check import collect_system_metrics # Para coletar métricas de sistema

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Instâncias globais para o orquestrador e coletor de métricas
# Estas instâncias devem ser as mesmas usadas pelo bot principal para ter métricas reais
# Para simplificar, vamos instanciá-las aqui. Em um ambiente de produção real,
# elas seriam compartilhadas ou expostas de forma mais robusta (e.g., via Prometheus).
orchestrator = None
metrics_collector = ProductionMetrics()
alert_system = AlertSystem(metrics_collector)

# Função para inicializar o orquestrador (pode ser chamado uma vez)
def initialize_orchestrator():
    global orchestrator
    if orchestrator is None:
        try:
            orchestrator = FreeTierOrchestrator()
            logger.info("Orchestrator inicializado para o dashboard.")
        except ValueError as e:
            logger.error(f"Erro ao inicializar Orchestrator: {e}. Verifique GOOGLE_API_KEY.")
            orchestrator = None # Garante que o orquestrador seja None em caso de falha

# Thread para coletar métricas de sistema periodicamente
def metrics_collection_thread():
    while True:
        collect_system_metrics(metrics_collector)
        # Atualiza métricas do orquestrador se ele estiver disponível
        if orchestrator:
            stats = orchestrator.get_usage_stats()
            # As métricas do orquestrador já são atualizadas no próprio orquestrador
            # e passadas para o metrics_collector via alert_system.
            # Apenas garantir que o metrics_collector tenha os dados mais recentes
            # do orquestrador.
            metrics_collector.update_metric('response_time_avg', stats['production_metrics']['response_time_avg'])
            metrics_collector.update_metric('api_quota_usage', stats['production_metrics']['api_quota_usage'])
            metrics_collector.update_metric('cache_efficiency', stats['production_metrics']['cache_efficiency'])
            metrics_collector.update_metric('error_rate', stats['production_metrics']['error_rate'])
            # user_satisfaction não é atualizado aqui, pois é uma métrica mais complexa
        
        # Verifica alertas
        active_alerts = alert_system.check_alerts()
        metrics_collector.update_metric('active_alerts', active_alerts) # Adiciona alertas às métricas

        time.sleep(10) # Coleta métricas a cada 10 segundos

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/metrics')
def get_metrics():
    # Retorna todas as métricas coletadas
    return jsonify(metrics_collector.metrics)

@app.route('/health')
def health_check():
    # Retorna o status de saúde básico
    return jsonify({"status": "ok", "metrics_collector_initialized": True, "orchestrator_initialized": orchestrator is not None})

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Inicializa o orquestrador em uma thread separada ou antes de iniciar o Flask
    # Para um ambiente de produção, o orquestrador seria um serviço separado
    # e o dashboard apenas consumiria suas métricas.
    # Aqui, para demonstração, inicializamos e coletamos métricas na mesma aplicação.
    initialize_orchestrator()

    # Inicia a thread de coleta de métricas
    metrics_thread = threading.Thread(target=metrics_collection_thread, daemon=True)
    metrics_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=True)
