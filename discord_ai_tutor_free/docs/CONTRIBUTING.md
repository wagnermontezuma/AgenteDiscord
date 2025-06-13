# Guia de Contribuição para Discord AI Tutor Free

Agradecemos o seu interesse em contribuir para o projeto Discord AI Tutor Free! Suas contribuições são valiosas para melhorar e expandir este bot de tutoria de IA.

Este guia detalha o processo para configurar seu ambiente de desenvolvimento, fazer alterações e enviar suas contribuições.

## Sumário

1.  [Código de Conduta](#1-código-de-conduta)
2.  [Como Contribuir](#2-como-contribuir)
    *   [Reportar Bugs](#reportar-bugs)
    *   [Sugerir Novas Funcionalidades](#sugerir-novas-funcionalidades)
    *   [Contribuir com Código](#contribuir-com-código)
3.  [Configuração do Ambiente de Desenvolvimento](#3-configuração-do-ambiente-de-desenvolvimento)
    *   [Pré-requisitos](#pré-requisitos)
    *   [Clonar o Repositório](#clonar-o-repositório)
    *   [Configurar Ambiente Virtual](#configurar-ambiente-virtual)
    *   [Instalar Dependências](#instalar-dependências)
    *   [Configurar Variáveis de Ambiente](#configurar-variáveis-de-ambiente)
    *   [Executar Testes](#executar-testes)
4.  [Processo de Desenvolvimento](#4-processo-de-desenvolvimento)
    *   [Criar uma Nova Branch](#criar-uma-nova-branch)
    *   [Fazer Suas Alterações](#fazer-suas-alterações)
    *   [Testar Suas Alterações](#testar-suas-alterações)
    *   [Documentar Suas Alterações](#documentar-suas-alterações)
5.  [Enviando um Pull Request (PR)](#5-enviando-um-pull-request-pr)
    *   [Diretrizes para Commits](#diretrizes-para-commits)
    *   [Revisão do Código](#revisão-do-código)

---

## 1. Código de Conduta

Este projeto adota o [Código de Conduta do Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct.html). Ao participar, espera-se que você siga este código.

## 2. Como Contribuir

Existem várias maneiras de contribuir para o projeto:

### Reportar Bugs

Se você encontrar um bug, por favor, abra uma [Issue no GitHub](https://github.com/seu-usuario/discord-ai-tutor-free/issues) (substitua pela URL do seu repositório). Ao reportar um bug, inclua:

-   Uma descrição clara e concisa do problema.
-   Passos para reproduzir o bug.
-   Comportamento esperado vs. comportamento atual.
-   Capturas de tela ou logs, se aplicável.
-   Sua versão do Python e das dependências.

### Sugerir Novas Funcionalidades

Se você tiver uma ideia para uma nova funcionalidade, abra uma [Issue no GitHub](https://github.com/seu-usuario/discord-ai-tutor-free/issues) e descreva sua sugestão. Explique o problema que a funcionalidade resolveria e como ela beneficiaria os usuários.

### Contribuir com Código

Se você deseja contribuir com código, siga o processo detalhado abaixo.

## 3. Configuração do Ambiente de Desenvolvimento

Para começar a desenvolver, você precisará configurar seu ambiente:

### Pré-requisitos

-   Python 3.9+
-   `pip` (gerenciador de pacotes do Python)
-   `git`

### Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/discord-ai-tutor-free.git
cd discord_ai_tutor_free
```

### Configurar Ambiente Virtual

```bash
python -m venv venv
# No Windows
.\venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate
```

### Instalar Dependências

```bash
pip install -r requirements.txt
```

### Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no `.env.example` e preencha suas credenciais do Discord e Google AI Studio.

```bash
cp .env.example .env
```

Edite `.env`:

```
DISCORD_BOT_TOKEN=SEU_TOKEN_DO_BOT_DISCORD
GOOGLE_API_KEY=SUA_CHAVE_API_DO_GOOGLE_AI_STUDIO
```

### Executar Testes

É crucial executar os testes existentes para garantir que suas alterações não introduzam regressões.

```bash
pytest
```

## 4. Processo de Desenvolvimento

### Criar uma Nova Branch

Sempre crie uma nova branch para suas alterações. Use um nome descritivo para a branch (ex: `feature/nova-funcionalidade`, `bugfix/corrigir-erro-cache`).

```bash
git checkout -b feature/sua-nova-funcionalidade
```

### Fazer Suas Alterações

Implemente suas alterações. Mantenha seus commits pequenos e focados em uma única alteração lógica.

### Testar Suas Alterações

Execute os testes existentes (`pytest`) e adicione novos testes para cobrir suas alterações, se aplicável. Certifique-se de que todos os testes passem.

### Documentar Suas Alterações

Se suas alterações adicionarem novas funcionalidades, modificarem o comportamento existente ou introduzirem novas configurações, atualize a documentação relevante (ex: `README.md`, `docs/API.md`, `docs/ARCHITECTURE.md`).

## 5. Enviando um Pull Request (PR)

Quando suas alterações estiverem prontas, envie um Pull Request para a branch `main` do repositório.

### Diretrizes para Commits

-   Use mensagens de commit claras e concisas.
-   Comece a mensagem com um verbo imperativo (ex: "Adicionar", "Corrigir", "Atualizar").
-   Exemplo: `feat: Adicionar sistema de cache para respostas da API`
-   Exemplo: `fix: Corrigir erro de permissão no Discord`

### Revisão do Código

Seu Pull Request será revisado por um mantenedor do projeto. Esteja preparado para discutir suas alterações e fazer ajustes com base no feedback. Uma vez aprovado, suas alterações serão mescladas.

Agradecemos novamente por sua contribuição!
