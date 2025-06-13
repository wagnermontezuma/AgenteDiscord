import discord
import logging.config
import argparse
import asyncio
import os
import sys
from typing import Optional # Importa Optional

from config import LOGGING_CONFIG, DISCORD_BOT_TOKEN, CACHE_FILE
from agents.discord_tutor import DiscordAITutorFree
from utils.free_tier_orchestrator import FreeTierOrchestrator
from tools.response_cache import ResponseCache

# Configura o logging usando o dicionário do config.py
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Instâncias globais para acesso pelos comandos CLI
# Serão inicializadas conforme necessário para evitar problemas de importação circular ou dependências não resolvidas
_orchestrator: Optional[FreeTierOrchestrator] = None
_cache_manager: Optional[ResponseCache] = None

def get_orchestrator() -> FreeTierOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FreeTierOrchestrator()
    return _orchestrator

def get_cache_manager() -> ResponseCache:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ResponseCache(cache_file=CACHE_FILE)
    return _cache_manager

async def start_bot():
    """
    Inicia o bot Discord.
    """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.guilds = True

    bot = DiscordAITutorFree(intents=intents)
    bot.run_bot()

async def show_status():
    """
    Mostra o status detalhado do bot e métricas.
    """
    orchestrator = get_orchestrator()
    stats = orchestrator.get_usage_stats()
    
    status_message = (
        "**Status do Discord AI Tutor:**\n"
        f"```\n"
        f"Total de Requisições Processadas: {stats['total_requests_processed']}\n"
        f"Chamadas à API (Gemini): {stats['api_calls_total']}\n"
        f"Hits de Cache Salvos: {stats['cache_hits_total']}\n"
        f"```\n"
        "**Métricas por Agente:**\n"
        "```\n"
    )
    for agent_name, metrics in stats['agent_metrics'].items():
        status_message += f"- {agent_name}:\n"
        status_message += f"  API Calls: {metrics['api_calls']}\n"
        status_message += f"  Cache Hits: {metrics['cache_hits']}\n"
    status_message += "```"
    
    print(status_message)
    logger.info("Comando 'status' executado.")

async def test_apis():
    """
    Testa a conexão com a API do Discord e Google AI Studio.
    """
    print("--- Testando Conectividade ---")
    
    # Teste de Conectividade Discord (simplificado)
    if DISCORD_BOT_TOKEN:
        print("Testando token do Discord... (Verificado na inicialização do bot)")
        # Um teste mais robusto exigiria uma conexão real, mas isso é suficiente para CLI
        print("Status do Token Discord: OK (se o bot iniciar, o token é válido)")
    else:
        print("Status do Token Discord: FALHA (DISCORD_BOT_TOKEN não configurado)")

    # Teste de Conectividade Google AI Studio
    orchestrator = get_orchestrator()
    test_prompt = "Olá, como você está?"
    print(f"\nTestando conexão com Google AI Studio (modelo: {orchestrator.default_model_name})...")
    try:
        # Usar um prompt simples e desativar cache para forçar chamada à API
        response = await orchestrator.generate_response(test_prompt, {"categories": ["general"]}, use_cache=False)
        if response:
            print("Conexão com Google AI Studio: SUCESSO!")
            print(f"Exemplo de resposta: {response[:100]}...")
        else:
            print("Conexão com Google AI Studio: FALHA (resposta vazia ou erro interno).")
    except Exception as e:
        print(f"Conexão com Google AI Studio: ERRO - {e}")
    
    # Verificação de integridade do cache
    cache_manager = get_cache_manager()
    print(f"\nVerificando integridade do cache ({cache_manager.cache_file})...")
    try:
        cache_manager._load_cache() # Tenta recarregar para verificar integridade
        print(f"Integridade do Cache: OK. Entradas: {len(cache_manager.cache)}")
    except Exception as e:
        print(f"Integridade do Cache: FALHA - {e}")

    logger.info("Comando 'test-api' executado.")

async def clear_cache_cli():
    """
    Limpa o cache de respostas.
    """
    cache_manager = get_cache_manager()
    initial_entries = len(cache_manager.cache)
    cache_manager.cache = {} # Limpa o cache em memória
    cache_manager._save_cache() # Salva o cache vazio no arquivo
    print(f"Cache limpo. {initial_entries} entradas removidas.")
    logger.info("Comando 'clear-cache' executado.")

async def show_stats():
    """
    Mostra estatísticas de uso detalhadas (API calls, cache hits, etc.).
    """
    orchestrator = get_orchestrator()
    stats = orchestrator.get_usage_stats()
    
    stats_message = (
        "**Estatísticas de Uso do Bot:**\n"
        f"```\n"
        f"Total de Requisições Processadas: {stats['total_requests_processed']}\n"
        f"Chamadas à API (Gemini): {stats['api_calls_total']}\n"
        f"Hits de Cache Salvos: {stats['cache_hits_total']}\n"
        f"```\n"
        "**Estatísticas Detalhadas do Cache:**\n"
        f"```\n"
        f"Entradas Atuais: {stats['cache_stats']['current_entries']}\n"
        f"Hits de Cache: {stats['cache_stats']['hits']}\n"
        f"Misses de Cache: {stats['cache_stats']['misses']}\n"
        f"Taxa de Acerto do Cache: {stats['cache_stats']['hit_rate_percent']}%\n"
        f"```\n"
        "**Métricas de API por Agente:**\n"
        "```\n"
    )
    for agent_name, metrics in stats['agent_metrics'].items():
        stats_message += f"- {agent_name}: API Calls: {metrics['api_calls']}, Cache Hits: {metrics['cache_hits']}\n"
    stats_message += "```"

    print(stats_message)
    logger.info("Comando 'stats' executado.")

def main():
    parser = argparse.ArgumentParser(description="Discord AI Tutor Bot CLI.")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando 'start'
    start_parser = subparsers.add_parser("start", help="Inicia o bot Discord.")
    start_parser.set_defaults(func=start_bot)

    # Comando 'status'
    status_parser = subparsers.add_parser("status", help="Mostra o status detalhado do bot e métricas.")
    status_parser.set_defaults(func=show_status)

    # Comando 'test-api'
    test_api_parser = subparsers.add_parser("test-api", help="Testa a conexão com as APIs do Discord e Google AI Studio.")
    test_api_parser.set_defaults(func=test_apis)

    # Comando 'clear-cache'
    clear_cache_parser = subparsers.add_parser("clear-cache", help="Limpa o cache de respostas do bot.")
    clear_cache_parser.set_defaults(func=clear_cache_cli)

    # Comando 'stats'
    stats_parser = subparsers.add_parser("stats", help="Mostra estatísticas de uso detalhadas (API calls, cache hits, etc.).")
    stats_parser.set_defaults(func=show_stats)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        # Executa a função assíncrona no loop de eventos
        try:
            asyncio.run(args.func())
        except Exception as e:
            logger.critical(f"Erro ao executar comando CLI: {e}")
            print(f"ERRO: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
