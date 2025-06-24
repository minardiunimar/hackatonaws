#!/usr/bin/env python3
"""
Teste de validação dos CPFs extraídos
"""

from document_processor import CPFValidator

def test_cpf_candidates():
    """Testa os candidatos a CPF válido"""
    
    candidates = [
        "20026210689",  # Primeiros 11 dígitos
        "26210689876",  # Últimos 11 dígitos  
        "20026210676",  # 200 + 262106 + 76
        "20010689876",  # 200 + 106898 + 76
    ]
    
    print("Testando candidatos a CPF válido:")
    print("-" * 50)
    
    for cpf in candidates:
        is_valid = CPFValidator.validate_cpf(cpf)
        formatted = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
        print(f"{formatted} - {status}")
    
    print("\nTestando CPFs conhecidamente válidos:")
    print("-" * 50)
    
    valid_cpfs = [
        "11144477735",  # CPF válido conhecido
        "12345678909",  # Outro CPF válido
    ]
    
    for cpf in valid_cpfs:
        is_valid = CPFValidator.validate_cpf(cpf)
        formatted = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"
        status = "✅ VÁLIDO" if is_valid else "❌ INVÁLIDO"
        print(f"{formatted} - {status}")

if __name__ == "__main__":
    test_cpf_candidates()
