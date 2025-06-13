import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class PromptBuilder:
    def __init__(self, current_version: str = "v1.0"):
        self.templates = self._load_templates()
        self.current_version = current_version
        logger.info(f"PromptBuilder inicializado com a versão: {self.current_version}")

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Carrega os templates de prompts, incluindo diferentes versões.
        Em um sistema mais complexo, isso poderia vir de um arquivo ou DB.
        """
        return {
            "v1.0": {
                "concept": """
Situação: Você é um tutor de IA que explica conceitos complexos de forma didática.
Desafio: Explicar o conceito de {topic} de forma clara e concisa.
Audiência: Usuário com nível {user_level} em IA.
Formato: Resposta concisa (máximo 300 palavras), use analogias simples.
Fundamentos: Linguagem acessível, exemplos práticos, termine com uma pergunta para verificar a compreensão.
""",
                "code": """
Situação: Você é um assistente de programação especializado em IA.
Desafio: Ajudar com o problema de código relacionado a {topic} e {language}.
Audiência: Usuário com nível {user_level} em programação.
Formato: Forneça código funcional, explique cada parte do código, seja direto e objetivo.
Fundamentos: Segurança do código, boas práticas, clareza na explicação.
""",
                "resource": """
Situação: Você é um recomendador de recursos de aprendizado de IA.
Desafio: Recomendar materiais gratuitos sobre {topic}.
Audiência: Usuário com nível {user_level} em IA.
Formato: Lista de recursos (cursos, livros, tutoriais, artigos), com links (se possível).
Fundamentos: Foco em recursos GRATUITOS e de alta qualidade, seja encorajador.
""",
                "general": """
Situação: Você é um assistente de IA amigável e prestativo.
Desafio: Responder à pergunta geral: "{question}".
Audiência: Usuário geral.
Formato: Resposta educada e concisa.
Fundamentos: Clareza, utilidade, segurança.
"""
            },
            # Futuras versões de templates podem ser adicionadas aqui
            "v1.1": {
                "concept": """
Situação: Você é um tutor de IA que explica conceitos complexos de forma didática.
Desafio: Explicar o conceito de {topic} de forma clara e concisa.
Audiência: Usuário com nível {user_level} em IA.
Formato: Resposta concisa (máximo 250 palavras), use analogias simples.
Fundamentos: Linguagem acessível, exemplos práticos, termine com uma pergunta para verificar a compreensão.
(Versão 1.1: Mais concisa)
""",
                "code": """
Situação: Você é um assistente de programação especializado em IA.
Desafio: Ajudar com o problema de código relacionado a {topic} e {language}.
Audiência: Usuário com nível {user_level} em programação.
Formato: Forneça código funcional, explique cada parte do código, seja direto e objetivo.
Fundamentos: Segurança do código, boas práticas, clareza na explicação.
(Versão 1.1: Sem mudanças significativas)
""",
                "resource": """
Situação: Você é um recomendador de recursos de aprendizado de IA.
Desafio: Recomendar materiais gratuitos sobre {topic}.
Audiência: Usuário com nível {user_level} em IA.
Formato: Lista de recursos (cursos, livros, tutoriais, artigos), com links (se possível).
Fundamentos: Foco em recursos GRATUITOS e de alta qualidade, seja encorajador.
(Versão 1.1: Sem mudanças significativas)
""",
                "general": """
Situação: Você é um assistente de IA amigável e prestativo.
Desafio: Responder à pergunta geral: "{question}".
Audiência: Usuário geral.
Formato: Resposta educada e concisa.
Fundamentos: Clareza, utilidade, segurança.
(Versão 1.1: Sem mudanças significativas)
"""
            }
        }

    def get_template(self, agent_type: str, version: Optional[str] = None) -> Optional[str]:
        """Retorna o template de prompt para um tipo de agente e versão específicos."""
        if version is None:
            version = self.current_version
        
        if version in self.templates and agent_type in self.templates[version]:
            return self.templates[version][agent_type]
        
        logger.warning(f"Template para '{agent_type}' na versão '{version}' não encontrado. Retornando None.")
        return None

    def build_prompt(self, agent_type: str, data: Dict[str, Any], version: Optional[str] = None) -> Optional[str]:
        """
        Constrói um prompt completo usando o template e os dados fornecidos.
        """
        template_str = self.get_template(agent_type, version)
        if not template_str:
            return None
        
        try:
            # Preenche o template com os dados
            prompt = template_str.format(**data)
            logger.debug(f"Prompt construído para '{agent_type}': {prompt[:100]}...")
            return prompt
        except KeyError as e:
            logger.error(f"Erro ao construir prompt para '{agent_type}': Chave '{e}' faltando nos dados. Dados: {data}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao construir prompt para '{agent_type}': {e}")
            return None

    def build_scaff_prompt(self, question: str, context: Optional[str], history: Optional[list]) -> str:
        """Constrói um prompt utilizando o framework S.C.A.F.F."""
        parts = [
            "S.C.A.F.F. Framework:",
            "1. **S**tep-by-step: Think step-by-step.",
            "2. **C**ontext: Use the provided context.",
            "3. **A**ction: Formulate a concise answer.",
            "4. **F**ormat: Ensure the response is well-structured.",
            "5. **F**act-check: Verify accuracy.",
            "",
        ]

        if context:
            parts.append(f"Context: {context}")

        if history:
            parts.append("History:")
            for entry in history:
                role = entry.get("role", "user").capitalize()
                content = entry.get("content", "")
                parts.append(f"{role}: {content}")

        parts.append(f"Question: {question}")

        prompt = "\n".join(parts)
        logger.debug(f"Prompt S.C.A.F.F gerado: {prompt[:100]}...")
        return prompt

    def count_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em uma string.
        Esta é uma estimativa simplificada (baseada em palavras) e não uma contagem exata de tokens de LLM.
        Para contagem exata, seria necessário usar a API do Google AI ou uma biblioteca específica.
        """
        # Uma estimativa simples: 1 token ~ 4 caracteres ou 0.75 palavras
        # Usaremos palavras para uma estimativa mais robusta para o usuário.
        words = text.split()
        return len(words) # Retorna o número de palavras como estimativa de tokens

    def optimize_prompt(self, agent_type: str, data: Dict[str, Any], max_tokens: int = 500, version: Optional[str] = None) -> Optional[str]:
        """
        Constrói e tenta otimizar o prompt para um número máximo de tokens.
        A otimização aqui é uma simplificação: apenas tenta usar uma versão mais concisa se disponível.
        Em um cenário real, envolveria sumarização ou truncamento inteligente.
        """
        initial_prompt = self.build_prompt(agent_type, data, version)
        if not initial_prompt:
            return None

        initial_tokens = self.count_tokens(initial_prompt)
        logger.info(f"Prompt inicial para '{agent_type}' tem {initial_tokens} tokens.")

        if initial_tokens <= max_tokens:
            return initial_prompt
        
        logger.warning(f"Prompt para '{agent_type}' excede {max_tokens} tokens ({initial_tokens} tokens). Tentando otimizar.")

        # Tenta usar uma versão mais concisa se disponível (ex: v1.1 para 'concept')
        if version == "v1.0" and "v1.1" in self.templates:
            optimized_template = self.get_template(agent_type, "v1.1")
            if optimized_template:
                optimized_prompt = optimized_template.format(**data)
                optimized_tokens = self.count_tokens(optimized_prompt)
                if optimized_tokens <= max_tokens:
                    logger.info(f"Prompt otimizado para '{agent_type}' usando v1.1: {optimized_tokens} tokens.")
                    return optimized_prompt
                else:
                    logger.warning(f"Otimização com v1.1 ainda excede o limite ({optimized_tokens} tokens).")
        
        # Fallback: Truncar o prompt se ainda for muito longo (pode cortar no meio de uma frase)
        # Esta é uma medida de último recurso e pode degradar a qualidade.
        # Uma abordagem melhor seria sumarizar o contexto ou o desafio.
        if initial_tokens > max_tokens:
            # Estima o número de caracteres para o max_tokens (assumindo 1 token ~ 4 caracteres)
            max_chars = max_tokens * 4
            if len(initial_prompt) > max_chars:
                truncated_prompt = initial_prompt[:max_chars] + "..."
                logger.warning(f"Prompt truncado para '{agent_type}' para {len(truncated_prompt)} caracteres.")
                return truncated_prompt
        
        return initial_prompt # Retorna o prompt original se a otimização falhar ou não for necessária

    def set_current_version(self, version: str):
        """Define a versão atual dos templates a ser usada."""
        if version in self.templates:
            self.current_version = version
            logger.info(f"Versão atual dos prompts definida para: {self.current_version}")
        else:
            logger.warning(f"Versão '{version}' não encontrada. Mantendo a versão atual: {self.current_version}")

# Exemplo de uso (para testes internos, pode ser removido em produção)
if __name__ == "__main__":
    prompt_builder = PromptBuilder()

    print("\n--- Teste de Geração de Prompts ---")
    concept_data = {"topic": "Redes Neurais Convolucionais", "user_level": "iniciante"}
    concept_prompt = prompt_builder.build_prompt("concept", concept_data)
    print(f"Prompt de Conceito:\n{concept_prompt}\nTokens: {prompt_builder.count_tokens(concept_prompt)}")
    assert concept_prompt is not None

    code_data = {"topic": "depuração", "language": "Python", "user_level": "intermediário"}
    code_prompt = prompt_builder.build_prompt("code", code_data)
    print(f"\nPrompt de Código:\n{code_prompt}\nTokens: {prompt_builder.count_tokens(code_prompt)}")
    assert code_prompt is not None

    resource_data = {"topic": "Processamento de Linguagem Natural", "user_level": "avançado"}
    resource_prompt = prompt_builder.build_prompt("resource", resource_data)
    print(f"\nPrompt de Recurso:\n{resource_prompt}\nTokens: {prompt_builder.count_tokens(resource_prompt)}")
    assert resource_prompt is not None

    general_data = {"question": "Qual a previsão do tempo para amanhã?"}
    general_prompt = prompt_builder.build_prompt("general", general_data)
    print(f"\nPrompt Geral:\n{general_prompt}\nTokens: {prompt_builder.count_tokens(general_prompt)}")
    assert general_prompt is not None

    print("\n--- Teste de Otimização de Tokens ---")
    # Criar um prompt longo para testar otimização/truncamento
    long_concept_data = {
        "topic": "Aplicações avançadas de Machine Learning em bioinformática e descoberta de medicamentos, incluindo o uso de modelos de grafos e aprendizado por reforço para otimização de estruturas moleculares.",
        "user_level": "pesquisador"
    }
    # Teste com um limite baixo para forçar otimização/truncamento
    optimized_prompt = prompt_builder.optimize_prompt("concept", long_concept_data, max_tokens=50)
    print(f"\nPrompt Otimizado (max 50 tokens):\n{optimized_prompt}\nTokens: {prompt_builder.count_tokens(optimized_prompt)}")
    assert prompt_builder.count_tokens(optimized_prompt) <= 50 or "..." in optimized_prompt # Pode ser truncado

    # Teste com uma versão mais concisa
    prompt_builder.set_current_version("v1.1")
    optimized_prompt_v11 = prompt_builder.optimize_prompt("concept", concept_data, max_tokens=100)
    print(f"\nPrompt Otimizado (v1.1, max 100 tokens):\n{optimized_prompt_v11}\nTokens: {prompt_builder.count_tokens(optimized_prompt_v11)}")
    assert "Versão 1.1" in optimized_prompt_v11 # Verifica se a versão correta foi usada

    print("\n--- Teste de Versionamento ---")
    prompt_builder.set_current_version("v1.0")
    concept_prompt_v10 = prompt_builder.build_prompt("concept", concept_data)
    print(f"\nPrompt de Conceito (v1.0):\n{concept_prompt_v10}")
    assert "máximo 300 palavras" in concept_prompt_v10

    prompt_builder.set_current_version("v1.1")
    concept_prompt_v11 = prompt_builder.build_prompt("concept", concept_data)
    print(f"\nPrompt de Conceito (v1.1):\n{concept_prompt_v11}")
    assert "máximo 250 palavras" in concept_prompt_v11

    print("\nTestes do PromptBuilder concluídos.")
