#!/usr/bin/env python3
"""
Script para testar a correção da identificação incorreta de NIS/PIS/PASEP como CPF
"""

import re
from document_processor_textract import CPFValidator, DocumentProcessorTextract

def test_cpf_extraction():
    """Testa a extração de CPF com diferentes cenários"""
    
    processor = DocumentProcessorTextract()
    
    # Cenários de teste
    test_cases = [
        {
            "name": "Documento com CPF e NIS separados",
            "text": """
            REPÚBLICA FEDERATIVA DO BRASIL
            REGISTRO GERAL
            Nome: JOÃO DA SILVA SANTOS
            CPF: 111.444.777-35
            NIS/PIS/PASEP: 12345678901
            RG: 12.345.678-9
            """,
            "expected_cpf": "111.444.777-35",
            "should_find_cpf": True
        },
        {
            "name": "Documento só com NIS (sem CPF)",
            "text": """
            CARTEIRA DE IDENTIDADE
            Nome: MARIA OLIVEIRA
            NIS: 98765432109
            RG: 98.765.432-1
            """,
            "expected_cpf": None,
            "should_find_cpf": False
        },
        {
            "name": "Documento com número válido de CPF sem contexto",
            "text": """
            DOCUMENTO DE IDENTIFICAÇÃO
            Nome: PEDRO SANTOS
            Número: 111.444.777-35
            Data: 01/01/2020
            """,
            "expected_cpf": "111.444.777-35",
            "should_find_cpf": True
        },
        {
            "name": "Documento com PIS próximo a CPF",
            "text": """
            CARTEIRA NACIONAL DE HABILITAÇÃO
            Nome: ANA COSTA
            CPF: 111.444.777-35
            PIS: 12345678901
            Categoria: B
            """,
            "expected_cpf": "111.444.777-35",
            "should_find_cpf": True
        }
    ]
    
    print("="*60)
    print("TESTE DE EXTRAÇÃO DE CPF vs NIS/PIS/PASEP")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTeste {i}: {test_case['name']}")
        print("-" * 40)
        
        # Extrai informações
        info = processor.extract_information_from_text(test_case['text'])
        
        cpf_found = info.get('cpf', '')
        cpf_valid = CPFValidator.validate_cpf(cpf_found) if cpf_found else False
        
        print(f"Texto de entrada:")
        print(test_case['text'].strip())
        print(f"\nCPF extraído: {cpf_found or 'Nenhum'}")
        print(f"CPF válido: {cpf_valid}")
        print(f"Nome extraído: {info.get('nome', 'Nenhum')}")
        
        # Verifica resultado
        if test_case['should_find_cpf']:
            if cpf_found == test_case['expected_cpf']:
                print("✅ PASSOU - CPF correto extraído")
            else:
                print(f"❌ FALHOU - Esperado: {test_case['expected_cpf']}, Obtido: {cpf_found}")
        else:
            if not cpf_found:
                print("✅ PASSOU - Nenhum CPF extraído (correto)")
            else:
                print(f"❌ FALHOU - CPF extraído quando não deveria: {cpf_found}")

def test_cpf_validator():
    """Testa o validador de CPF"""
    print("\n" + "="*60)
    print("TESTE DO VALIDADOR DE CPF")
    print("="*60)
    
    test_cpfs = [
        ("111.444.777-35", True, "CPF válido"),
        ("111.111.111-11", False, "CPF com dígitos iguais"),
        ("123.456.789-00", False, "CPF inválido"),
        ("12345678901", False, "Número de 11 dígitos inválido"),
        ("000.000.000-00", False, "CPF zerado"),
    ]
    
    for cpf, expected, description in test_cpfs:
        result = CPFValidator.validate_cpf(cpf)
        status = "✅ PASSOU" if result == expected else "❌ FALHOU"
        print(f"{status} - {description}: {cpf} -> {result}")

if __name__ == "__main__":
    test_cpf_validator()
    test_cpf_extraction()
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO")
    print("="*60)
