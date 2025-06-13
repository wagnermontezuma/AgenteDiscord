import pytest
import discord # Adicionado para discord.Intents
from unittest.mock import MagicMock, AsyncMock, patch # Adicionado MagicMock e AsyncMock
from discord_ai_tutor_free.agents.discord_tutor import DiscordAITutorFree
from discord_ai_tutor_free.utils.prompt_builder import PromptBuilder
import google.generativeai as genai

@pytest.fixture
def discord_tutor_agent():
    """
    Fixture para uma instância do DiscordAITutorFree (usado para simular o agente).
    """
    # Mockar intents para a inicialização do bot, mesmo que não seja um bot completo aqui
    mock_intents = MagicMock(spec=discord.Intents)
    mock_intents.message_content = True
    mock_intents.members = True
    mock_intents.guilds = True
    
    # Retorna uma instância do bot, que contém o método get_ai_response
    return DiscordAITutorFree(intents=mock_intents)

@pytest.mark.asyncio
async def test_google_ai_studio_api_integration(discord_tutor_agent, mock_google_ai_studio_api):
    """
    Testa a integração com a API do Google AI Studio.
    Verifica se a API é chamada corretamente e se a resposta é processada.
    """
    question = "Qual é a capital do Brasil?"
    context = "O Brasil é um país da América do Sul."
    history = []

    # O mock_google_ai_studio_api já está configurado para retornar uma resposta simulada.
    # A chamada para generate_content deve ser feita dentro do método do agente.
    
    # O método get_ai_response está no DiscordTutorAgent, que é o agente real.
    # No DiscordAITutorFree, a lógica de resposta passa pelo orchestrator.
    # Para este teste de integração de API, vamos simular a chamada ao método
    # que realmente interage com a API, que seria dentro de um agente específico
    # ou diretamente no orchestrator.
    # Como o DiscordAITutorFree encapsula a lógica, vamos mockar o orchestrator
    # para que ele chame a API.
    
    # Para testar a integração da API, precisamos de um agente que faça a chamada real.
    # O DiscordTutorAgent é o agente que faz a chamada ao Google AI Studio.
    # Vamos instanciar o DiscordTutorAgent diretamente para este teste.
    from discord_ai_tutor_free.agents.discord_tutor import DiscordTutorAgent as RealDiscordTutorAgent
    real_tutor_agent = RealDiscordTutorAgent()
    
    response = await real_tutor_agent.get_ai_response(question, context, history)
    
    # Verifica se a API foi chamada
    mock_google_ai_studio_api.assert_called_once()
    mock_google_ai_studio_api.return_value.generate_content.assert_called_once()
    
    # Verifica se a resposta é a esperada do mock
    assert response == "Resposta simulada do Google AI Studio."

@pytest.mark.asyncio
async def test_google_ai_studio_api_error_handling(discord_tutor_agent, mock_google_ai_studio_api):
    """
    Testa o tratamento de erros na integração com a API do Google AI Studio.
    """
    question = "Teste de erro."
    context = ""
    history = []

    # Configura o mock para levantar uma exceção
    mock_google_ai_studio_api.return_value.generate_content.side_effect = Exception("Erro de API simulado")
    
    # Para testar a integração da API, precisamos de um agente que faça a chamada real.
    # O DiscordTutorAgent é o agente que faz a chamada ao Google AI Studio.
    # Vamos instanciar o DiscordTutorAgent diretamente para este teste.
    from discord_ai_tutor_free.agents.discord_tutor import DiscordTutorAgent as RealDiscordTutorAgent
    real_tutor_agent = RealDiscordTutorAgent()
    
    response = await real_tutor_agent.get_ai_response(question, context, history)
    
    # Verifica se a API foi chamada
    mock_google_ai_studio_api.assert_called_once()
    mock_google_ai_studio_api.return_value.generate_content.assert_called_once()
    
    # Verifica se a resposta de erro é retornada
    assert "Desculpe, não consegui processar sua solicitação" in response
    assert "Erro de API simulado" in response
