import pytest
import time # Adicionado para testes de performance
import discord # Adicionado para discord.Intents
from unittest.mock import MagicMock, AsyncMock, patch # Adicionado MagicMock e AsyncMock
from discord_ai_tutor_free.agents.discord_tutor import DiscordAITutorFree
from discord_ai_tutor_free.utils.free_tier_orchestrator import FreeTierOrchestrator
from discord_ai_tutor_free.tools.response_cache import ResponseCache
from discord_ai_tutor_free.tools.simple_classifier import SimpleClassifier
# from discord_ai_tutor_free.agents.discord_tutor import DiscordTutorAgent # Removido
from discord_ai_tutor_free.utils.prompt_builder import PromptBuilder

@pytest.fixture
def mock_bot_instance():
    """
    Fixture para simular uma instância do DiscordAITutorFree com mocks.
    """
    # Mockar intents para a inicialização do bot
    mock_intents = MagicMock(spec=discord.Intents)
    mock_intents.message_content = True
    mock_intents.members = True
    mock_intents.guilds = True

    bot = DiscordAITutorFree(intents=mock_intents)
    bot.orchestrator = AsyncMock(spec=FreeTierOrchestrator)
    bot.cache = AsyncMock(spec=ResponseCache)
    bot.classifier = AsyncMock(spec=SimpleClassifier)
    # O DiscordAITutorFree não tem um atributo tutor_agent diretamente,
    # ele usa o orchestrator para interagir com os agentes.
    # A linha bot.tutor_agent = AsyncMock(spec=DiscordTutorAgent) foi removida.
    bot.prompt_builder = AsyncMock(spec=PromptBuilder)
    return bot

@pytest.mark.asyncio
async def test_full_question_flow(mock_bot_instance, mock_discord_message, mock_google_ai_studio_api):
    """
    Simula o fluxo completo de uma pergunta do Discord até a resposta.
    Testa: detecção de pergunta -> classificação -> cache check -> orquestrador -> agente -> resposta.
    """
    question = "O que é machine learning?"
    mock_discord_message.content = question
    
    # Configurar mocks para o fluxo
    mock_bot_instance.classifier.classify_message.return_value = ("pergunta", 0.9)
    mock_bot_instance.cache.get_from_cache.return_value = None # Simula cache miss
    mock_bot_instance.orchestrator.process_request.return_value = "Resposta simulada do orquestrador."
    
    # Executar o método on_message do bot
    await mock_bot_instance.on_message(mock_discord_message)
    
    # Verificar as chamadas dos mocks
    mock_bot_instance.classifier.classify_message.assert_called_once_with(question)
    mock_bot_instance.cache.get_from_cache.assert_called_once_with(question)
    mock_bot_instance.orchestrator.process_request.assert_called_once_with(
        question, mock_discord_message.author.id, mock_discord_message.guild.id
    )
    mock_discord_message.channel.send.assert_called_once_with("Resposta simulada do orquestrador.")
    
    response = mock_discord_message.channel.send.call_args[0][0]
    assert response is not None
    assert len(response) < 2000 # Limite Discord

@pytest.mark.asyncio
async def test_full_question_flow_performance(mock_bot_instance, mock_discord_message, mock_google_ai_studio_api):
    """
    Testa o tempo de resposta do fluxo completo.
    """
    question = "Qual o impacto da IA na sociedade?"
    mock_discord_message.content = question
    
    mock_bot_instance.classifier.classify_message.return_value = ("pergunta", 0.9)
    mock_bot_instance.cache.get_from_cache.return_value = None
    mock_bot_instance.orchestrator.process_request.return_value = "Resposta de performance simulada."
    
    start_time = time.perf_counter()
    await mock_bot_instance.on_message(mock_discord_message)
    end_time = time.perf_counter()
    
    response_time = end_time - start_time
    print(f"Tempo de resposta do fluxo completo: {response_time:.4f} segundos")
    assert response_time < 5.0 # Tempo de resposta esperado menor que 5 segundos

@pytest.mark.asyncio
async def test_full_question_flow_with_cache_hit(mock_bot_instance, mock_discord_message):
    """
    Simula o fluxo completo com um cache hit.
    """
    question = "O que é machine learning?"
    mock_discord_message.content = question
    
    # Configurar mocks para o fluxo com cache hit
    mock_bot_instance.classifier.classify_message.return_value = ("pergunta", 0.9)
    mock_bot_instance.cache.get_from_cache.return_value = "Resposta do cache." # Simula cache hit
    
    # Executar o método on_message do bot
    await mock_bot_instance.on_message(mock_discord_message)
    
    # Verificar as chamadas dos mocks
    mock_bot_instance.classifier.classify_message.assert_called_once_with(question)
    mock_bot_instance.cache.get_from_cache.assert_called_once_with(question)
    mock_bot_instance.orchestrator.process_request.assert_not_called() # Não deve chamar o orquestrador
    mock_discord_message.channel.send.assert_called_once_with("Resposta do cache.")

@pytest.mark.asyncio
async def test_full_question_flow_non_question(mock_bot_instance, mock_discord_message):
    """
    Simula o fluxo para uma mensagem que não é uma pergunta.
    """
    mock_discord_message.content = "Olá a todos!"
    
    # Configurar mocks para o fluxo
    mock_bot_instance.classifier.classify_message.return_value = ("saudacao", 0.9)
    
    # Executar o método on_message do bot
    await mock_bot_instance.on_message(mock_discord_message)
    
    # Verificar as chamadas dos mocks
    mock_bot_instance.classifier.classify_message.assert_called_once_with("Olá a todos!")
    mock_bot_instance.cache.get_from_cache.assert_not_called()
    mock_bot_instance.orchestrator.process_request.assert_not_called()
    mock_discord_message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_full_question_flow_bot_message(mock_bot_instance, mock_discord_message):
    """
    Simula o fluxo para uma mensagem enviada pelo próprio bot.
    """
    mock_discord_message.author.bot = True
    mock_discord_message.content = "Eu sou um bot."
    
    # Executar o método on_message do bot
    await mock_bot_instance.on_message(mock_discord_message)
    
    # Verificar que nenhuma função principal foi chamada
    mock_bot_instance.classifier.classify_message.assert_not_called()
    mock_bot_instance.cache.get_from_cache.assert_not_called()
    mock_bot_instance.orchestrator.process_request.assert_not_called()
    mock_discord_message.channel.send.assert_not_called()
