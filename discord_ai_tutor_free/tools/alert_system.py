import logging
from typing import Dict, Any
from tools.metrics import ProductionMetrics

logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self, metrics_collector: ProductionMetrics):
        self.metrics_collector = metrics_collector
        self.alert_thresholds = {
            'api_rate_limit_warning': 0.80, # 80% do limite de taxa
            'error_rate_critical': 0.05,   # 5% de taxa de erro
            'response_time_critical': 15,  # 15 segundos
            'cache_hit_rate_critical': 0.50, # 50% de taxa de acerto do cache
            'consecutive_api_failures_critical': 3 # 3 falhas consecutivas de API
        }
        self.consecutive_api_failures = 0

    def check_alerts(self) -> Dict[str, bool]:
        """Verifica as condições de alerta e retorna um dicionário de alertas ativos."""
        active_alerts = {}
        metrics = self.metrics_collector.metrics
        
        # Alerta: Rate limit próximo do limite (80%)
        # Esta métrica precisa ser calculada com base no uso real e no limite total.
        # Por enquanto, usaremos 'api_quota_usage' como um proxy para o número de chamadas.
        # Para ser preciso, precisaríamos saber o limite total da API por período.
        # Assumindo um limite hipotético de 1000 chamadas por minuto para exemplo.
        hypothetical_api_limit = 1000 
        api_usage_ratio = metrics.get('api_quota_usage', 0) / hypothetical_api_limit
        if api_usage_ratio >= self.alert_thresholds['api_rate_limit_warning']:
            active_alerts['api_rate_limit_warning'] = True
            logger.warning(f"ALERTA: Uso de API próximo do limite! ({api_usage_ratio:.2%})")
        
        # Alerta: Erro rate > 5%
        error_rate = metrics.get('error_rate', 0)
        if error_rate > self.alert_thresholds['error_rate_critical']:
            active_alerts['error_rate_critical'] = True
            logger.error(f"ALERTA: Taxa de erro crítica! ({error_rate:.2%})")

        # Alerta: Tempo de resposta > 15 segundos
        response_time_avg = metrics.get('response_time_avg', 0)
        if response_time_avg > self.alert_thresholds['response_time_critical']:
            active_alerts['response_time_critical'] = True
            logger.warning(f"ALERTA: Tempo de resposta médio crítico! ({response_time_avg:.2f}s)")

        # Alerta: Cache hit rate < 50%
        cache_efficiency = metrics.get('cache_efficiency', 0)
        if cache_efficiency < self.alert_thresholds['cache_hit_rate_critical']:
            active_alerts['cache_hit_rate_critical'] = True
            logger.warning(f"ALERTA: Eficiência do cache baixa! ({cache_efficiency:.2%})")

        # Alerta: Falhas de API consecutivas
        # Esta métrica precisa ser atualizada externamente (no orquestrador)
        if self.consecutive_api_failures >= self.alert_thresholds['consecutive_api_failures_critical']:
            active_alerts['consecutive_api_failures_critical'] = True
            logger.critical(f"ALERTA: {self.consecutive_api_failures} falhas consecutivas de API!")
        
        return active_alerts

    def increment_api_failure(self):
        """Incrementa o contador de falhas consecutivas de API."""
        self.consecutive_api_failures += 1
        logger.warning(f"Falha de API detectada. Falhas consecutivas: {self.consecutive_api_failures}")

    def reset_api_failures(self):
        """Reseta o contador de falhas consecutivas de API."""
        if self.consecutive_api_failures > 0:
            logger.info(f"Falhas consecutivas de API resetadas de {self.consecutive_api_failures} para 0.")
        self.consecutive_api_failures = 0

# Exemplo de uso (para testes internos)
if __name__ == "__main__":
    # Configura logging para ver as mensagens
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Cria um coletor de métricas mock para teste
    mock_metrics = ProductionMetrics()
    alert_system = AlertSystem(mock_metrics)

    print("--- Teste de Alertas ---")

    # Teste 1: Nenhuma alerta (valores padrão)
    print("\nCenário 1: Sem alertas")
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert not alerts

    # Teste 2: Alerta de tempo de resposta
    print("\nCenário 2: Tempo de resposta alto")
    mock_metrics.update_metric('response_time_avg', 20)
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert alerts.get('response_time_critical')

    # Teste 3: Alerta de taxa de erro
    print("\nCenário 3: Taxa de erro alta")
    mock_metrics.update_metric('error_rate', 0.06)
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert alerts.get('error_rate_critical')

    # Teste 4: Alerta de eficiência de cache baixa
    print("\nCenário 4: Eficiência de cache baixa")
    mock_metrics.update_metric('cache_efficiency', 0.40)
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert alerts.get('cache_hit_rate_critical')

    # Teste 5: Alerta de falhas consecutivas de API
    print("\nCenário 5: Falhas consecutivas de API")
    alert_system.increment_api_failure() # 1
    alert_system.increment_api_failure() # 2
    alert_system.increment_api_failure() # 3 - Deve disparar o alerta
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert alerts.get('consecutive_api_failures_critical')

    # Teste 6: Resetar falhas consecutivas
    print("\nCenário 6: Resetar falhas consecutivas")
    alert_system.reset_api_failures()
    alerts = alert_system.check_alerts()
    print(f"Alertas ativos: {alerts}")
    assert not alerts.get('consecutive_api_failures_critical')

    print("\nTestes do AlertSystem concluídos.")
