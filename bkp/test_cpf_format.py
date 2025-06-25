#!/usr/bin/env python3
"""
Teste específico para o formato de CPF 200~262106898/76
"""

import re
from document_processor import CPFValidator

def test_cpf_patterns():
    """Testa os padrões de CPF"""
    
    # Padrões de CPF do processador
    cpf_patterns = [
        r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'c\.p\.f\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        # Formato com ~ e / (ex: 200~262106898/76)
        r'(\d{3}~\d{9}/\d{2})',
        # Formato mais flexível para capturar variações
        r'(\d{3}[~\-\.]\d{3}[\.\-]?\d{3}[\.\-/]\d{2})',
        # Padrão genérico para 11 dígitos com separadores variados
        r'(\d{3}[^\d\s]\d{6}[^\d\s]\d{2})',
    ]
    
    # Texto de teste com o CPF problemático
    test_text = "200~262106898/76"
    
    print("Testando padrões de CPF:")
    print(f"Texto de teste: {test_text}")
    print("-" * 50)
    
    found_match = False
    for i, pattern in enumerate(cpf_patterns):
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            found_match = True
            cpf_found = match.group(1) if len(match.groups()) > 0 else match.group(0)
            print(f"✓ Padrão {i+1}: {pattern}")
            print(f"  CPF encontrado: {cpf_found}")
            
            # Testa limpeza e validação
            cpf_clean = CPFValidator.clean_cpf(cpf_found)
            print(f"  CPF limpo: {cpf_clean}")
            
            if len(cpf_clean) == 11:
                is_valid = CPFValidator.validate_cpf(cpf_found)
                print(f"  CPF válido: {is_valid}")
            else:
                print(f"  CPF inválido: tamanho incorreto ({len(cpf_clean)} dígitos)")
            print()
        else:
            print(f"✗ Padrão {i+1}: {pattern} - Não encontrou")
    
    if not found_match:
        print("❌ Nenhum padrão encontrou o CPF!")
    else:
        print("✅ Pelo menos um padrão funcionou!")

def test_cpf_cleaning():
    """Testa especificamente a limpeza do CPF"""
    test_cpfs = [
        "200~262106898/76",
        "111.444.777-35",
        "11144477735",
        "111-444-777/35"
    ]
    
    print("\nTestando limpeza de CPFs:")
    print("-" * 50)
    
    for cpf in test_cpfs:
        cleaned = CPFValidator.clean_cpf(cpf)
        is_valid = CPFValidator.validate_cpf(cpf)
        print(f"Original: {cpf}")
        print(f"Limpo: {cleaned} ({len(cleaned)} dígitos)")
        print(f"Válido: {is_valid}")
        print()

if __name__ == "__main__":
    test_cpf_patterns()
    test_cpf_cleaning()
