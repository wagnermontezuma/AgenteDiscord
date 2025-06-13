import pytest
import os
import json
import time
import logging # Adicionado para o teste de erro de JSON
from tools.response_cache import ResponseCache

@pytest.fixture
def temp_cache_file(tmp_path):
    """Fixture para criar um arquivo de cache temporário."""
    file = tmp_path / "test_cache.json"
    yield str(file)
    if os.path.exists(str(file)):
        os.remove(str(file))
    if os.path.exists(str(file) + ".bak"):
        os.remove(str(file) + ".bak")

@pytest.fixture
def cache_manager(temp_cache_file):
    """Fixture para uma instância de ResponseCache."""
    return ResponseCache(cache_file=temp_cache_file, ttl_hours=0.01) # TTL curto para testes

def test_cache_initialization(temp_cache_file):
    """Testa a inicialização do cache."""
    cache = ResponseCache(cache_file=temp_cache_file)
    assert cache.cache == {}
    assert cache.hits == 0
    assert cache.misses == 0

def test_cache_response_and_get_hit(cache_manager):
    """Testa o armazenamento e recuperação de uma resposta."""
    question = "Qual a capital do Brasil?"
    response = "Brasília"
    cache_manager.cache_response(question, response)
    
    cached_response = cache_manager.get_cached_response(question)
    assert cached_response == response
    assert cache_manager.hits == 1
    assert cache_manager.misses == 0

def test_cache_get_miss(cache_manager):
    """Testa um cache miss."""
    question = "Qual a capital da Argentina?"
    cached_response = cache_manager.get_cached_response(question)
    assert cached_response is None
    assert cache_manager.hits == 0
    assert cache_manager.misses == 1

def test_cache_normalization(cache_manager):
    """Testa a normalização de perguntas."""
    question1 = "Qual a capital da França?"
    response1 = "Paris"
    cache_manager.cache_response(question1, response1)

    question2 = "  qual a CAPITAL da frança? "
    cached_response = cache_manager.get_cached_response(question2)
    assert cached_response == response1
    assert cache_manager.hits == 1

def test_cache_expiration(temp_cache_file):
    """Testa a expiração do cache."""
    cache_manager = ResponseCache(cache_file=temp_cache_file, ttl_hours=0.0001) # TTL de ~0.36 segundos
    question = "Teste de expiração"
    response = "Resposta expirável"
    cache_manager.cache_response(question, response)
    
    time.sleep(0.5) # Espera mais que o TTL
    
    cached_response = cache_manager.get_cached_response(question)
    assert cached_response is None
    assert cache_manager.misses == 1 # Contado como miss porque expirou

def test_cache_cleanup_expired(temp_cache_file):
    """Testa a limpeza manual de entradas expiradas."""
    cache_manager = ResponseCache(cache_file=temp_cache_file, ttl_hours=0.0001)
    question1 = "Q1"
    response1 = "R1"
    question2 = "Q2"
    response2 = "R2"

    cache_manager.cache_response(question1, response1)
    cache_manager.cache_response(question2, response2)
    assert len(cache_manager.cache) == 2

    time.sleep(0.5) # Espera expirar

    cache_manager.cleanup_expired()
    assert len(cache_manager.cache) == 0

def test_cache_persistence(temp_cache_file):
    """Testa se o cache persiste após reinicialização."""
    cache_manager1 = ResponseCache(cache_file=temp_cache_file, ttl_hours=1)
    question = "Teste de persistência"
    response = "Resposta persistente"
    cache_manager1.cache_response(question, response)
    
    # Simula reinicialização
    cache_manager2 = ResponseCache(cache_file=temp_cache_file, ttl_hours=1)
    cached_response = cache_manager2.get_cached_response(question)
    assert cached_response == response
    assert cache_manager2.hits == 1

def test_cache_compression(cache_manager):
    """Testa a compressão e descompressão de respostas longas."""
    long_question = "Esta é uma pergunta muito longa para testar a compressão." * 10
    long_response = "Esta é uma resposta muito, muito, muito longa que deve ser comprimida para economizar espaço no cache. " * 200
    
    cache_manager.cache_response(long_question, long_response)
    
    # Verifica se a resposta foi marcada como comprimida e armazenada como hex
    normalized_q = cache_manager._normalize_question(long_question)
    q_hash = cache_manager._generate_hash(normalized_q)
    entry = cache_manager.cache[q_hash]
    assert entry['compressed'] is True
    assert isinstance(entry['response'], str) # Deve ser uma string hex
    
    retrieved_response = cache_manager.get_cached_response(long_question)
    assert retrieved_response == long_response
    assert cache_manager.hits == 1

def test_cache_backup(temp_cache_file):
    """Testa se um arquivo .bak é criado."""
    cache_manager = ResponseCache(cache_file=temp_cache_file)
    question = "Backup test"
    response = "Backup response"
    cache_manager.cache_response(question, response)
    
    assert os.path.exists(temp_cache_file)
    assert os.path.exists(temp_cache_file + ".bak")

def test_cache_json_decode_error(temp_cache_file, caplog):
    """Testa o tratamento de erro de JSON malformado."""
    with open(temp_cache_file, 'w') as f:
        f.write("invalid json {")
    
    with caplog.at_level(logging.ERROR):
        cache = ResponseCache(cache_file=temp_cache_file)
        assert cache.cache == {}
        assert "Erro ao decodificar JSON do cache" in caplog.text

def test_cache_stats_reset(cache_manager):
    """Testa o reset das estatísticas."""
    cache_manager.cache_response("q1", "r1")
    cache_manager.get_cached_response("q1") # Hit
    cache_manager.get_cached_response("q2") # Miss

    stats = cache_manager.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['total_requests'] == 2

    cache_manager.reset_stats()
    stats_after_reset = cache_manager.get_stats()
    assert stats_after_reset['hits'] == 0
    assert stats_after_reset['misses'] == 0
    assert stats_after_reset['total_requests'] == 0
