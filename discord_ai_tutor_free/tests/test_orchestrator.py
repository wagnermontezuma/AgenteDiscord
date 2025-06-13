import pytest
import asyncio
import time
import logging
from unittest.mock import AsyncMock, MagicMock, patch

from utils.free_tier_orchestrator import FreeTierOrchestrator, Agent
from tools.response_cache import ResponseCache
from utils.prompt_builder import PromptBuilder
from config import GOOGLE_API_KEY

# Configura o logging para os testes
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_google_api():
    """Mocka a API do Google Generative AI."""
    with patch('google.generativeai.GenerativeModel') as MockModel:
        mock_instance = MockModel.return_value
        mock_instance.generate_content_async = AsyncMock()
        
        # Configura uma resposta padrão para o mock
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = "Mocked AI response."
        mock_instance.generate_content_async.return_value = mock_response
        
        yield MockModel

@pytest.fixture
def mock_response_cache():
    """Mocka a classe ResponseCache."""
    with patch('tools.response_cache.ResponseCache') as MockCache:
        mock_instance = MockCache.return_value
        mock_instance.get_cached_response = MagicMock(return_value=None)
        mock_instance.cache_response = MagicMock()
        mock_instance.get_stats = MagicMock(return_value={"hits": 0, "misses": 0, "total_requests": 0, "hit_rate_percent": 0, "current_entries": 0})
        mock_instance.reset_stats = MagicMock()
        yield MockCache

@pytest.fixture
def mock_prompt_builder():
    """Mocka a classe PromptBuilder."""
    with patch('utils.prompt_builder.PromptBuilder') as MockBuilder:
        mock_instance = MockBuilder.return_value
        mock_instance.optimize_prompt = MagicMock(side_effect=lambda agent_type, data, max_tokens: f"Optimized prompt for {agent_type}: {data['question']}")
        yield MockBuilder

@pytest.fixture
def orchestrator(mock_google_api, mock_response_cache, mock_prompt_builder):
    """Fixture para uma instância de FreeTierOrchestrator com mocks."""
    # Garante que GOOGLE_API_KEY esteja definida para a inicialização
    with patch('config.GOOGLE_API_KEY', 'test_api_key'):
        return FreeTierOrchestrator()

@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Testa a inicialização do orquestrador."""
    assert orchestrator.default_model_name == "gemini-pro"
    assert isinstance(orchestrator.cache, ResponseCache)
    assert isinstance(orchestrator.prompt_builder, PromptBuilder)
    assert len(orchestrator.agents) == 4 # concept, code, resource, general

@pytest.mark.asyncio
async def test_generate_response_cache_hit(orchestrator, mock_response_cache):
    """Testa a geração de resposta com cache hit."""
    mock_response_cache.return_value.get_cached_response.return_value = "Cached response for test."
    
    prompt = "Test question"
    classification = {"categories": ["concept"], "confidence_score": 0.9, "language": "pt"}
    
    response = await orchestrator.generate_response(prompt, classification)
    
    assert response == "Cached response for test."
    mock_response_cache.return_value.get_cached_response.assert_called_once_with(prompt)
    mock_response_cache.return_value.cache_response.assert_not_called()
    assert orchestrator.cache_hits_saved == 1
    assert orchestrator.api_calls_made == 0
    assert orchestrator.agent_metrics['ConceptExplainer']['cache_hits'] == 1

@pytest.mark.asyncio
async def test_generate_response_api_call(orchestrator, mock_google_api, mock_response_cache):
    """Testa a geração de resposta com chamada à API (cache miss)."""
    mock_response_cache.return_value.get_cached_response.return_value = None # Garante miss
    mock_google_api.return_value.generate_content_async.return_value.candidates[0].content.parts[0].text = "API generated response."
    
    prompt = "Test question for API"
    classification = {"categories": ["code"], "confidence_score": 0.8, "language": "en"}
    
    response = await orchestrator.generate_response(prompt, classification)
    
    assert response == "API generated response."
    mock_response_cache.return_value.get_cached_response.assert_called_once_with(prompt)
    mock_google_api.return_value.generate_content_async.assert_called_once()
    mock_response_cache.return_value.cache_response.assert_called_once_with(prompt, "API generated response.")
    assert orchestrator.api_calls_made == 1
    assert orchestrator.cache_hits_saved == 0
    assert orchestrator.agent_metrics['CodeHelper']['api_calls'] == 1

@pytest.mark.asyncio
async def test_generate_response_routing(orchestrator, mock_google_api, mock_response_cache):
    """Testa o roteamento para diferentes agentes."""
    mock_response_cache.return_value.get_cached_response.return_value = None
    
    # Teste para agente 'resource'
    prompt_resource = "Recomende um livro sobre IA."
    classification_resource = {"categories": ["resource"], "confidence_score": 0.7, "language": "pt"}
    await orchestrator.generate_response(prompt_resource, classification_resource)
    assert orchestrator.agent_metrics['ResourceRecommender']['api_calls'] == 1
    
    # Teste para agente 'general' (fallback)
    prompt_general = "Olá, tudo bem?"
    classification_general = {"categories": ["general"], "confidence_score": 0.2, "language": "pt"}
    await orchestrator.generate_response(prompt_general, classification_general)
    assert orchestrator.agent_metrics['GeneralResponder']['api_calls'] == 1

@pytest.mark.asyncio
async def test_generate_response_api_failure_fallback_to_cache(orchestrator, mock_google_api, mock_response_cache):
    """Testa fallback para cache quando a API falha."""
    mock_response_cache.return_value.get_cached_response.side_effect = [None, "Fallback from cache."] # Primeiro miss, depois hit
    mock_google_api.return_value.generate_content_async.side_effect = Exception("API error") # Simula falha da API
    
    prompt = "Question for API failure"
    classification = {"categories": ["concept"], "confidence_score": 0.9, "language": "pt"}
    
    response = await orchestrator.generate_response(prompt, classification)
    
    assert response == "Fallback from cache."
    assert mock_google_api.return_value.generate_content_async.call_count > 0 # Deve ter tentado chamar a API
    assert orchestrator.cache_hits_saved == 1 # O hit do fallback
    assert orchestrator.agent_metrics['ConceptExplainer']['cache_hits'] == 1

@pytest.mark.asyncio
async def test_generate_response_api_failure_no_fallback(orchestrator, mock_google_api, mock_response_cache):
    """Testa falha total quando API e cache falham."""
    mock_response_cache.return_value.get_cached_response.return_value = None
    mock_google_api.return_value.generate_content_async.side_effect = Exception("API error")
    
    prompt = "Question for total failure"
    classification = {"categories": ["concept"], "confidence_score": 0.9, "language": "pt"}
    
    response = await orchestrator.generate_response(prompt, classification)
    
    assert "Desculpe, não consegui processar sua solicitação" in response
    assert mock_google_api.return_value.generate_content_async.call_count > 0 # Deve ter tentado chamar a API
    assert orchestrator.cache_hits_saved == 0

@pytest.mark.asyncio
async def test_rate_limiting(orchestrator, mock_google_api, mock_response_cache):
    """Testa se o rate limiting está funcionando."""
    mock_response_cache.return_value.get_cached_response.return_value = None
    
    # Reduz o intervalo para testar mais rápido
    orchestrator.rate_limit_interval = 0.1 # 100ms entre requests
    
    start_time = time.time()
    for i in range(3): # Faz 3 requests
        prompt = f"Rate limit test {i}"
        classification = {"categories": ["general"], "confidence_score": 0.5, "language": "pt"}
        await orchestrator.generate_response(prompt, classification)
    end_time = time.time()
    
    # Espera-se que o tempo total seja pelo menos (número de requests - 1) * rate_limit_interval
    expected_min_time = (3 - 1) * orchestrator.rate_limit_interval
    assert (end_time - start_time) >= expected_min_time
    assert mock_google_api.return_value.generate_content_async.call_count == 3

@pytest.mark.asyncio
async def test_retry_mechanism(orchestrator, mock_google_api, mock_response_cache):
    """Testa o mecanismo de retry com backoff exponencial."""
    mock_response_cache.return_value.get_cached_response.return_value = None
    
    # Simula falha nas 2 primeiras tentativas e sucesso na 3ª
    mock_google_api.return_value.generate_content_async.side_effect = [
        Exception("Transient error 1"),
        Exception("Transient error 2"),
        MagicMock(candidates=[MagicMock(content=MagicMock(parts=[MagicMock(text="Retry success.")]))])
    ]
    
    prompt = "Retry test question"
    classification = {"categories": ["general"], "confidence_score": 0.5, "language": "pt"}
    
    response = await orchestrator.generate_response(prompt, classification)
    
    assert response == "Retry success."
    assert mock_google_api.return_value.generate_content_async.call_count == 3 # 3 tentativas
    assert orchestrator.api_calls_made == 1 # Apenas a última tentativa bem-sucedida conta como chamada de API real

def test_get_usage_stats(orchestrator):
    """Testa a recuperação de estatísticas de uso."""
    orchestrator.api_calls_made = 5
    orchestrator.cache_hits_saved = 3
    orchestrator.agent_metrics['ConceptExplainer']['api_calls'] = 2
    orchestrator.agent_metrics['CodeHelper']['cache_hits'] = 1

    stats = orchestrator.get_usage_stats()
    assert stats['api_calls_total'] == 5
    assert stats['cache_hits_total'] == 3
    assert stats['total_requests_processed'] == 8
    assert stats['agent_metrics']['ConceptExplainer']['api_calls'] == 2
    assert stats['agent_metrics']['CodeHelper']['cache_hits'] == 1

def test_reset_stats(orchestrator):
    """Testa o reset das estatísticas."""
    orchestrator.api_calls_made = 5
    orchestrator.cache_hits_saved = 3
    orchestrator.agent_metrics['ConceptExplainer']['api_calls'] = 2
    orchestrator.cache.hits = 10 # Simula hits no cache manager

    orchestrator.reset_stats()
    stats = orchestrator.get_usage_stats()
    assert stats['api_calls_total'] == 0
    assert stats['cache_hits_total'] == 0
    assert stats['total_requests_processed'] == 0
    assert stats['agent_metrics']['ConceptExplainer']['api_calls'] == 0
    assert orchestrator.cache.hits == 0 # Verifica se o cache manager também foi resetado
