import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class SimpleClassifier:
    def __init__(self, keywords: Dict[str, List[str]] = None):
        """
        Inicializa o classificador com um dicionário de palavras-chave.
        As chaves do dicionário são as categorias e os valores são listas de palavras-chave.
        """
        self.keywords = keywords if keywords is not None else self._default_keywords()
        logger.info(f"SimpleClassifier inicializado com {len(self.keywords)} categorias.")

    def _default_keywords(self) -> Dict[str, List[str]]:
        """Define um conjunto padrão de palavras-chave para classificação."""
        return {
            "concept": ["o que é", "conceito", "explicar", "definir", "machine learning", "redes neurais", "inteligência artificial", "ia", "algoritmo", "modelo", "aprendizado de máquina", "deep learning"],
            "code": ["código", "implementar", "python", "erro", "bug", "tensorflow", "pytorch", "javascript", "java", "c++", "html", "css", "sql", "função", "classe", "variável", "loop", "condicional", "debug", "sintaxe", "biblioteca", "framework"],
            "resource": ["curso", "material", "livro", "tutorial", "recomenda", "onde aprender", "documentação", "guia", "exemplo", "artigo", "site", "plataforma"],
            "general": ["olá", "oi", "bom dia", "boa tarde", "boa noite", "e aí", "salve", "tchau", "até mais", "adeus", "flw", "bye", "ajuda", "socorro", "problema", "não consigo", "obrigado", "valeu", "agradeço", "bot", "discord", "você", "seu nome", "quem é você", "qual", "como", "por que", "quando", "onde", "quem", "me diga", "fale sobre"],
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza o texto para processamento."""
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\s]', '', text) # Remove caracteres especiais
        text = re.sub(r'\s+', ' ', text) # Normaliza múltiplos espaços
        return text

    def _detect_language(self, text: str) -> str:
        """
        Detecta o idioma da mensagem (Português ou Inglês) com base em palavras-chave simples.
        Esta é uma detecção simplificada e pode não ser 100% precisa.
        """
        normalized_text = self._normalize_text(text)
        
        portuguese_keywords = ["o que é", "como", "por que", "você", "obrigado", "ajuda", "sim", "não", "bom dia"]
        english_keywords = ["what is", "how to", "why", "you", "thank you", "help", "yes", "no", "good morning"]

        pt_score = sum(1 for kw in portuguese_keywords if kw in normalized_text)
        en_score = sum(1 for kw in english_keywords if kw in normalized_text)

        if pt_score > en_score:
            return "pt"
        elif en_score > pt_score:
            return "en"
        else:
            return "unknown" # Ou um padrão, se não houver distinção clara

    def classify_question(self, text: str) -> Dict[str, Any]:
        """
        Classifica uma pergunta, retornando a(s) categoria(s) e um score de confiança.
        """
        normalized_text = self._normalize_text(text)
        detected_language = self._detect_language(text)
        
        scores: Dict[str, int] = {category: 0 for category in self.keywords}
        
        # Contagem de ocorrências de palavras-chave
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in normalized_text:
                    scores[category] += 1
        
        # Determina a(s) categoria(s) com maior score
        max_score = 0
        for score in scores.values():
            if score > max_score:
                max_score = score
        
        classified_categories: List[str] = []
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    classified_categories.append(category)
        
        # Fallback para 'general' se nenhuma categoria específica for detectada
        if not classified_categories:
            classified_categories.append("general")
            confidence_score = 0.1 # Baixa confiança para fallback
        else:
            # Calcula um score de confiança simples (pode ser aprimorado)
            # Por exemplo, a proporção de palavras-chave encontradas em relação ao total de palavras na pergunta
            total_keywords_in_message = sum(scores.values())
            total_words_in_message = len(normalized_text.split())
            
            if total_words_in_message > 0:
                confidence_score = min(1.0, total_keywords_in_message / total_words_in_message)
            else:
                confidence_score = 0.0
            
            # Ajusta o score para ser mais significativo
            confidence_score = round(confidence_score * 0.5 + (max_score / 10) * 0.5, 2) # Combina densidade e score máximo
            confidence_score = min(1.0, confidence_score) # Garante que não exceda 1.0

        logger.debug(f"Mensagem '{text}' classificada como: {classified_categories} com confiança {confidence_score}. Idioma: {detected_language}")
        
        return {
            "categories": classified_categories,
            "confidence_score": confidence_score,
            "language": detected_language,
            "raw_scores": scores # Para depuração
        }

    def add_keywords(self, category: str, new_keywords: List[str]):
        """Adiciona novas palavras-chave a uma categoria existente ou cria uma nova."""
        if category not in self.keywords:
            self.keywords[category] = []
            logger.info(f"Nova categoria '{category}' criada.")
        
        added_count = 0
        for keyword in new_keywords:
            normalized_keyword = keyword.lower()
            if normalized_keyword not in [k.lower() for k in self.keywords[category]]:
                self.keywords[category].append(normalized_keyword)
                added_count += 1
        logger.info(f"{added_count} novas palavras-chave adicionadas à categoria '{category}'.")

    def remove_keywords(self, category: str, keywords_to_remove: List[str]):
        """Remove palavras-chave de uma categoria."""
        if category in self.keywords:
            initial_count = len(self.keywords[category])
            keywords_to_remove_normalized = [r.lower() for r in keywords_to_remove]
            self.keywords[category] = [
                k for k in self.keywords[category] 
                if k.lower() not in keywords_to_remove_normalized
            ]
            removed_count = initial_count - len(self.keywords[category])
            logger.info(f"{removed_count} palavras-chave removidas da categoria '{category}'.")
            if not self.keywords[category]:
                logger.warning(f"Categoria '{category}' está vazia após remoção de palavras-chave.")
        else:
            logger.warning(f"Tentativa de remover palavras-chave de categoria inexistente: '{category}'.")

# Exemplo de uso (para testes internos, pode ser removido em produção)
if __name__ == "__main__":
    classifier = SimpleClassifier()

    print("\n--- Teste de Classificação e Confiança ---")
    test_questions = [
        "O que é machine learning?", # Concept
        "Como implementar um algoritmo de classificação em Python?", # Code, Concept
        "Recomende um livro sobre redes neurais.", # Resource, Concept
        "Olá, tudo bem?", # General
        "What is deep learning?", # Concept (English)
        "How to fix a bug in my Java code?", # Code (English)
        "Onde posso encontrar um tutorial de TensorFlow?", # Resource, Code, Concept
        "Qual a capital do Brasil?", # General (fallback)
        "Me explique o conceito de backpropagation em redes neurais.", # Concept
        "Tenho um erro no meu código Python com PyTorch, pode ajudar?", # Code, Concept
        "Quero aprender sobre IA, qual o melhor curso?", # Resource, Concept
        "Hello, how are you?", # General (English)
        "Me diga sobre inteligência artificial.", # Concept
        "Qual a sintaxe de um loop for em JavaScript?", # Code
        "Preciso de um material sobre SQL para iniciantes.", # Resource, Code
        "Qual a diferença entre machine learning e deep learning?", # Concept
        "Como debugar um programa em C++?", # Code
        "Existe algum guia para usar a biblioteca Pandas em Python?", # Resource, Code
        "O que é um framework?", # Concept
        "Qual o seu nome?" # General
    ]

    for i, question in enumerate(test_questions):
        result = classifier.classify_question(question)
        print(f"Q{i+1}: '{question}'")
        print(f"  -> Categorias: {result['categories']}, Confiança: {result['confidence_score']:.2f}, Idioma: {result['language']}")
        # print(f"  -> Scores Brutos: {result['raw_scores']}") # Para depuração
    
    print("\n--- Teste de Adição e Remoção de Palavras-chave ---")
    classifier.add_keywords("new_category", ["nova palavra", "teste"])
    result_new = classifier.classify_question("Isso é uma nova palavra para teste.")
    print(f"Mensagem: 'Isso é uma nova palavra para teste.' -> Categorias: {result_new['categories']}")
    assert "new_category" in result_new['categories']

    classifier.remove_keywords("new_category", ["nova palavra"])
    result_after_removal = classifier.classify_question("Isso é uma nova palavra para teste.")
    print(f"Mensagem: 'Isso é uma nova palavra para teste.' (após remoção) -> Categorias: {result_after_removal['categories']}")
    assert "new_category" not in result_after_removal['categories'] # Pode ainda estar lá se "teste" for suficiente

    print("\nTestes concluídos.")
