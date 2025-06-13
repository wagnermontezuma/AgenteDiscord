# System Patterns: Discord AI Tutor Free

## System Architecture

O Discord AI Tutor Free é arquitetado como um bot Discord modular, com componentes distintos para lidar com diferentes aspectos da funcionalidade. A arquitetura é projetada para ser escalável e de fácil manutenção.

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

## Key Technical Decisions

- **Modularidade**: O código é dividido em módulos (`agents`, `tools`, `utils`, `tests`) para promover a separação de preocupações e facilitar o desenvolvimento e a manutenção.
- **Cache de Respostas**: Implementação de um sistema de cache (`response_cache.py`) para armazenar respostas geradas pela IA, reduzindo chamadas repetidas à API e melhorando a performance.
- **Orquestração de Chamadas de IA**: O `Free Tier Orchestrator` gerencia as interações com a API de IA, potencialmente otimizando o uso de recursos e lidando com limites de taxa.
- **Classificação Simples**: Um classificador (`simple_classifier.py`) pode ser usado para categorizar mensagens de entrada, permitindo respostas mais direcionadas ou o roteamento para diferentes "agentes" de IA.
- **Variáveis de Ambiente**: Utilização de arquivos `.env` para gerenciar configurações sensíveis (como chaves de API), garantindo segurança e flexibilidade no deploy.

## Design Patterns in Use

- **Observer Pattern**: O `Discord Monitor` pode ser visto como um observador que escuta eventos do Discord e notifica o `main.py` ou outros componentes.
- **Singleton Pattern**: O sistema de cache (`response_cache.py`) pode ser implementado como um singleton para garantir que haja apenas uma instância do cache em toda a aplicação.
- **Strategy Pattern**: O `Free Tier Orchestrator` pode empregar o Strategy Pattern para alternar entre diferentes modelos de IA ou estratégias de chamada de API, dependendo da disponibilidade ou custo.
- **Dependency Injection**: As dependências (como a API do Google AI Studio) são injetadas nos componentes que as utilizam, facilitando testes e substituições.

## Component Relationships

- `main.py`: Ponto de entrada da aplicação, orquestra a interação entre os componentes.
- `discord_tutor.py`: Contém a lógica principal do bot Discord, interagindo com o `discord_monitor` e o `free_tier_orchestrator`.
- `discord_monitor.py`: Responsável por monitorar eventos do Discord e interagir com a API do Discord.
- `free_tier_orchestrator.py`: Gerencia as chamadas para a API de IA, utilizando o `prompt_builder` e o `response_cache`.
- `prompt_builder.py`: Constrói os prompts para a API de IA com base nas interações do usuário.
- `response_cache.py`: Gerencia o armazenamento e recuperação de respostas em cache.
- `simple_classifier.py`: Classifica as mensagens de entrada para determinar a intenção do usuário.
