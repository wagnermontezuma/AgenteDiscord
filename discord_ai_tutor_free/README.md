# Discord AI Tutor (Free Tier)

Este projeto implementa um bot de Discord que atua como um tutor de IA, utilizando a API gratuita do Google AI Studio. Ele é projetado para ser eficiente e otimizado para o uso da camada gratuita, incluindo um sistema de cache local para minimizar chamadas à API.

## Estrutura do Projeto

```
discord_ai_tutor_free/
├── agents/
│ ├── __init__.py
│ └── discord_tutor.py        # Lógica principal do bot e interação com a IA
├── tools/
│ ├── __init__.py
│ ├── discord_monitor.py      # Monitora atividades do Discord (mensagens, comandos)
│ ├── simple_classifier.py    # Classifica intenções de mensagens para otimização
│ └── response_cache.py       # Gerencia o cache de respostas da API
├── utils/
│ ├── __init__.py
│ └── free_tier_orchestrator.py # Orquestra chamadas à API e gerencia limites
├── main.py                   # Ponto de entrada principal do bot
├── requirements.txt          # Dependências do Python
├── .env.example              # Exemplo de variáveis de ambiente
├── config.py                 # Configurações globais e de logging
├── response_cache.json       # Arquivo de cache para respostas da API
├── docs/                     # Documentação técnica e de contribuição
├── deploy/                   # Scripts de deploy e Dockerfile
└── README.md                 # Este arquivo
```

## Guia Completo de Instalação e Configuração

Siga os passos abaixo para configurar e executar o bot.

### 1. Pré-requisitos

Certifique-se de ter o Python 3.9 ou superior e o `pip` instalados em seu sistema. Para a containerização com Docker, você precisará ter o [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

### 2. Clonar o Repositório

Abra seu terminal ou prompt de comando e clone o repositório:

```bash
git clone https://github.com/seu-usuario/discord-ai-tutor-free.git # Substitua pela URL do seu repositório
cd discord_ai_tutor_free
```

### 3. Configurar o Ambiente Virtual (Recomendado)

É altamente recomendável usar um ambiente virtual para isolar as dependências do projeto.

```bash
python -m venv venv
# No Windows
.\venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate
```

### 4. Instalar Dependências

Com o ambiente virtual ativado, instale as dependências listadas no `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 5. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (na mesma pasta que `main.py`) com base no `.env.example`.

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha com suas credenciais:

```
DISCORD_BOT_TOKEN=SEU_TOKEN_DO_BOT_DISCORD
GOOGLE_API_KEY=SUA_CHAVE_API_DO_GOOGLE_AI_STUDIO
```

- **DISCORD_BOT_TOKEN**: Obtenha este token criando um novo aplicativo de bot no [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications). Certifique-se de habilitar os "Privileged Gateway Intents" necessários (Message Content Intent, etc.).
- **GOOGLE_API_KEY**: Obtenha sua chave de API no [Google AI Studio](https://aistudio.google.com/app/apikey).

### 6. Criar o Bot Discord e Obter o Token

1. Vá para o [Portal do Desenvolvedor do Discord](https://discord.com/developers/applications).
2. Clique em "New Application" e dê um nome ao seu bot.
3. Na barra lateral esquerda, vá para "Bot".
4. Clique em "Add Bot" e confirme.
5. Copie o "TOKEN" do bot e cole-o no seu arquivo `.env` como `DISCORD_BOT_TOKEN`.
6. Em "Privileged Gateway Intents", ative "MESSAGE CONTENT INTENT".
7. Para adicionar o bot ao seu servidor, vá para "OAuth2" -> "URL Generator".
8. Em "SCOPES", selecione `bot`.
9. Em "BOT PERMISSIONS", selecione as permissões necessárias (ex: `Send Messages`, `Read Message History`).
10. Copie a URL gerada e cole-a no seu navegador para adicionar o bot ao seu servidor.

### 7. Obter a API Key do Google AI Studio

1. Acesse o [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Faça login com sua conta Google.
3. Crie uma nova chave de API ou use uma existente.
4. Copie a chave de API e cole-a no seu arquivo `.env` como `GOOGLE_API_KEY`.

### 8. Teste de Funcionamento

Após configurar tudo, você pode iniciar o bot executando o arquivo `main.py`:

```bash
python main.py
```

O bot deverá se conectar ao Discord e começar a responder às mensagens. Teste enviando uma mensagem para o bot no seu servidor Discord.

## Uso do Cache

Este bot utiliza um sistema de cache local (`response_cache.json`) para armazenar respostas da API do Google AI Studio. Isso ajuda a reduzir o número de chamadas à API, economizando seu limite da camada gratuita. As respostas são armazenadas por um tempo configurável (padrão: 1 hora) e são invalidadas após esse período.

## Logging

O logging é configurado para exibir mensagens no console e salvar em um arquivo `discord_ai_tutor.log` na raiz do projeto. Isso é útil para depuração e monitoramento do comportamento do bot.

## Docker e Deploy

Para facilitar o deploy e a portabilidade, o bot pode ser containerizado usando Docker.

### Construir a Imagem Docker

```bash
docker build -t discord-ai-tutor-free .
```

### Executar o Container Docker

```bash
docker run -d --name discord-tutor-bot --env-file ./.env discord-ai-tutor-free
```

Certifique-se de que o arquivo `.env` esteja na mesma pasta onde você executa o comando `docker run`.

### Scripts de Deploy Automatizado

Os seguintes scripts são fornecidos para automatizar o processo de deploy:

- `deploy.sh`: Script completo para construir e executar o container Docker.
- `setup.py`: Script de instalação automatizada (para ambiente local ou CI/CD).
- `health_check.py`: Script para verificar a saúde do bot após o deploy.
- `backup.py`: Script para fazer backup do cache e configurações.

Consulte a documentação em `docs/` para mais detalhes sobre como usar esses scripts.

## Troubleshooting Comum

Consulte o arquivo `docs/TROUBLESHOOTING.md` para soluções para problemas comuns.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests. Consulte `docs/CONTRIBUTING.md` para um guia detalhado.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
