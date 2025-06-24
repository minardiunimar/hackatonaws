#!/usr/bin/env python3
"""
Análise detalhada do formato CPF 200~262106898/76
"""

def analyze_cpf_format():
    cpf_text = "200~262106898/76"
    
    print(f"CPF original: {cpf_text}")
    print(f"Comprimento total: {len(cpf_text)}")
    
    # Separar por partes
    parts = cpf_text.replace('~', '|').replace('/', '|').split('|')
    print(f"Partes separadas: {parts}")
    
    # Contar dígitos em cada parte
    for i, part in enumerate(parts):
        print(f"Parte {i+1}: '{part}' - {len(part)} caracteres")
    
    # Extrair apenas números
    only_numbers = ''.join(filter(str.isdigit, cpf_text))
    print(f"Apenas números: {only_numbers}")
    print(f"Total de dígitos: {len(only_numbers)}")
    
    # Possíveis interpretações para CPF de 11 dígitos:
    print("\nPossíveis interpretações:")
    
    # Interpretação 1: Primeiros 11 dígitos
    if len(only_numbers) >= 11:
        cpf1 = only_numbers[:11]
        print(f"1. Primeiros 11 dígitos: {cpf1}")
        print(f"   Formatado: {cpf1[:3]}.{cpf1[3:6]}.{cpf1[6:9]}-{cpf1[9:11]}")
    
    # Interpretação 2: Últimos 11 dígitos
    if len(only_numbers) >= 11:
        cpf2 = only_numbers[-11:]
        print(f"2. Últimos 11 dígitos: {cpf2}")
        print(f"   Formatado: {cpf2[:3]}.{cpf2[3:6]}.{cpf2[6:9]}-{cpf2[9:11]}")
    
    # Interpretação 3: Baseado na estrutura 200~262106898/76
    # Talvez seja: 200 + 262106898 (primeiros 6) + 76 = 200262106876?
    if len(parts) == 3:
        part1 = parts[0]  # 200
        part2 = parts[1]  # 262106898
        part3 = parts[2]  # 76
        
        # Tentar diferentes combinações
        cpf3 = part1 + part2[:6] + part3  # 200 + 262106 + 76 = 20026210676
        print(f"3. Combinação 1: {cpf3}")
        if len(cpf3) == 11:
            print(f"   Formatado: {cpf3[:3]}.{cpf3[3:6]}.{cpf3[6:9]}-{cpf3[9:11]}")
        
        cpf4 = part1 + part2[-6:] + part3  # 200 + 106898 + 76 = 20010689876
        print(f"4. Combinação 2: {cpf4}")
        if len(cpf4) == 11:
            print(f"   Formatado: {cpf4[:3]}.{cpf4[3:6]}.{cpf4[6:9]}-{cpf4[9:11]}")

if __name__ == "__main__":
    analyze_cpf_format()
