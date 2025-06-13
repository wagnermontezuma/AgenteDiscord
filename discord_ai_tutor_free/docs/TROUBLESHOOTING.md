# Guia de Troubleshooting: Discord AI Tutor Free

Este documento fornece soluções para problemas comuns que você pode encontrar ao configurar ou executar o Discord AI Tutor Free.

## Sumário

1.  [Problemas de API Key](#1-problemas-de-api-key)
2.  [Erros de Permissão do Discord](#2-erros-de-permissão-do-discord)
3.  [Rate Limiting Atingido](#3-rate-limiting-atingido)
4.  [Cache Corrompido](#4-cache-corrompido)
5.  [Problemas de Conectividade](#5-problemas-de-conectividade)
6.  [Outros Problemas](#6-outros-problemas)

---

## 1. Problemas de API Key

### Sintoma

O bot não responde, ou você vê erros relacionados à autenticação da API do Google AI Studio ou do Discord no log.

### Possíveis Causas e Soluções

-   **API Key Incorreta/Inválida**:
    -   Verifique se a `GOOGLE_API_KEY` no seu arquivo `.env` está correta e não contém erros de digitação.
    -   Certifique-se de que a chave de API do Google AI Studio ainda é válida e não foi revogada.
-   **Token do Bot Discord Incorreto/Inválido**:
    -   Verifique se o `DISCORD_BOT_TOKEN` no seu arquivo `.env` está correto.
    -   Certifique-se de que o token do bot não expirou ou foi redefinido no [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications).
-   **Variáveis de Ambiente Não Carregadas**:
    -   Confirme se o arquivo `.env` está na raiz do projeto (mesma pasta que `main.py`).
    -   Verifique se você ativou corretamente o ambiente virtual antes de executar o bot.
    -   Se estiver usando Docker, certifique-se de que o `--env-file ./.env` está sendo usado no comando `docker run`.

## 2. Erros de Permissão do Discord

### Sintoma

O bot está online, mas não consegue ler mensagens, enviar respostas ou realizar ações específicas no Discord.

### Possíveis Causas e Soluções

-   **Permissões Insuficientes no Portal do Desenvolvedor**:
    -   Vá para o [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications), selecione seu aplicativo de bot.
    -   Em "Bot", certifique-se de que os "Privileged Gateway Intents" (especialmente "MESSAGE CONTENT INTENT") estão ativados.
    -   Em "OAuth2" -> "URL Generator", verifique se as permissões de bot corretas (ex: `Send Messages`, `Read Message History`) foram selecionadas ao adicionar o bot ao servidor. Se não, gere uma nova URL de convite e adicione o bot novamente.
-   **Permissões de Canal/Servidor**:
    -   Verifique as permissões do bot nos canais específicos do seu servidor Discord. O bot pode ter permissões sobrescritas que o impedem de funcionar corretamente em certos canais.
    -   Certifique-se de que o papel do bot no servidor tem as permissões necessárias.

## 3. Rate Limiting Atingido

### Sintoma

O bot para de responder temporariamente ou as respostas demoram muito para chegar, e você pode ver mensagens de erro relacionadas a "rate limit" nos logs.

### Possíveis Causas e Soluções

-   **Excesso de Chamadas à API**:
    -   A API do Google AI Studio (e outras APIs) tem limites de taxa. O bot tenta mitigar isso com o sistema de cache.
    -   **Solução**: Reduza a frequência de interações com o bot. O sistema de cache deve ajudar a gerenciar isso automaticamente. Se o problema persistir, pode ser necessário otimizar a lógica de chamada da API ou considerar um plano de API pago se o volume de uso for muito alto.
-   **Cache Ineficaz**:
    -   Verifique se o cache está funcionando corretamente. O arquivo `response_cache.json` deve estar sendo atualizado.
    -   Aumente o tempo de vida (TTL) do cache se as respostas puderem ser reutilizadas por mais tempo.

## 4. Cache Corrompido

### Sintoma

O bot se comporta de forma inesperada, retorna respostas antigas ou incorretas, ou falha ao tentar ler/escrever no cache.

### Possíveis Causas e Soluções

-   **Arquivo `response_cache.json` Danificado**:
    -   O arquivo de cache pode ter sido corrompido devido a um desligamento inesperado ou erro de escrita.
    -   **Solução**: Exclua o arquivo `discord_ai_tutor_free/response_cache.json`. O bot irá recriá-lo automaticamente na próxima execução. Isso limpará o cache, mas resolverá a corrupção.
-   **Problemas de Permissão de Escrita**:
    -   Certifique-se de que o bot tem permissão para ler e escrever no diretório onde `response_cache.json` está localizado.

## 5. Problemas de Conectividade

### Sintoma

O bot não consegue se conectar ao Discord ou à API do Google AI Studio. Mensagens como "Connection refused", "Timeout" ou "DNS resolution failed" podem aparecer nos logs.

### Possíveis Causas e Soluções

-   **Problemas de Rede**:
    -   Verifique sua conexão com a internet.
    -   Certifique-se de que não há firewalls ou proxies bloqueando as conexões de saída do bot para o Discord (porta 443) ou para os servidores da Google AI Studio.
-   **Serviços Indisponíveis**:
    -   Verifique o status dos serviços do Discord e do Google AI Studio. Pode haver uma interrupção temporária.
-   **Configuração de Proxy (se aplicável)**:
    -   Se você estiver usando um proxy, certifique-se de que as variáveis de ambiente `HTTP_PROXY` e `HTTPS_PROXY` estão configuradas corretamente.

## 6. Outros Problemas

### O bot não inicia

-   **Verifique os logs**: O arquivo `discord_ai_tutor.log` (na raiz do projeto) é a primeira fonte de informação. Ele geralmente contém mensagens de erro detalhadas que podem indicar a causa do problema.
-   **Dependências Faltando**: Certifique-se de que todas as dependências em `requirements.txt` foram instaladas corretamente (`pip install -r requirements.txt`).
-   **Erro de Sintaxe no Código**: Se você fez alterações no código, verifique se não há erros de sintaxe.

### O bot não responde a comandos específicos

-   **Prefixo do Comando**: Verifique se você está usando o prefixo de comando correto (se aplicável) ou se está mencionando o bot corretamente.
-   **Lógica do Comando**: Revise a lógica no `discord_tutor.py` ou `main.py` para o comando específico.

Se você não conseguir resolver o problema, por favor, abra uma [Issue no GitHub](https://github.com/seu-usuario/discord-ai-tutor-free/issues) com o máximo de detalhes possível, incluindo logs e passos para reproduzir o problema.
