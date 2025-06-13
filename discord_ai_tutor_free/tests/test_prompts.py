import pytest
from unittest.mock import MagicMock, patch
from discord_ai_tutor_free.utils.prompt_builder import PromptBuilder

@pytest.fixture
def prompt_builder():
    return PromptBuilder()

def test_scaff_prompt_generation(prompt_builder):
    """
    Testa a geração de prompts S.C.A.F.F.
    """
    question = "Qual é a capital da França?"
    context = "A França é um país europeu."
    history = [
        {"role": "user", "content": "Olá"},
        {"role": "assistant", "content": "Olá! Como posso ajudar?"}
    ]
    
    expected_prompt_part = "S.C.A.F.F. Framework:\n" \
                           "1. **S**tep-by-step: Think step-by-step.\n" \
                           "2. **C**ontext: Use the provided context.\n" \
                           "3. **A**ction: Formulate a concise answer.\n" \
                           "4. **F**ormat: Ensure the response is well-structured.\n" \
                           "5. **F**act-check: Verify accuracy.\n\n" \
                           "Context: A França é um país europeu.\n" \
                           "History:\n" \
                           "User: Olá\n" \
                           "Assistant: Olá! Como posso ajudar?\n" \
                           "Question: Qual é a capital da França?"

    prompt = prompt_builder.build_scaff_prompt(question, context, history)
    
    assert expected_prompt_part in prompt
    assert "S.C.A.F.F. Framework" in prompt
    assert "Context: A França é um país europeu." in prompt
    assert "Question: Qual é a capital da França?" in prompt
    assert "User: Olá" in prompt
    assert "Assistant: Olá! Como posso ajudar?" in prompt

def test_scaff_prompt_no_context(prompt_builder):
    """
    Testa a geração de prompts S.C.A.F.F. sem contexto.
    """
    question = "Qual é a capital da França?"
    history = []
    
    prompt = prompt_builder.build_scaff_prompt(question, None, history)
    
    assert "Context:" not in prompt
    assert "Question: Qual é a capital da França?" in prompt

def test_scaff_prompt_no_history(prompt_builder):
    """
    Testa a geração de prompts S.C.A.F.F. sem histórico.
    """
    question = "Qual é a capital da França?"
    context = "A França é um país europeu."
    
    prompt = prompt_builder.build_scaff_prompt(question, context, None)
    
    assert "History:" not in prompt
    assert "Context: A França é um país europeu." in prompt
    assert "Question: Qual é a capital da França?" in prompt

def test_scaff_prompt_empty_history(prompt_builder):
    """
    Testa a geração de prompts S.C.A.F.F. com histórico vazio.
    """
    question = "Qual é a capital da França?"
    context = "A França é um país europeu."
    history = []
    
    prompt = prompt_builder.build_scaff_prompt(question, context, history)
    
    assert "History:" not in prompt
    assert "Context: A França é um país europeu." in prompt
    assert "Question: Qual é a capital da França?" in prompt
