import pytest
import asyncio
import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock, patch
import time
import logging # Adicionado para o teste de logging

from agents.discord_tutor import DiscordAITutorFree
from config import DISCORD_BOT_TOKEN

# Mock do token do Discord para evitar falha na inicialização
@pytest.fixture(autouse=True)
def mock_discord_token():
    with patch('config.DISCORD_BOT_TOKEN', 'MOCK_TOKEN'):
        yield

@pytest.fixture
def mock_intents():
    """Fixture para intents mockados."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True
    return intents

@pytest.fixture
def mock_classifier():
    """Mock da classe SimpleClassifier."""
    with patch('agents.discord_tutor.SimpleClassifier') as MockClassifier:
        mock_instance = MockClassifier.return_value
        mock_instance.classify_question = MagicMock(return_value={"categories": ["general"], "confidence_score": 0.1, "language": "pt"})
        yield MockClassifier

@pytest.fixture
def mock_orchestrator():
    """Mock da classe FreeTierOrchestrator."""
    with patch('agents.discord_tutor.FreeTierOrchestrator') as MockOrchestrator:
        mock_instance = MockOrchestrator.return_value
        mock_instance.generate_response = AsyncMock(return_value="Mocked AI response from orchestrator.")
        mock_instance.get_usage_stats = MagicMock(return_value={
            "api_calls_total": 10, "cache_hits_total": 5, "total_requests_processed": 15,
            "cache_stats": {"hits": 5, "misses": 10, "total_requests": 15, "hit_rate_percent": 33.33, "current_entries": 10},
            "agent_metrics": {"ConceptExplainer": {"api_calls": 2, "cache_hits": 1}}
        })
        mock_instance.reset_stats = MagicMock()
        yield MockOrchestrator

@pytest.fixture
def bot(mock_intents, mock_classifier, mock_orchestrator):
    """Fixture para uma instância do bot."""
    b = DiscordAITutorFree(intents=mock_intents)
    # Mocka o bot.user para evitar AttributeError em on_message
    b.user = MagicMock(spec=discord.ClientUser)
    b.user.id = 1234567890 # ID de exemplo para o bot
    b.user.bot = True # O bot é um bot
    b.user.mentioned_in = MagicMock(return_value=True) # Simula menção
    
    # Desabilita o comando help padrão para evitar conflitos com o nosso (se tivéssemos um)
    # b.remove_command('help') 
    return b

@pytest.mark.asyncio
async def test_bot_initialization(bot):
    """Testa a inicialização do bot."""
    assert isinstance(bot, DiscordAITutorFree)
    assert isinstance(bot.classifier, MagicMock) # Deve ser o mock
    assert isinstance(bot.orchestrator, MagicMock) # Deve ser o mock
    assert bot.command_prefix == '!ia '

@pytest.mark.asyncio
async def test_on_ready(bot, caplog):
    """Testa o evento on_ready."""
    with caplog.at_level(logging.INFO):
        await bot.on_ready()
        assert f'Bot conectado como {bot.user} (ID: {bot.user.id})' in caplog.text

@pytest.mark.asyncio
async def test_on_message_ignore_self_and_bots(bot):
    """Testa se o bot ignora mensagens próprias e de outros bots."""
    mock_message = MagicMock(spec=discord.Message)
    mock_message.author = bot.user # Mensagem do próprio bot
    mock_message.author.bot = False # Não é um bot externo, mas é o próprio bot
    await bot.on_message(mock_message)
    mock_message.author.bot = True # Mensagem de outro bot
    mock_message.author = MagicMock(spec=discord.User, bot=True)
    await bot.on_message(mock_message)
    
    bot.process_commands.assert_not_called() # Não deve processar comandos
    bot.orchestrator.generate_response.assert_not_called() # Não deve gerar resposta

@pytest.mark.asyncio
async def test_on_message_anti_spam(bot, mock_classifier, mock_orchestrator):
    """Testa o sistema anti-spam."""
    mock_message = MagicMock(spec=discord.Message)
    mock_message.author = MagicMock(spec=discord.User, id=123, bot=False)
    mock_message.channel = AsyncMock(spec=discord.TextChannel)
    mock_message.content = "Olá bot"
    mock_message.guild = MagicMock()
    mock_message.guild.me = bot.user
    mock_message.mentions = [bot.user] # Simula menção
    mock_message.channel.typing.return_value.__aenter__ = AsyncMock()
    mock_message.channel.typing.return_value.__aexit__ = AsyncMock()

    # Primeira mensagem (deve passar)
    await bot.on_message(mock_message)
    mock_orchestrator.return_value.generate_response.assert_called_once()
    mock_orchestrator.return_value.generate_response.reset_mock()

    # Segunda mensagem dentro do cooldown (deve ser ignorada)
    mock_message.content = "Outra pergunta"
    await bot.on_message(mock_message)
    mock_orchestrator.return_value.generate_response.assert_not_called()

    # Espera o cooldown e tenta novamente (deve passar)
    await asyncio.sleep(bot.spam_cooldown + 0.1)
    await bot.on_message(mock_message)
    mock_orchestrator.return_value.generate_response.assert_called_once()

@pytest.mark.asyncio
async def test_on_message_ai_question_response(bot, mock_classifier, mock_orchestrator):
    """Testa a resposta a uma pergunta de IA."""
    mock_message = MagicMock(spec=discord.Message)
    mock_message.author = MagicMock(spec=discord.User, id=456, bot=False)
    mock_message.channel = AsyncMock(spec=discord.TextChannel)
    mock_message.content = "O que é machine learning?"
    mock_message.guild = MagicMock()
    mock_message.guild.me = bot.user
    mock_message.mentions = [bot.user]
    mock_message.channel.typing.return_value.__aenter__ = AsyncMock()
    mock_message.channel.typing.return_value.__aexit__ = AsyncMock()

    mock_classifier.return_value.classify_question.return_value = {"categories": ["concept"], "confidence_score": 0.8, "language": "pt"}
    mock_orchestrator.return_value.generate_response.return_value = "Resposta da IA sobre ML."

    await bot.on_message(mock_message)
    mock_classifier.return_value.classify_question.assert_called_once_with("O que é machine learning?")
    mock_orchestrator.return_value.generate_response.assert_called_once()
    mock_message.channel.send.assert_called_once_with("Resposta da IA sobre ML.")

@pytest.mark.asyncio
async def test_on_message_long_response_split(bot, mock_classifier, mock_orchestrator):
    """Testa a divisão de respostas longas."""
    mock_message = MagicMock(spec=discord.Message)
    mock_message.author = MagicMock(spec=discord.User, id=789, bot=False)
    mock_message.channel = AsyncMock(spec=discord.TextChannel)
    mock_message.content = "Pergunta muito longa para testar a divisão de resposta."
    mock_message.guild = MagicMock()
    mock_message.guild.me = bot.user
    mock_message.mentions = [bot.user]
    mock_message.channel.typing.return_value.__aenter__ = AsyncMock()
    mock_message.channel.typing.return_value.__aexit__ = AsyncMock()

    long_response = "A" * 2500 # Resposta maior que 2000 caracteres
    mock_orchestrator.return_value.generate_response.return_value = long_response

    await bot.on_message(mock_message)
    assert mock_message.channel.send.call_count == 2 # Deve ter sido chamada duas vezes
    mock_message.channel.send.assert_any_call(long_response[:2000])
    mock_message.channel.send.assert_any_call(long_response[2000:])

@pytest.mark.asyncio
async def test_command_status(bot, mock_orchestrator):
    """Testa o comando !ia status."""
    ctx = AsyncMock(spec=commands.Context)
    ctx.author = MagicMock(spec=discord.User, name="TestUser")
    ctx.channel = AsyncMock(spec=discord.TextChannel)
    
    # Usa ctx.invoke para simular a chamada de comando corretamente
    await ctx.invoke(bot.get_command('status'))
    
    mock_orchestrator.return_value.get_usage_stats.assert_called_once()
    ctx.channel.send.assert_called_once()
    sent_message = ctx.channel.send.call_args[0][0]
    assert "Status do Discord AI Tutor" in sent_message
    assert "Total de Requisições Processadas: 15" in sent_message

@pytest.mark.asyncio
async def test_command_cache_info(bot, mock_orchestrator):
    """Testa o comando !ia cache."""
    ctx = AsyncMock(spec=commands.Context)
    ctx.author = MagicMock(spec=discord.User, name="TestUser")
    ctx.channel = AsyncMock(spec=discord.TextChannel)
    
    # Usa ctx.invoke para simular a chamada de comando corretamente
    await ctx.invoke(bot.get_command('cache'))
    
    mock_orchestrator.return_value.cache.get_stats.assert_called_once()
    ctx.channel.send.assert_called_once()
    sent_message = ctx.channel.send.call_args[0][0]
    assert "Informações do Cache" in sent_message
    assert "Hits de Cache: 5" in sent_message

@pytest.mark.asyncio
async def test_command_reset_admin(bot, mock_orchestrator):
    """Testa o comando !ia reset por um administrador."""
    ctx = AsyncMock(spec=commands.Context)
    ctx.author = MagicMock(spec=discord.User, name="AdminUser")
    ctx.channel = AsyncMock(spec=discord.TextChannel)
    ctx.author.guild_permissions = MagicMock(administrator=True) # Simula admin
    
    # Usa ctx.invoke para simular a chamada de comando corretamente
    await ctx.invoke(bot.get_command('reset'))
    
    mock_orchestrator.return_value.cache.cleanup_expired.assert_called_once()
    mock_orchestrator.return_value.cache._save_cache.assert_called_once()
    mock_orchestrator.return_value.reset_stats.assert_called_once()
    assert bot.last_response_time == {}
    ctx.channel.send.assert_called_once_with("Cache limpo e estatísticas resetadas com sucesso!")

@pytest.mark.asyncio
async def test_command_reset_non_admin(bot, mock_orchestrator):
    """Testa o comando !ia reset por um não-administrador."""
    ctx = AsyncMock(spec=commands.Context)
    ctx.author = MagicMock(spec=discord.User, name="NormalUser")
    ctx.channel = AsyncMock(spec=discord.TextChannel)
    ctx.author.guild_permissions = MagicMock(administrator=False) # Simula não-admin
    
    # O comando de reset tem um decorador commands.has_permissions(administrator=True)
    # que levanta commands.MissingPermissions. Precisamos chamar o error handler.
    command = bot.get_command('reset')
    with pytest.raises(commands.MissingPermissions): # Espera a exceção
        await ctx.invoke(command) # Usa ctx.invoke para simular a chamada de comando
    
    # Verifica se o error handler foi chamado e enviou a mensagem correta
    # Como o error handler é um método do bot, ele não é um mock direto.
    # Podemos verificar a chamada a ctx.send.
    ctx.channel.send.assert_called_once_with("Você não tem permissão para usar este comando.")
    mock_orchestrator.return_value.reset_stats.assert_not_called() # Não deve resetar
