import google.generativeai as genai
import logging
import asyncio
import time
from typing import Optional, List, Dict, Any, NamedTuple
from tools.response_cache import ResponseCache
from config import GOOGLE_API_KEY, CACHE_FILE, CACHE_EXPIRATION_TIME
from utils.prompt_builder import PromptBuilder
from tools.metrics import ProductionMetrics
from tools.alert_system import AlertSystem # Importa AlertSystem

logger = logging.getLogger(__name__)

class Agent(NamedTuple):
    """Representa um agente especializado com suas configurações."""
    name: str
    model: str
    instruction: str

class FreeTierOrchestrator:
    def __init__(self, default_model_name: str = "gemini-pro"):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY não está configurada nas variáveis de ambiente.")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        self.default_model_name = default_model_name
        self.cache = ResponseCache(cache_file=CACHE_FILE, ttl_hours=CACHE_EXPIRATION_TIME / 3600)
        self.prompt_builder = PromptBuilder() # Instancia o PromptBuilder
        
        self._agent_configs = self._define_agent_configs() # Define as configurações dos agentes
        self.agents: Dict[str, Agent] = {} # Agentes serão carregados sob demanda
        self.metrics_collector = ProductionMetrics() # Instancia o coletor de métricas
        self.alert_system = AlertSystem(self.metrics_collector) # Instancia o sistema de alertas
        self.api_calls_made = 0 # Manter para compatibilidade e transição
        self.cache_hits_saved = 0 # Manter para compatibilidade e transição
        self.agent_metrics: Dict[str, Dict[str, int]] = {} # Métricas por agente, inicializadas no lazy load

        # Rate Limiting: 10 requests por minuto (60 segundos / 10 requests = 6 segundos por request)
        self.rate_limit_interval = 60 / 10 # Segundos entre requests
        self.last_request_time = 0.0
        self.rate_limit_semaphore = asyncio.Semaphore(1) # Garante que apenas 1 request por vez respeite o intervalo
        self.total_response_time = 0
        self.successful_api_calls = 0

        logger.info(f"FreeTierOrchestrator inicializado. Agentes serão carregados sob demanda.")

    def _define_agent_configs(self) -> Dict[str, Dict[str, str]]:
        """Define as configurações dos agentes especializados."""
        return {
            "concept": {
                "name": "ConceptExplainer",
                "model": "gemini-pro",
                "instruction": """
Você é um tutor especialista em IA que explica conceitos de forma clara e didática.
REGRAS: Respostas CONCISAS (máximo 300 palavras), use analogias simples,
termine com uma pergunta para verificar a compreensão do usuário.
"""
            },
            "code": {
                "name": "CodeHelper",
                "model": "gemini-pro",
                "instruction": """
Você é um assistente de programação especializado em IA. Forneça exemplos de código,
ajude a depurar e explique implementações.
REGRAS: Forneça código funcional, explique cada parte do código,
seja direto e objetivo.
"""
            },
            "resource": {
                "name": "ResourceRecommender",
                "model": "gemini-pro",
                "instruction": """
Você é um recomendador de recursos de aprendizado de IA. Recomende materiais
gratuitos como cursos, livros, tutoriais e artigos.
REGRAS: Foque em recursos GRATUITOS e de alta qualidade,
forneça links se possível (mesmo que placeholders), seja encorajador.
"""
            },
            "general": { # Agente de fallback para perguntas gerais
                "name": "GeneralResponder",
                "model": "gemini-pro",
                "instruction": """
Você é um assistente de IA amigável e prestativo. Responda a perguntas gerais
de forma educada e concisa.
"""
            }
        }

    def _get_agent(self, agent_key: str) -> Agent:
        """Retorna uma instância de agente, inicializando-a se necessário (lazy loading)."""
        if agent_key not in self.agents:
            config = self._agent_configs.get(agent_key)
            if not config:
                logger.warning(f"Configuração de agente para '{agent_key}' não encontrada. Usando agente 'general'.")
                config = self._agent_configs["general"]
                agent_key = "general" # Garante que a chave do agente seja 'general' para métricas

            self.agents[agent_key] = Agent(
                name=config["name"],
                model=config["model"],
                instruction=config["instruction"]
            )
            # Inicializa as métricas para o agente se ainda não existirem
            if self.agents[agent_key].name not in self.agent_metrics:
                self.agent_metrics[self.agents[agent_key].name] = {"api_calls": 0, "cache_hits": 0}
            logger.info(f"Agente '{self.agents[agent_key].name}' carregado sob demanda.")
        return self.agents[agent_key]

    async def _apply_rate_limit(self):
        """Aplica o rate limiting para chamadas à API."""
        async with self.rate_limit_semaphore:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_interval:
                wait_time = self.rate_limit_interval - elapsed
                logger.warning(f"Rate limit atingido. Aguardando {wait_time:.2f} segundos.")
                await asyncio.sleep(wait_time)
            self.last_request_time = time.time()

    async def _call_gemini_api(self, agent: Agent, user_question: str, max_retries: int = 3, initial_backoff: int = 1, user_level: str = "iniciante", language: str = "pt") -> Optional[str]:
        """
        Faz uma chamada à API do Google Gemini com retries e backoff exponencial,
        usando o PromptBuilder para construir o prompt.
        """
        # Prepara os dados para o PromptBuilder
        prompt_data = {
            "question": user_question,
            "topic": user_question, # Usar a pergunta como tópico inicial, pode ser refinado
            "user_level": user_level,
            "language": language # Para templates que usam idioma
        }
        
        # Constrói o prompt otimizado usando o PromptBuilder
        # Define um limite de tokens para o prompt de entrada (ex: 1000 tokens)
        full_prompt = self.prompt_builder.optimize_prompt(agent.name.lower().replace("explainer", "").replace("helper", "").replace("recommender", "").replace("responder", ""), prompt_data, max_tokens=1000)
        
        if not full_prompt:
            logger.error(f"Falha ao construir o prompt para o agente '{agent.name}'.")
            return None

        for attempt in range(max_retries):
            await self._apply_rate_limit() # Aplica rate limit antes de cada tentativa
            start_time = time.time() # Inicia a contagem do tempo de resposta
            try:
                model_instance = genai.GenerativeModel(agent.model)
                
                logger.info(f"Chamando API para agente '{agent.name}' (tentativa {attempt + 1}/{max_retries}). Prompt: '{full_prompt[:50]}...'")
                response = await model_instance.generate_content_async(full_prompt)
                
                end_time = time.time()
                response_time = end_time - start_time
                self.total_response_time += response_time
                self.successful_api_calls += 1
                self.metrics_collector.update_metric('response_time_avg', self.total_response_time / self.successful_api_calls)
                self.metrics_collector.update_metric('api_quota_usage', self.api_calls_made + 1) # Incrementa o uso da cota
                
                self.api_calls_made += 1 # Manter para compatibilidade
                self.agent_metrics[agent.name]["api_calls"] += 1
                
                if response and response.candidates and response.candidates[0].content.parts:
                    generated_text = response.candidates[0].content.parts[0].text
                    logger.info(f"Resposta da API recebida para agente '{agent.name}'. Tempo: {response_time:.2f}s")
                    self.metrics_collector.update_metric('error_rate', 0) # Reseta a taxa de erro se a chamada for bem-sucedida
                    self.alert_system.reset_api_failures() # Reseta o contador de falhas consecutivas
                    return generated_text
                else:
                    logger.warning(f"Resposta da API vazia ou em formato inesperado para agente '{agent.name}'.")
                    self.metrics_collector.update_metric('error_rate', self.metrics_collector.get_metric('error_rate') + 1) # Incrementa erro
                    self.alert_system.increment_api_failure() # Incrementa falha consecutiva
                    return None
            except genai.types.BlockedPromptException as e:
                logger.error(f"Prompt bloqueado pela API para agente '{agent.name}': {e}")
                self.metrics_collector.update_metric('error_rate', self.metrics_collector.get_metric('error_rate') + 1) # Incrementa erro
                self.alert_system.increment_api_failure() # Incrementa falha consecutiva
                return "Desculpe, sua pergunta foi bloqueada pelo filtro de segurança da IA. Por favor, tente reformular."
            except Exception as e:
                logger.error(f"Erro na chamada da API para agente '{agent.name}' (tentativa {attempt + 1}/{max_retries}): {e}")
                self.metrics_collector.update_metric('error_rate', self.metrics_collector.get_metric('error_rate') + 1) # Incrementa erro
                self.alert_system.increment_api_failure() # Incrementa falha consecutiva
                if attempt < max_retries - 1:
                    wait_time = initial_backoff * (2 ** attempt)
                    logger.info(f"Retentando em {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Todas as {max_retries} tentativas falharam para agente '{agent.name}'.")
        return None

    async def generate_response(self, prompt: str, classification_result: Dict[str, Any], use_cache: bool = True) -> Optional[str]:
        """
        Gera uma resposta usando o modelo Gemini, roteando para o agente apropriado.
        Integra cache, rate limiting, retries e fallbacks.
        """
        # 1. Tenta buscar no cache primeiro
        if use_cache:
            cached_response = self.cache.get_cached_response(prompt)
            if cached_response:
                self.cache_hits_saved += 1 # Manter para compatibilidade
                # Atribui o hit ao agente principal da classificação, se houver
                main_category = classification_result['categories'][0] if classification_result['categories'] else "general"
                # Ajusta o nome da categoria para corresponder às chaves do self.agents
                if main_category == "concept": agent_key = "concept"
                elif main_category == "code": agent_key = "code"
                elif main_category == "resource": agent_key = "resource"
                else: agent_key = "general"

                if agent_key in self.agents:
                    self.agent_metrics[self.agents[agent_key].name]["cache_hits"] += 1
                
                # Atualiza a métrica de eficiência do cache
                total_requests = self.api_calls_made + self.cache_hits_saved + 1 # +1 para a requisição atual
                cache_efficiency = (self.cache_hits_saved + 1) / total_requests if total_requests > 0 else 0
                self.metrics_collector.update_metric('cache_efficiency', cache_efficiency)

                logger.info(f"Resposta recuperada do cache para o prompt: '{prompt[:50]}...'")
                return cached_response

        # 2. Roteamento para o agente apropriado
        # Prioriza a primeira categoria classificada, ou usa 'general' como fallback
        target_category = classification_result['categories'][0] if classification_result['categories'] else "general"
        
        # Mapeia a categoria do classificador para a chave do agente
        if target_category == "concept": agent_key = "concept"
        elif target_category == "code": agent_key = "code"
        elif target_category == "resource": agent_key = "resource"
        else: agent_key = "general" # Fallback para 'general' se a categoria não for mapeada

        agent = self._get_agent(agent_key) # Usa o método de lazy loading

        logger.info(f"Roteando para o agente: {agent.name} (Classificação: {classification_result['categories']})")

        # 3. Chama a API com retries e rate limiting, passando dados para o PromptBuilder
        response = await self._call_gemini_api(
            agent, 
            prompt, 
            user_level="iniciante", # Placeholder, idealmente viria do contexto do usuário
            language=classification_result.get('language', 'pt') # Usa idioma detectado
        )

        # 4. Fallback para cache em caso de falha da API
        if response is None:
            logger.warning(f"Falha na API para o agente '{agent.name}'. Tentando fallback para cache (se houver).")
            cached_response_fallback = self.cache.get_cached_response(prompt)
            if cached_response_fallback:
                self.cache_hits_saved += 1 # Manter para compatibilidade
                if agent_key in self.agents:
                    self.agent_metrics[self.agents[agent_key].name]["cache_hits"] += 1
                
                # Atualiza a métrica de eficiência do cache
                total_requests = self.api_calls_made + self.cache_hits_saved + 1 # +1 para a requisição atual
                cache_efficiency = (self.cache_hits_saved + 1) / total_requests if total_requests > 0 else 0
                self.metrics_collector.update_metric('cache_efficiency', cache_efficiency)

                logger.info(f"Resposta recuperada do cache como fallback para o prompt: '{prompt[:50]}...'")
                return cached_response_fallback
            else:
                logger.error(f"Nenhuma resposta da API e nenhum fallback de cache para o prompt: '{prompt[:50]}...'")
                return "Desculpe, não consegui processar sua solicitação no momento. Por favor, tente novamente mais tarde."
        
        # 5. Armazena a resposta da API no cache
        if use_cache and response:
            self.cache.cache_response(prompt, response)
            logger.debug(f"Resposta da API armazenada em cache para o prompt: '{prompt[:50]}...'")
        
        return response

    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso da API e do cache, incluindo por agente."""
        cache_stats = self.cache.get_stats()
        
        # Atualiza as métricas no coletor antes de retornar
        self.metrics_collector.update_metric('api_quota_usage', self.api_calls_made)
        self.metrics_collector.update_metric('cache_efficiency', 
            (self.cache_hits_saved / (self.api_calls_made + self.cache_hits_saved)) if (self.api_calls_made + self.cache_hits_saved) > 0 else 0
        )
        # user_satisfaction e outras métricas de sistema seriam atualizadas por outros módulos/ferramentas
        
        return {
            "api_calls_total": self.api_calls_made,
            "cache_hits_total": self.cache_hits_saved,
            "total_requests_processed": self.api_calls_made + self.cache_hits_saved,
            "cache_stats": cache_stats,
            "agent_metrics": self.agent_metrics,
            "production_metrics": self.metrics_collector.metrics, # Inclui as métricas avançadas
            "active_alerts": self.alert_system.check_alerts() # Inclui os alertas ativos
        }

    def reset_stats(self):
        """Reseta as estatísticas de uso."""
        self.api_calls_made = 0
        self.cache_hits_saved = 0
        self.total_response_time = 0
        self.successful_api_calls = 0
        self.cache.reset_stats()
        # Resetar agent_metrics para apenas os agentes que foram carregados
        for agent_name in self.agent_metrics:
            self.agent_metrics[agent_name] = {"api_calls": 0, "cache_hits": 0}
        self.metrics_collector = ProductionMetrics() # Reseta o coletor de métricas também
        self.alert_system = AlertSystem(self.metrics_collector) # Reseta o sistema de alertas
        logger.info("Estatísticas de uso do orquestrador resetadas.")

# Exemplo de uso (para testes internos, pode ser removido em produção)
if __name__ == "__main__":
    import sys
    from tools.simple_classifier import SimpleClassifier # Importa o classificador

    # Adiciona um manipulador de console para ver os logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG) # Define o nível de logging para DEBUG para ver mais detalhes

    # Mock da chave API para evitar erro de configuração em teste local sem .env
    # Em um ambiente real, GOOGLE_API_KEY viria do config.py
    if not GOOGLE_API_KEY:
        print("AVISO: GOOGLE_API_KEY não configurada. O teste de API real não funcionará.")
        print("Por favor, defina GOOGLE_API_KEY no seu arquivo .env para testes completos.")
        # Para permitir que o teste continue sem uma chave real, vamos mockar a resposta da API
        # Isso é apenas para o bloco __main__ e não afeta o comportamento real da classe.
        class MockGenerativeModel:
            def __init__(self, model_name):
                self.model_name = model_name
            async def generate_content_async(self, prompt):
                class MockCandidate:
                    class MockContent:
                        parts = [type('obj', (object,), {'text': f"Mocked response from {self.model_name} for: {prompt}"})()]
                    content = MockContent()
                return type('obj', (object,), {'candidates': [MockCandidate()]})()
        
        genai.GenerativeModel = MockGenerativeModel
        print("Usando modelo mockado para testes.")

    async def main_test():
        orchestrator = FreeTierOrchestrator()
        classifier = SimpleClassifier() # Instancia o classificador

        print("\n--- Teste de Geração de Resposta com Roteamento e Cache ---")
        
        # Teste 1: Pergunta de Conceito (MISS inicial)
        prompt1 = "O que é aprendizado de máquina?"
        classification1 = classifier.classify_question(prompt1)
        print(f"\nClassificação para '{prompt1}': {classification1['categories']}, Idioma: {classification1['language']}")
        response1 = await orchestrator.generate_response(prompt1, classification1)
        print(f"Prompt: '{prompt1}'\nResposta: '{response1}'")
        assert response1 is not None and "Mocked response from gemini-pro" in response1

        # Teste 2: Pergunta de Conceito (HIT do cache)
        response1_cached = await orchestrator.generate_response(prompt1, classification1)
        print(f"Prompt: '{prompt1}' (cached)\nResposta: '{response1_cached}'")
        assert response1_cached == response1

        # Teste 3: Pergunta de Código (MISS inicial)
        prompt2 = "Como faço um loop for em Python?"
        classification2 = classifier.classify_question(prompt2)
        print(f"\nClassificação para '{prompt2}': {classification2['categories']}, Idioma: {classification2['language']}")
        response2 = await orchestrator.generate_response(prompt2, classification2)
        print(f"Prompt: '{prompt2}'\nResposta: '{response2}'")
        assert response2 is not None and "Mocked response from gemini-pro" in response2

        # Teste 4: Pergunta de Recurso (MISS inicial)
        prompt3 = "Recomende um curso gratuito de deep learning."
        classification3 = classifier.classify_question(prompt3)
        print(f"\nClassificação para '{prompt3}': {classification3['categories']}, Idioma: {classification3['language']}")
        response3 = await orchestrator.generate_response(prompt3, classification3)
        print(f"Prompt: '{prompt3}'\nResposta: '{response3}'")
        assert response3 is not None and "Mocked response from gemini-pro" in response3

        # Teste 5: Pergunta Geral (MISS inicial)
        prompt4 = "Olá, tudo bem?"
        classification4 = classifier.classify_question(prompt4)
        print(f"\nClassificação para '{prompt4}': {classification4['categories']}, Idioma: {classification4['language']}")
        response4 = await orchestrator.generate_response(prompt4, classification4)
        print(f"Prompt: '{prompt4}'\nResposta: '{response4}'")
        assert response4 is not None and "Mocked response from gemini-pro" in response4

        # Teste 6: Pergunta em Inglês
        prompt5 = "What is machine learning?"
        classification5 = classifier.classify_question(prompt5)
        print(f"\nClassificação para '{prompt5}': {classification5['categories']}, Idioma: {classification5['language']}")
        response5 = await orchestrator.generate_response(prompt5, classification5, language=classification5['language'])
        print(f"Prompt: '{prompt5}'\nResposta: '{response5}'")
        assert response5 is not None and "Mocked response from gemini-pro" in response5

        print("\n--- Teste de Rate Limiting (simulado) ---")
        # Este teste é mais conceitual com o mock, mas a lógica de sleep será ativada
        for i in range(5):
            p = f"Pergunta de teste de rate limit {i+1}"
            c = classifier.classify_question(p)
            await orchestrator.generate_response(p, c)
            print(f"Request {i+1} enviado.")
        
        print("\n--- Teste de Estatísticas ---")
        stats = orchestrator.get_usage_stats()
        print(f"Estatísticas de Uso: {stats}")
        assert stats['api_calls_total'] >= 6 # Pelo menos 6 chamadas (1 por agente + 5 do rate limit)
        assert stats['cache_hits_total'] >= 1 # Pelo menos 1 hit do cache
        assert stats['agent_metrics']['ConceptExplainer']['api_calls'] >= 1
        assert stats['agent_metrics']['CodeHelper']['api_calls'] >= 1
        assert stats['agent_metrics']['ResourceRecommender']['api_calls'] >= 1
        assert stats['agent_metrics']['GeneralResponder']['api_calls'] >= 1

        print("\n--- Teste de Reset de Estatísticas ---")
        orchestrator.reset_stats()
        stats_after_reset = orchestrator.get_usage_stats()
        print(f"Estatísticas após reset: {stats_after_reset}")
        assert stats_after_reset['api_calls_total'] == 0
        assert stats_after_reset['cache_hits_total'] == 0
        assert stats_after_reset['agent_metrics']['ConceptExplainer']['api_calls'] == 0

        print("\nTestes do FreeTierOrchestrator concluídos.")

    # Executa o loop de eventos assíncrono
    asyncio.run(main_test())
