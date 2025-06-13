# Documentação da API Interna: Discord AI Tutor Free

Este documento descreve as principais interfaces e componentes internos do projeto Discord AI Tutor Free, focando nas interações entre os módulos. Não se trata de uma API externa para consumo por terceiros, mas sim de um guia para desenvolvedores que desejam entender e estender o código-fonte.

## Sumário

1.  [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2.  [Módulos Principais](#2-módulos-principais)
    *   [`main.py`](#mainpy)
    *   [`agents/discord_tutor.py`](#agentsdiscord_tutorpy)
    *   [`tools/discord_monitor.py`](#toolsdiscord_monitorpy)
    *   [`tools/simple_classifier.py`](#toolssimple_classifierpy)
    *   [`tools/response_cache.py`](#toolsresponse_cachepy)
    *   [`utils/free_tier_orchestrator.py`](#utilsfree_tier_orchestratorpy)
    *   [`utils/prompt_builder.py`](#utilsprompt_builderpy)
3.  [Fluxo de Dados](#3-fluxo-de-dados)
4.  [Configuração e Variáveis de Ambiente](#4-configuração-e-variáveis-de-ambiente)

---

## 1. Visão Geral da Arquitetura

O bot é construído em torno de uma arquitetura modular, onde cada componente tem uma responsabilidade clara. O `main.py` atua como o orquestrador principal, inicializando e conectando os diferentes módulos.

```mermaid
graph TD
    A[Usuário Discord] --> B(Comando/Mensagem)
    B --> C{Bot Discord (main.py)}
    C --> D[Discord Monitor]
    C --> E[Free Tier Orchestrator]
    E --> F[Prompt Builder]
    E --> G[Response Cache]
    E --> H[Google AI Studio API]
    C --> I[Simple Classifier]

    D --> C
    F --> E
    G --> E
    H --> E
    I --> C
```

## 2. Módulos Principais

### `main.py`

-   **Função**: Ponto de entrada da aplicação. Inicializa o cliente Discord, carrega as variáveis de ambiente, configura o logging e inicia o bot.
-   **Interage com**: `discord_tutor.py`, `config.py`.
-   **Métodos/Funções Chave**:
    -   `run_bot()`: Função principal para iniciar o bot.
    -   `on_ready()`: Evento do Discord disparado quando o bot está pronto.
    -   `on_message()`: Evento do Discord disparado quando uma mensagem é recebida.

### `agents/discord_tutor.py`

-   **Função**: Contém a lógica de negócios principal para o bot tutor de IA. Processa mensagens de entrada, interage com o orquestrador de IA e formata as respostas.
-   **Interage com**: `utils/free_tier_orchestrator.py`, `tools/simple_classifier.py`.
-   **Classes/Métodos Chave**:
    -   `DiscordTutorAgent`: Classe principal do agente.
    -   `process_message(message)`: Processa uma mensagem recebida do Discord.
    -   `generate_response(prompt)`: Gera uma resposta usando o orquestrador de IA.

### `tools/discord_monitor.py`

-   **Função**: Responsável por monitorar e lidar com eventos específicos do Discord, como novas mensagens, reações, etc. Pode ser estendido para incluir funcionalidades de moderação ou automação.
-   **Interage com**: API do Discord (via `discord.Client`).
-   **Classes/Métodos Chave**:
    -   `DiscordMonitor`: Classe para encapsular a lógica de monitoramento.
    -   `on_message_event(message)`: Callback para o evento de nova mensagem.

### `tools/simple_classifier.py`

-   **Função**: Fornece uma funcionalidade básica de classificação de texto. Pode ser usado para categorizar a intenção do usuário ou o tipo de pergunta, permitindo que o bot responda de forma mais inteligente.
-   **Interage com**: N/A (pode ser integrado com `discord_tutor.py`).
-   **Classes/Métodos Chave**:
    -   `SimpleClassifier`: Classe para a lógica de classificação.
    -   `classify(text)`: Retorna uma categoria ou intenção para o texto de entrada.

### `tools/response_cache.py`

-   **Função**: Implementa um sistema de cache local para armazenar respostas da API de IA. Isso reduz a latência e o número de chamadas à API, otimizando o uso da camada gratuita.
-   **Interage com**: `response_cache.json`.
-   **Classes/Métodos Chave**:
    -   `ResponseCache`: Classe para gerenciar o cache.
    -   `get(key)`: Recupera uma resposta do cache.
    -   `set(key, value, ttl)`: Armazena uma resposta no cache com um tempo de vida (TTL).
    -   `invalidate(key)`: Invalida uma entrada específica do cache.
    -   `clear()`: Limpa todo o cache.

### `utils/free_tier_orchestrator.py`

-   **Função**: Orquestra as chamadas para a API do Google AI Studio (ou outras APIs de IA gratuitas/de baixo custo). Gerencia a lógica de fallback, limites de taxa e otimização de custos.
-   **Interage com**: Google AI Studio API, `tools/response_cache.py`, `utils/prompt_builder.py`.
-   **Classes/Métodos Chave**:
    -   `FreeTierOrchestrator`: Classe principal do orquestrador.
    -   `generate_text(prompt)`: Envia um prompt para a API de IA e retorna a resposta, utilizando o cache.
    -   `handle_rate_limit()`: Lógica para lidar com limites de taxa da API.

### `utils/prompt_builder.py`

-   **Função**: Constrói e formata os prompts que serão enviados para a API de IA. Garante que os prompts sigam um formato consistente e incluam o contexto necessário.
-   **Interage com**: N/A (utilizado por `free_tier_orchestrator.py`).
-   **Classes/Métodos Chave**:
    -   `PromptBuilder`: Classe para construir prompts.
    -   `build_tutor_prompt(question, context)`: Constrói um prompt para o tutor de IA.
    -   `build_classification_prompt(text)`: Constrói um prompt para classificação.

## 3. Fluxo de Dados

1.  **Mensagem Recebida**: Um usuário envia uma mensagem para o bot no Discord.
2.  **`main.py`**: O evento `on_message` em `main.py` é acionado.
3.  **`discord_tutor.py`**: A mensagem é passada para o `DiscordTutorAgent` para processamento.
4.  **`simple_classifier.py` (Opcional)**: A mensagem pode ser classificada para determinar a intenção.
5.  **`free_tier_orchestrator.py`**: O `DiscordTutorAgent` solicita uma resposta de IA ao `FreeTierOrchestrator`.
6.  **`response_cache.py`**: O `FreeTierOrchestrator` verifica se a resposta já está no cache.
    *   **Cache Hit**: Se a resposta estiver no cache e for válida, ela é retornada imediatamente.
    *   **Cache Miss**: Se não estiver no cache ou for inválida, o processo continua.
7.  **`prompt_builder.py`**: Um prompt é construído com base na pergunta do usuário e no contexto.
8.  **Google AI Studio API**: O `FreeTierOrchestrator` envia o prompt para a API do Google AI Studio.
9.  **Resposta da API**: A resposta da IA é recebida.
10. **`response_cache.py`**: A resposta é armazenada no cache para uso futuro.
11. **`discord_tutor.py`**: A resposta é formatada e enviada de volta ao canal Discord pelo bot.

## 4. Configuração e Variáveis de Ambiente

As configurações do bot são gerenciadas através do arquivo `config.py` e variáveis de ambiente carregadas de `.env`.

-   `DISCORD_BOT_TOKEN`: Token de autenticação do bot Discord.
-   `GOOGLE_API_KEY`: Chave de API para o Google AI Studio.
-   Outras variáveis de configuração podem ser adicionadas conforme necessário em `config.py` ou `.env`.

Para mais detalhes sobre a configuração, consulte o `README.md`.
