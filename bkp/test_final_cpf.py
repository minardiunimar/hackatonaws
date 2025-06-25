#!/usr/bin/env python3
"""
Teste final da extração e validação de CPF
"""

import re
from document_processor import CPFValidator

def test_complete_cpf_extraction():
    """Testa o processo completo de extração de CPF"""
    
    # Padrões de CPF atualizados
    cpf_patterns = [
        r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'c\.p\.f\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'(\d{3}~\d{9}/\d{2})',
        r'(\d{3}[~\-\.]\d{3}[\.\-]?\d{3}[\.\-/]\d{2})',
        r'(\d{3}[^\d\s]\d{6}[^\d\s]\d{2})',
    ]
    
    # Texto de teste
    test_text = "Documento contém CPF: 200~262106898/76"
    
    print("Teste completo de extração de CPF:")
    print(f"Texto: {test_text}")
    print("-" * 60)
    
    # Simula o processo do DocumentProcessor
    for i, pattern in enumerate(cpf_patterns):
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            # Extrai o CPF encontrado
            cpf_raw = match.group(1) if len(match.groups()) > 0 else match.group(0)
            print(f"✓ Padrão {i+1} encontrou: {cpf_raw}")
            
            # Limpa o CPF
            cpf_clean = CPFValidator.clean_cpf(cpf_raw)
            print(f"  CPF limpo: {cpf_clean}")
            
            # Formata para exibição
            if len(cpf_clean) == 11:
                cpf_formatted = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:11]}"
                print(f"  CPF formatado: {cpf_formatted}")
                
                # Valida
                is_valid = CPFValidator.validate_cpf(cpf_raw)
                print(f"  CPF válido: {'✅ SIM' if is_valid else '❌ NÃO'}")
                
                if is_valid:
                    print(f"\n🎉 SUCESSO! CPF válido encontrado: {cpf_formatted}")
                    break
            else:
                print(f"  ❌ CPF inválido: {len(cpf_clean)} dígitos")
            print()

def test_edge_cases():
    """Testa casos extremos"""
    
    test_cases = [
        "200~262106898/76",
        "111.444.777-35", 
        "CPF: 200~262106898/76",
        "C.P.F: 111.444.777-35",
        "262106898/76",
    ]
    
    print("\nTeste de casos extremos:")
    print("-" * 60)
    
    for test_case in test_cases:
        print(f"Teste: '{test_case}'")
        
        # Tenta extrair com padrão específico
        match = re.search(r'(\d{3}~\d{9}/\d{2})', test_case)
        if match:
            cpf_raw = match.group(1)
            cpf_clean = CPFValidator.clean_cpf(cpf_raw)
            is_valid = CPFValidator.validate_cpf(cpf_raw)
            
            print(f"  Extraído: {cpf_raw}")
            print(f"  Limpo: {cpf_clean}")
            print(f"  Válido: {'✅' if is_valid else '❌'}")
        else:
            print("  ❌ Não encontrado com padrão específico")
        print()

if __name__ == "__main__":
    test_complete_cpf_extraction()
    test_edge_cases()
