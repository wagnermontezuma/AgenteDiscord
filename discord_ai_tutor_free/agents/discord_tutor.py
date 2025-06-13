import discord
from discord.ext import commands
import logging
import re
import time
from typing import List, Dict, Any
import asyncio

from tools.discord_monitor import DiscordMonitor # Pode ser removido ou adaptado se os eventos forem tratados aqui
from tools.simple_classifier import SimpleClassifier
from utils.free_tier_orchestrator import FreeTierOrchestrator
from config import DISCORD_BOT_TOKEN, LOGGING_CONFIG
import logging.config

# Configura o logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class DiscordAITutorFree(commands.Bot):
    def __init__(self, *, intents: discord.Intents, command_prefix: str = '!ia '):
        super().__init__(command_prefix=command_prefix, intents=intents)
        
        # Instâncias das ferramentas e orquestrador
        self.classifier = SimpleClassifier()
        self.orchestrator = FreeTierOrchestrator()
        
        # Anti-spam por usuário
        self.last_response_time: Dict[int, float] = {}
        self.spam_cooldown = 30 # segundos

        # Adiciona comandos
        self._add_commands()

        logger.info("DiscordAITutorFree inicializado.")

    async def on_ready(self):
        """Evento chamado quando o bot está pronto e conectado ao Discord."""
        logger.info(f'Bot conectado como {self.user} (ID: {self.user.id})')
        print(f'Bot conectado como {self.user} (ID: {self.user.id})')
        print('------')
        # O DiscordMonitor pode ser integrado aqui ou removido se seus eventos forem tratados diretamente
        # self.monitor = DiscordMonitor(self) # Se DiscordMonitor ainda for usado para algo além de on_ready/on_message

    async def on_message(self, message: discord.Message):
        """Evento chamado quando uma mensagem é enviada em um canal que o bot pode ver."""
        if message.author == self.user or message.author.bot:
            return # Ignora mensagens do próprio bot ou de outros bots

        logger.info(f"Mensagem de {message.author} ({message.author.id}) no canal #{message.channel} ({message.channel.id}): {message.content}")

        # Processa comandos primeiro
        await self.process_commands(message)

        # Verifica anti-spam
        if message.author.id in self.last_response_time:
            elapsed_time = time.time() - self.last_response_time[message.author.id]
            if elapsed_time < self.spam_cooldown:
                logger.warning(f"Anti-spam ativado para {message.author.name}. Tempo restante: {self.spam_cooldown - elapsed_time:.2f}s")
                # Opcional: enviar uma mensagem de aviso de spam
                # await message.channel.send(f"Por favor, espere um pouco antes de enviar outra pergunta, {message.author.mention}.")
                return
        
        # Verifica se a mensagem é uma menção ao bot ou em um DM
        if self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            clean_message_content = self._clean_mention(message.content)
            logger.info(f"Mensagem limpa para processamento: '{clean_message_content}'")

            # Classifica a mensagem para otimização
            classification_result = self.classifier.classify_question(clean_message_content)
            logger.debug(f"Classificação detectada: {classification_result}")

            # Respostas rápidas para saudações/despedidas (usando a nova estrutura de classificação)
            if "general" in classification_result['categories'] and classification_result['confidence_score'] < 0.5:
                # Se for uma saudação simples ou despedida, e a confiança for baixa para outras categorias
                if any(kw in clean_message_content.lower() for kw in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
                    await message.channel.send(f"Olá, {message.author.mention}! Como posso ajudar hoje?")
                    self.last_response_time[message.author.id] = time.time()
                    return
                if any(kw in clean_message_content.lower() for kw in ["tchau", "até mais", "adeus"]):
                    await message.channel.send(f"Até mais, {message.author.mention}! Se precisar de algo, é só chamar.")
                    self.last_response_time[message.author.id] = time.time()
                    return

            # Verifica se é uma pergunta sobre IA (usando as categorias específicas)
            is_ai_question = any(cat in classification_result['categories'] for cat in ["concept", "code", "resource"])
            
            if is_ai_question or classification_result['confidence_score'] > 0.3: # Responde se for IA ou tiver confiança razoável
                self.last_response_time[message.author.id] = time.time() # Atualiza timestamp do anti-spam

                # Processa a mensagem com o orquestrador de IA
                async with message.channel.typing(): # Mostra que o bot está digitando
                    response = await self.orchestrator.generate_response(clean_message_content, classification_result)
                    if response:
                        await self._send_long_message(message.channel, response)
                    else:
                        await message.channel.send("Desculpe, não consegui gerar uma resposta no momento. Tente novamente mais tarde.")
            else:
                logger.debug(f"Mensagem não classificada como pergunta de IA ou com baixa confiança: '{clean_message_content}'")
                # Opcional: responder com uma mensagem de "não entendi" ou ignorar
                # await message.channel.send(f"Não entendi sua pergunta sobre IA, {message.author.mention}. Poderia reformular?")

        else:
            logger.debug(f"Mensagem não direcionada ao bot: '{message.content}'")

    def _clean_mention(self, text: str) -> str:
        """Remove a menção do bot do início da mensagem."""
        if self.user:
            mention_pattern = re.compile(r'<@!?' + str(self.user.id) + r'>\s*')
            return mention_pattern.sub('', text).strip()
        return text

    async def _send_long_message(self, channel: discord.TextChannel, text: str):
        """Divide e envia mensagens longas em chunks de 2000 caracteres."""
        if len(text) <= 2000:
            await channel.send(text)
            return

        chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
        for chunk in chunks:
            await channel.send(chunk)
            await asyncio.sleep(0.5) # Pequeno delay para evitar rate limit do Discord

    def _add_commands(self):
        """Adiciona os comandos administrativos ao bot."""

        @self.command(name='status', help='Mostra o status e estatísticas do bot.')
        async def status(ctx: commands.Context):
            logger.info(f"Comando !ia status executado por {ctx.author.name}")
            orchestrator_stats = self.orchestrator.get_usage_stats()
            cache_stats = orchestrator_stats['cache_stats']
            agent_metrics = orchestrator_stats['agent_metrics']

            status_message = (
                "**Status do Discord AI Tutor:**\n"
                f"```\n"
                f"Uptime: {self._format_uptime()}\n"
                f"Total de Requisições Processadas: {orchestrator_stats['total_requests_processed']}\n"
                f"Chamadas à API (Gemini): {orchestrator_stats['api_calls_total']}\n"
                f"Hits de Cache Salvos: {orchestrator_stats['cache_hits_total']}\n"
                f"```\n"
                "**Métricas por Agente:**\n"
                "```\n"
            )
            for agent_name, metrics in agent_metrics.items():
                status_message += f"- {agent_name}:\n"
                status_message += f"  API Calls: {metrics['api_calls']}\n"
                status_message += f"  Cache Hits: {metrics['cache_hits']}\n"
            status_message += "```"
            
            await self._send_long_message(ctx.channel, status_message)

        @self.command(name='cache', help='Mostra informações detalhadas do cache.')
        async def cache_info(ctx: commands.Context):
            logger.info(f"Comando !ia cache executado por {ctx.author.name}")
            cache_stats = self.orchestrator.cache.get_stats()
            cache_message = (
                "**Informações do Cache:**\n"
                f"```\n"
                f"Entradas Atuais: {cache_stats['current_entries']}\n"
                f"Hits de Cache: {cache_stats['hits']}\n"
                f"Misses de Cache: {cache_stats['misses']}\n"
                f"Total de Requisições de Cache: {cache_stats['total_requests']}\n"
                f"Taxa de Acerto do Cache: {cache_stats['hit_rate_percent']}%\n"
                f"Arquivo de Cache: {self.orchestrator.cache.cache_file}\n"
                f"Tempo de Expiração (TTL): {self.orchestrator.cache.ttl_seconds / 3600:.1f} horas\n"
                f"```"
            )
            await ctx.send(cache_message)

        @self.command(name='reset', help='Limpa o cache e reseta as estatísticas (apenas para administradores).')
        @commands.has_permissions(administrator=True) # Requer permissão de administrador
        async def reset(ctx: commands.Context):
            logger.warning(f"Comando !ia reset executado por {ctx.author.name} (Admin).")
            self.orchestrator.cache.cleanup_expired() # Garante que o cache está limpo
            self.orchestrator.cache.cache = {} # Limpa o cache em memória
            self.orchestrator.cache._save_cache() # Salva o cache vazio
            self.orchestrator.reset_stats()
            self.last_response_time = {} # Reseta o anti-spam também
            await ctx.send("Cache limpo e estatísticas resetadas com sucesso!")
            logger.info("Cache e estatísticas resetados por comando administrativo.")

        @reset.error
        async def reset_error(ctx, error):
            if isinstance(error, commands.MissingPermissions):
                await ctx.send("Você não tem permissão para usar este comando.")
                logger.warning(f"Tentativa de reset por não-admin: {ctx.author.name}")
            else:
                logger.error(f"Erro no comando reset: {error}")
                await ctx.send(f"Ocorreu um erro ao resetar: {error}")


    def _format_uptime(self) -> str:
        """Formata o tempo de atividade do bot."""
        # Isso é um placeholder. Para um uptime real, você precisaria
        # registrar o tempo de inicialização do bot.
        return "N/A (funcionalidade de uptime real a ser implementada)"

    def run_bot(self):
        """Inicia o bot do Discord."""
        if not DISCORD_BOT_TOKEN:
            logger.critical("DISCORD_BOT_TOKEN não encontrado. Por favor, configure-o no arquivo .env.")
            print("ERRO: DISCORD_BOT_TOKEN não encontrado. Por favor, configure-o no arquivo .env.")
            return

        try:
            logger.info("Iniciando bot do Discord...")
            self.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            logger.critical("Falha no login do Discord. Verifique seu token.")
            print("ERRO: Falha no login do Discord. Verifique seu token.")
        except Exception as e:
            logger.critical(f"Erro inesperado ao iniciar o bot: {e}")
            print(f"ERRO: Erro inesperado ao iniciar o bot: {e}")

# Exemplo de uso (para main.py)
if __name__ == "__main__":
    # Para executar este arquivo diretamente para testes, você precisaria de um token
    # e intents configurados.
    # Exemplo de como seria no main.py:
    # from config import DISCORD_BOT_TOKEN
    # intents = discord.Intents.default()
    # intents.message_content = True # Habilita o intent de conteúdo de mensagem
    # intents.members = True # Necessário para comandos de administração e menções
    # bot = DiscordAITutorFree(intents=intents)
    # bot.run_bot()
    print("Este módulo é a lógica principal do bot. Para executá-lo, use main.py.")
