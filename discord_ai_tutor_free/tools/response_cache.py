import json
import os
import hashlib
import re
import time
from typing import Optional, Dict, Any
import logging
import zlib

# Configuração de logging (pode ser movida para um módulo de utilidades de logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResponseCache:
    def __init__(self, cache_file: str = 'response_cache.json', ttl_hours: int = 24, compression_threshold: int = 1024):
        self.cache_file = cache_file
        self.ttl_seconds = ttl_hours * 3600
        self.compression_threshold = compression_threshold
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self._load_cache()
        self.cleanup_expired() # Limpa o cache na inicialização

    def _load_cache(self):
        """Carrega o cache do arquivo JSON."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Cache carregado de {self.cache_file}. Total de entradas: {len(self.cache)}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do cache: {e}. Iniciando com cache vazio.")
                self.cache = {}
            except Exception as e:
                logger.error(f"Erro ao carregar cache: {e}. Iniciando com cache vazio.")
                self.cache = {}
        else:
            logger.info(f"Arquivo de cache {self.cache_file} não encontrado. Iniciando com cache vazio.")

    def _save_cache(self):
        """Salva o cache no arquivo JSON."""
        try:
            import shutil
            if os.path.exists(self.cache_file):
                shutil.copyfile(self.cache_file, self.cache_file + ".bak")
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4)
            # Garante que sempre exista um arquivo de backup após salvar
            shutil.copyfile(self.cache_file, self.cache_file + ".bak")
            logger.debug(
                f"Cache salvo em {self.cache_file}. Total de entradas: {len(self.cache)}"
            )
        except Exception as e:
            logger.error(f"Erro ao salvar cache em {self.cache_file}: {e}")

    def _normalize_question(self, question: str) -> str:
        """Normaliza a pergunta para uso como chave de cache."""
        question = question.lower().strip()
        question = re.sub(r'[^a-z0-9\s]', '', question) # Remove caracteres especiais
        question = re.sub(r'\s+', ' ', question) # Normaliza múltiplos espaços
        return question

    def _generate_hash(self, text: str) -> str:
        """Gera um hash MD5 para o texto."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _compress_response(self, response: str) -> bytes:
        """Comprime a resposta usando zlib."""
        return zlib.compress(response.encode('utf-8'))

    def _decompress_response(self, compressed_response: bytes) -> str:
        """Descomprime a resposta usando zlib."""
        return zlib.decompress(compressed_response).decode('utf-8')

    def get_cached_response(self, question: str) -> Optional[str]:
        """
        Busca uma resposta no cache.
        Retorna a resposta se encontrada e não expirada, caso contrário, None.
        """
        normalized_question = self._normalize_question(question)
        question_hash = self._generate_hash(normalized_question)

        entry = self.cache.get(question_hash)
        if entry:
            if time.time() < entry['timestamp'] + self.ttl_seconds:
                self.hits += 1
                logger.debug(f"Cache HIT para a pergunta: '{question}'")
                response = entry['response']
                if entry.get('compressed', False):
                    response = self._decompress_response(bytes.fromhex(response))
                return response
            else:
                logger.debug(f"Entrada de cache expirada para a pergunta: '{question}'")
                self.misses += 1 # Incrementa miss apenas se expirado
                self.cache.pop(question_hash, None) # Remove a entrada expirada
                self._save_cache() # Salva para remover a entrada expirada
        else: # Se a entrada não existe
            self.misses += 1 # Incrementa miss apenas se não encontrado
            logger.debug(f"Cache MISS para a pergunta: '{question}'")
        return None

    def cache_response(self, question: str, response: str):
        """
        Armazena uma resposta no cache.
        """
        normalized_question = self._normalize_question(question)
        question_hash = self._generate_hash(normalized_question)

        entry = {
            'response': response,
            'timestamp': time.time(),
            'compressed': False
        }

        if len(response.encode('utf-8')) > self.compression_threshold:
            entry['response'] = self._compress_response(response).hex() # Armazena como hex string
            entry['compressed'] = True
            logger.debug(f"Resposta comprimida para a pergunta: '{question}'")

        self.cache[question_hash] = entry
        self._save_cache()
        logger.debug(f"Resposta armazenada em cache para a pergunta: '{question}'")

    def cleanup_expired(self):
        """
        Remove entradas expiradas do cache.
        """
        initial_count = len(self.cache)
        keys_to_remove = [
            key for key, entry in self.cache.items()
            if time.time() >= entry['timestamp'] + self.ttl_seconds
        ]
        for key in keys_to_remove:
            self.cache.pop(key, None)
        if len(keys_to_remove) > 0:
            logger.info(f"Limpeza de cache: {len(keys_to_remove)} entradas expiradas removidas.")
            self._save_cache()
        else:
            logger.info("Limpeza de cache: Nenhuma entrada expirada encontrada.")
        logger.info(f"Cache atualizado. Total de entradas: {len(self.cache)} (antes: {initial_count})")

    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de hit/miss do cache."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "current_entries": len(self.cache)
        }

    def reset_stats(self):
        """Reseta as estatísticas de hit/miss."""
        self.hits = 0
        self.misses = 0
        logger.info("Estatísticas de cache resetadas.")

# Exemplo de uso (para testes internos, pode ser removido em produção)
if __name__ == "__main__":
    cache_manager = ResponseCache(cache_file='test_cache.json', ttl_hours=0.0001) # TTL curto para teste

    print("\n--- Teste de Cache HIT/MISS ---")
    question1 = "Qual é a capital da França?"
    response1 = "Paris"

    # MISS inicial
    print(f"Buscando '{question1}'...")
    cached_response = cache_manager.get_cached_response(question1)
    print(f"Cache: {cached_response}")
    assert cached_response is None

    # Cache
    print(f"Armazenando '{question1}' -> '{response1}'...")
    cache_manager.cache_response(question1, response1)

    # HIT
    print(f"Buscando '{question1}' novamente...")
    cached_response = cache_manager.get_cached_response(question1)
    print(f"Cache: {cached_response}")
    assert cached_response == response1

    print("\n--- Teste de Normalização ---")
    question1_similar = "  qual é a Capital da frança? "
    print(f"Buscando '{question1_similar}' (normalizado)...")
    cached_response_similar = cache_manager.get_cached_response(question1_similar)
    print(f"Cache: {cached_response_similar}")
    assert cached_response_similar == response1

    print("\n--- Teste de Expiração ---")
    question2 = "Qual é a cor do céu?"
    response2 = "Azul"
    cache_manager.cache_response(question2, response2)
    print(f"Armazenado '{question2}'. Aguardando expiração...")
    time.sleep(1) # Espera um pouco mais que o TTL curto
    cached_response_expired = cache_manager.get_cached_response(question2)
    print(f"Cache após expiração: {cached_response_expired}")
    assert cached_response_expired is None

    print("\n--- Teste de Compressão ---")
    long_question = "Esta é uma pergunta muito longa que deve ser comprimida para economizar espaço no cache. Ela contém muitos caracteres e palavras para simular uma resposta de IA extensa. Vamos ver se a compressão funciona corretamente e se a descompressão recupera o texto original sem perdas. A qualidade da compressão é importante para otimizar o uso da API gratuita do Google AI Studio, pois respostas longas podem consumir mais recursos." * 50
    long_response = "Esta é uma resposta muito longa que deve ser comprimida para economizar espaço no cache. Ela contém muitos caracteres e palavras para simular uma resposta de IA extensa. Vamos ver se a compressão funciona corretamente e se a descompressão recupera o texto original sem perdas. A qualidade da compressão é importante para otimizar o uso da API gratuita do Google AI Studio, pois respostas longas podem consumir mais recursos." * 100
    
    cache_manager.cache_response(long_question, long_response)
    print(f"Armazenada resposta longa. Tamanho original: {len(long_response)} bytes.")
    
    retrieved_long_response = cache_manager.get_cached_response(long_question)
    print(f"Resposta longa recuperada. Tamanho recuperado: {len(retrieved_long_response)} bytes.")
    assert retrieved_long_response == long_response
    
    print("\n--- Estatísticas de Cache ---")
    stats = cache_manager.get_stats()
    print(f"Estatísticas: {stats}")
    assert stats['hits'] >= 1
    assert stats['misses'] >= 1

    # Limpeza do arquivo de teste
    if os.path.exists('test_cache.json'):
        os.remove('test_cache.json')
    if os.path.exists('test_cache.json.bak'):
        os.remove('test_cache.json.bak')
    print("\nTestes concluídos. Arquivo de cache de teste removido.")
