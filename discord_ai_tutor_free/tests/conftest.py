import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import json
from datetime import datetime, timedelta
import sys # Adicionado para manipulação do sys.path
import discord # Adicionado para discord.Intents

# Adiciona o diretório raiz do projeto ao sys.path
# Isso permite que os módulos do projeto sejam importados corretamente nos testes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Mock para a API do Google AI Studio
@pytest.fixture(autouse=True) # Autouse para aplicar em todos os testes
def mock_google_ai_studio_api():
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Resposta simulada do Google AI Studio."
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        yield mock_model

# Mock para GOOGLE_API_KEY em config.py
@pytest.fixture(autouse=True)
def mock_google_api_key():
    with patch('config.GOOGLE_API_KEY', 'TEST_API_KEY'):
        yield

# Mock para o cliente Discord
@pytest.fixture
def mock_discord_client():
    with patch('discord.Client') as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance

# Fixture para dados de teste (exemplo)
@pytest.fixture
def sample_data():
    return {
        "question": "O que é Python?",
        "context": "Python é uma linguagem de programação.",
        "expected_answer": "Python é uma linguagem de programação de alto nível."
    }

# Fixture para simular rate limiting
@pytest.fixture
def mock_rate_limiter():
    with patch('discord_ai_tutor_free.utils.free_tier_orchestrator.RateLimiter') as mock_limiter:
        mock_instance = MagicMock()
        mock_instance.check_limit.return_value = True  # Por padrão, permite a requisição
        mock_limiter.return_value = mock_instance
        yield mock_instance

# Fixture para o cache de respostas
@pytest.fixture
def response_cache_instance():
    # Cria um arquivo de cache temporário para os testes
    cache_file = "test_response_cache.json"
    if os.path.exists(cache_file):
        os.remove(cache_file)
    
    from discord_ai_tutor_free.tools.response_cache import ResponseCache
    cache = ResponseCache(cache_file)
    yield cache
    
    # Limpa o arquivo de cache após os testes
    if os.path.exists(cache_file):
        os.remove(cache_file)

@pytest.fixture
def populated_response_cache_instance():
    cache_file = "test_response_cache_populated.json"
    if os.path.exists(cache_file):
        os.remove(cache_file)
    
    from discord_ai_tutor_free.tools.response_cache import ResponseCache
    cache = ResponseCache(cache_file)
    
    # Adiciona alguns itens ao cache
    cache.add_to_cache("key1", "value1", datetime.now() + timedelta(minutes=5))
    cache.add_to_cache("key2", "value2", datetime.now() - timedelta(minutes=5)) # Expirado
    
    yield cache
    
    if os.path.exists(cache_file):
        os.remove(cache_file)

@pytest.fixture
def mock_discord_message():
    """
    Fixture para simular um objeto discord.Message.
    """
    mock_msg = AsyncMock()
    mock_msg.author.bot = False
    mock_msg.content = "Olá, como você está?"
    mock_msg.channel.send = AsyncMock()
    mock_msg.guild = MagicMock()
    mock_msg.guild.id = 12345
    mock_msg.author.id = 67890
    return mock_msg

@pytest.fixture
def mock_discord_guild():
    """
    Fixture para simular um objeto discord.Guild.
    """
    mock_guild = MagicMock()
    mock_guild.id = 12345
    return mock_guild

@pytest.fixture
def mock_discord_member():
    """
    Fixture para simular um objeto discord.Member.
    """
    mock_member = MagicMock()
    mock_member.id = 67890
    return mock_member

@pytest.fixture
def mock_discord_channel():
    """
    Fixture para simular um objeto discord.TextChannel.
    """
    mock_channel = AsyncMock()
    mock_channel.send = AsyncMock()
    return mock_channel
