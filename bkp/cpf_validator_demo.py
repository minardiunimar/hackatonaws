#!/usr/bin/env python3
"""
Demonstração do validador de CPF
Este script funciona sem dependências externas
"""

import re

class CPFValidator:
    """Classe para validação de CPF"""
    
    @staticmethod
    def clean_cpf(cpf: str) -> str:
        """Remove caracteres não numéricos do CPF"""
        return re.sub(r'[^0-9]', '', cpf)
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida CPF usando o algoritmo oficial
        Returns: True se válido, False caso contrário
        """
        cpf = CPFValidator.clean_cpf(cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcula segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        # Verifica se os dígitos calculados conferem
        return cpf[9] == str(digit1) and cpf[10] == str(digit2)

def main():
    print("=== DEMONSTRAÇÃO DO VALIDADOR DE CPF ===\n")
    
    # CPFs para teste
    cpfs_teste = [
        ("111.444.777-35", "Válido"),
        ("123.456.789-09", "Válido"),
        ("111.111.111-11", "Inválido - todos dígitos iguais"),
        ("123.456.789-10", "Inválido - dígito verificador errado"),
        ("12345678901", "Inválido - sem formatação"),
        ("000.000.000-00", "Inválido - zeros"),
    ]
    
    print("Testando CPFs:")
    print("-" * 60)
    
    for cpf, descricao in cpfs_teste:
        resultado = CPFValidator.validate_cpf(cpf)
        status = "✓ VÁLIDO" if resultado else "✗ INVÁLIDO"
        print(f"{cpf:<20} | {status:<12} | {descricao}")
    
    print("\n" + "=" * 60)
    print("TESTE INTERATIVO")
    print("=" * 60)
    
    while True:
        try:
            cpf_input = input("\nDigite um CPF para validar (ou 'sair' para terminar): ")
            
            if cpf_input.lower() in ['sair', 'exit', 'quit']:
                break
            
            if not cpf_input.strip():
                continue
            
            resultado = CPFValidator.validate_cpf(cpf_input)
            
            if resultado:
                print(f"✓ CPF {cpf_input} é VÁLIDO")
            else:
                print(f"✗ CPF {cpf_input} é INVÁLIDO")
                
        except KeyboardInterrupt:
            print("\n\nSaindo...")
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    main()
