# Tech Context: Discord AI Tutor Free

## Technologies Used

- **Python**: Linguagem de programação principal para o desenvolvimento do bot.
- **Discord.py**: Biblioteca Python para interagir com a API do Discord.
- **Google AI Studio API (Gemini API)**: Para capacidades de inteligência artificial e geração de texto.
- **JSON**: Formato para armazenamento de cache (`response_cache.json`).
- **Docker**: Para containerização da aplicação, facilitando o deploy e a portabilidade.
- **Bash Scripting**: Para scripts de deploy automatizados.
- **`python-dotenv`**: Para carregar variáveis de ambiente de arquivos `.env`.

## Development Setup

- **Ambiente Virtual**: Recomenda-se o uso de um ambiente virtual (`venv` ou `conda`) para gerenciar as dependências do projeto.
- **Gerenciamento de Dependências**: As dependências são listadas no arquivo `requirements.txt`.
- **Variáveis de Ambiente**: As configurações sensíveis (como tokens do Discord e chaves de API do Google AI Studio) são gerenciadas através de variáveis de ambiente, carregadas de um arquivo `.env`. Um arquivo `.env.example` é fornecido como modelo.
- **Estrutura de Diretórios**:
    - `discord_ai_tutor_free/`: Diretório raiz do projeto.
        - `agents/`: Contém a lógica principal dos agentes de IA (e.g., `discord_tutor.py`).
        - `tools/`: Contém ferramentas auxiliares (e.g., `discord_monitor.py`, `response_cache.py`, `simple_classifier.py`).
        - `utils/`: Contém utilitários gerais (e.g., `prompt_builder.py`, `free_tier_orchestrator.py`).
        - `tests/`: Contém testes de unidade e integração.
        - `memory-bank/`: Contém a documentação interna do projeto.
        - `docs/`: (A ser criado) Contém a documentação técnica e de usuário.
        - `main.py`: Ponto de entrada da aplicação.
        - `config.py`: Arquivo de configuração.
        - `requirements.txt`: Lista de dependências Python.
        - `response_cache.json`: Arquivo de cache.
        - `.env.example`: Exemplo de arquivo de variáveis de ambiente.
        - `.env`: Arquivo de variáveis de ambiente (não versionado).
        - `README.md`: Documentação principal do projeto.

## Technical Constraints

- **Limites da API do Google AI Studio**: O uso da API pode estar sujeito a limites de taxa e cotas, o que é mitigado pelo sistema de cache.
- **Recursos do Servidor Discord**: O bot deve ser otimizado para operar dentro dos limites de recursos de um servidor Discord (e.g., tempo de resposta, tamanho da mensagem).
- **Compatibilidade Python**: O projeto é desenvolvido para Python 3.9-slim, conforme especificado no Dockerfile.
- **Segurança**: As chaves de API e tokens devem ser mantidos em segurança e nunca expostos em código-fonte ou logs.
