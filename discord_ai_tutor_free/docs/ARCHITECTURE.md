# Arquitetura do Sistema: Discord AI Tutor Free

Este documento detalha a arquitetura do sistema Discord AI Tutor Free, descrevendo seus componentes principais, suas interações e as decisões de design que moldaram sua estrutura.

## Sumário

1.  [Visão Geral](#1-visão-geral)
2.  [Componentes Principais](#2-componentes-principais)
    *   [Módulo Principal (`main.py`)](#módulo-principal-mainpy)
    *   [Agentes (`agents/`)](#agentes-agents)
    *   [Ferramentas (`tools/`)](#ferramentas-tools)
    *   [Utilitários (`utils/`)](#utilitários-utils)
    *   [Configuração (`config.py`, `.env`)](#configuração-configpy-env)
    *   [Cache de Respostas (`response_cache.json`)](#cache-de-respostas-response_cachejson)
3.  [Fluxo de Execução](#3-fluxo-de-execução)
4.  [Considerações de Design](#4-considerações-de-design)
    *   [Modularidade](#modularidade)
    *   [Otimização de Custos e Desempenho](#otimização-de-custos-e-desempenho)
    *   [Extensibilidade](#extensibilidade)
    *   [Segurança](#segurança)
5.  [Diagrama de Componentes](#5-diagrama-de-componentes)

---

## 1. Visão Geral

O Discord AI Tutor Free é um bot Discord que integra capacidades de inteligência artificial para fornecer tutoria e respostas. A arquitetura é projetada para ser leve, eficiente e fácil de manter, com foco na utilização otimizada de recursos de APIs gratuitas.

## 2. Componentes Principais

### Módulo Principal (`main.py`)

-   **Responsabilidade**: Ponto de entrada da aplicação. Inicializa o cliente Discord, carrega as configurações e variáveis de ambiente, e gerencia o ciclo de vida do bot.
-   **Interações**: Orquestra a comunicação entre o cliente Discord e os agentes/ferramentas.

### Agentes (`agents/`)

-   **Responsabilidade**: Contêm a lógica de negócios específica para as interações de IA. Cada agente pode ser especializado em um tipo de tutoria ou funcionalidade.
-   **Exemplo**: `discord_tutor.py` (agente principal para tutoria de IA).
-   **Interações**: Utilizam os módulos em `tools/` e `utils/` para realizar suas tarefas.

### Ferramentas (`tools/`)

-   **Responsabilidade**: Fornecem funcionalidades auxiliares que podem ser utilizadas pelos agentes. São componentes reutilizáveis que encapsulam lógicas específicas.
-   **Exemplos**:
    -   `discord_monitor.py`: Lida com eventos do Discord.
    -   `simple_classifier.py`: Realiza classificação de texto.
    -   `response_cache.py`: Gerencia o cache de respostas da API.
-   **Interações**: Oferecem interfaces para os agentes e o módulo principal.

### Utilitários (`utils/`)

-   **Responsabilidade**: Contêm funções e classes de uso geral que suportam a lógica principal, mas não são ferramentas ou agentes por si só.
-   **Exemplos**:
    -   `free_tier_orchestrator.py`: Orquestra chamadas a APIs de IA, gerenciando limites e otimização.
    -   `prompt_builder.py`: Constrói prompts formatados para as APIs de IA.
-   **Interações**: Utilizados por agentes e outras ferramentas.

### Configuração (`config.py`, `.env`)

-   **Responsabilidade**: Gerenciam as configurações da aplicação e variáveis de ambiente sensíveis (tokens, chaves de API).
-   **`config.py`**: Contém configurações estáticas ou padrão.
-   **`.env`**: Armazena variáveis de ambiente que são carregadas em tempo de execução, garantindo que credenciais não sejam expostas no código-fonte.

### Cache de Respostas (`response_cache.json`)

-   **Responsabilidade**: Um arquivo JSON persistente que armazena respostas da API de IA para reduzir chamadas repetidas e otimizar o desempenho e o uso da camada gratuita.

## 3. Fluxo de Execução

1.  **Inicialização**: `main.py` é executado, carregando configurações e inicializando o cliente Discord e os módulos necessários.
2.  **Escuta de Eventos**: O cliente Discord (via `discord_monitor.py` ou diretamente em `main.py`) escuta por novas mensagens ou comandos.
3.  **Processamento da Mensagem**: Uma mensagem recebida é encaminhada para o `DiscordTutorAgent`.
4.  **Classificação (Opcional)**: A mensagem pode ser passada para `simple_classifier.py` para determinar a intenção.
5.  **Geração de Resposta de IA**: O `DiscordTutorAgent` solicita uma resposta ao `free_tier_orchestrator.py`.
6.  **Verificação de Cache**: O `free_tier_orchestrator.py` verifica `response_cache.py` para ver se a resposta já existe.
    *   Se sim, a resposta é retornada do cache.
    *   Se não, `prompt_builder.py` constrói um prompt e o `free_tier_orchestrator.py` faz uma chamada à API do Google AI Studio.
7.  **Armazenamento em Cache**: A resposta da API é armazenada em `response_cache.json` via `response_cache.py`.
8.  **Resposta ao Usuário**: A resposta final é enviada de volta ao canal Discord.

## 4. Considerações de Design

### Modularidade

-   O projeto é dividido em módulos lógicos (`agents`, `tools`, `utils`) para promover a separação de preocupações, facilitar a manutenção e permitir o desenvolvimento independente de funcionalidades.

### Otimização de Custos e Desempenho

-   O sistema de cache (`response_cache.py`) é fundamental para minimizar chamadas repetidas à API de IA, o que é crucial para manter o projeto dentro dos limites da camada gratuita.
-   O `free_tier_orchestrator.py` é projetado para gerenciar e otimizar o uso da API, incluindo a lógica para lidar com limites de taxa.

### Extensibilidade

-   A arquitetura permite a fácil adição de novos agentes (para diferentes tipos de tutoria), novas ferramentas (para funcionalidades adicionais) ou a integração com outras APIs de IA.

### Segurança

-   As credenciais sensíveis são gerenciadas através de variáveis de ambiente (`.env`), garantindo que não sejam expostas no código-fonte.

## 5. Diagrama de Componentes

```mermaid
component-diagram
    direction LR
    
    component "Discord User" as User
    component "Discord Client (main.py)" as Main
    component "Discord Monitor (tools/discord_monitor.py)" as DiscordMonitor
    component "Discord Tutor Agent (agents/discord_tutor.py)" as TutorAgent
    component "Simple Classifier (tools/simple_classifier.py)" as Classifier
    component "Free Tier Orchestrator (utils/free_tier_orchestrator.py)" as Orchestrator
    component "Prompt Builder (utils/prompt_builder.py)" as PromptBuilder
    component "Response Cache (tools/response_cache.py)" as Cache
    component "Google AI Studio API" as GoogleAPI
    database "response_cache.json" as CacheDB
    
    User --|> Main : Mensagem/Comando
    Main --|> DiscordMonitor : Eventos Discord
    Main --|> TutorAgent : Processar Mensagem
    
    TutorAgent --|> Classifier : Classificar Mensagem (Opcional)
    TutorAgent --|> Orchestrator : Solicitar Resposta IA
    
    Orchestrator --|> Cache : Verificar/Armazenar Cache
    Orchestrator --|> PromptBuilder : Construir Prompt
    Orchestrator --|> GoogleAPI : Chamar API IA
    
    Cache --|> CacheDB : Ler/Escrever
    GoogleAPI --|> Orchestr : Resposta IA
    
    Orchestrator --|> TutorAgent : Resposta IA
    TutorAgent --|> Main : Resposta Formatada
    Main --|> User : Enviar Resposta
