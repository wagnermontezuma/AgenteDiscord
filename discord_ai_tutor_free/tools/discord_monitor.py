import discord
import logging

logger = logging.getLogger(__name__)

class DiscordMonitor:
    def __init__(self, client: discord.Client):
        self.client = client
        self._setup_events()

    def _setup_events(self):
        """Configura os eventos do Discord a serem monitorados."""
        @self.client.event
        async def on_ready():
            logger.info(f'Bot conectado como {self.client.user}')
            print(f'Bot conectado como {self.client.user}')

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return # Ignora mensagens do próprio bot

            logger.info(f"Mensagem recebida de {message.author} no canal #{message.channel}: {message.content}")
            # Aqui você pode adicionar lógica para processar a mensagem,
            # como passar para o AI Tutor ou classificador.
            # Exemplo: await self.process_message(message)

        @self.client.event
        async def on_command_error(ctx, error):
            """Lida com erros de comando."""
            if isinstance(error, discord.ext.commands.CommandNotFound):
                logger.warning(f"Comando não encontrado: {ctx.message.content}")
                await ctx.send("Desculpe, não entendi esse comando.")
            else:
                logger.error(f"Erro de comando: {error}")
                await ctx.send(f"Ocorreu um erro: {error}")

    async def process_message(self, message: discord.Message):
        """
        Método placeholder para processar mensagens.
        Será implementado mais detalhadamente no discord_tutor.py.
        """
        logger.debug(f"Processando mensagem: {message.content}")
        # Exemplo simples de resposta
        # await message.channel.send(f"Recebi sua mensagem, {message.author.mention}!")

# Exemplo de uso (para testes internos, pode ser removido em produção)
if __name__ == "__main__":
    # Este bloco é apenas para demonstração e não pode ser executado diretamente
    # sem um token de bot Discord válido e intents configurados.
    # Para testar, você precisaria de um bot real e um loop de evento.
    print("Este módulo não pode ser executado diretamente. Ele é parte de um bot Discord.")
    print("Ele espera uma instância de discord.Client para configurar eventos.")
