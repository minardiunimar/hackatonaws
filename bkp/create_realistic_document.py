#!/usr/bin/env python3
"""
Cria um documento PDF mais realista para testar o processador Textract
"""

import fitz  # PyMuPDF
import os

def create_realistic_rg():
    """Cria um RG mais realista"""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    
    # Cabeçalho
    page.insert_text((50, 50), "REPÚBLICA FEDERATIVA DO BRASIL", fontsize=14, color=(0, 0, 1))
    page.insert_text((50, 80), "ESTADO DE SÃO PAULO", fontsize=12, color=(0, 0, 1))
    page.insert_text((50, 100), "SECRETARIA DE SEGURANÇA PÚBLICA", fontsize=10)
    
    # Título principal
    page.insert_text((200, 150), "CARTEIRA DE IDENTIDADE", fontsize=16, color=(1, 0, 0))
    page.insert_text((220, 170), "REGISTRO GERAL", fontsize=14, color=(1, 0, 0))
    
    # Informações pessoais
    y_pos = 220
    line_height = 25
    
    fields = [
        ("Nome:", "MARIA SILVA SANTOS"),
        ("Filiação:", "JOÃO SANTOS E ANA SILVA"),
        ("Data de Nascimento:", "15/03/1985"),
        ("Naturalidade:", "SÃO PAULO - SP"),
        ("CPF:", "111.444.777-35"),
        ("RG:", "12.345.678-9"),
        ("Data de Expedição:", "10/01/2020"),
        ("Órgão Expedidor:", "SSP/SP")
    ]
    
    for label, value in fields:
        page.insert_text((50, y_pos), label, fontsize=10, color=(0, 0, 0))
        page.insert_text((150, y_pos), value, fontsize=10, color=(0, 0, 0))
        y_pos += line_height
    
    # Adicionar uma "foto" simulada (retângulo)
    rect = fitz.Rect(400, 200, 500, 300)
    page.draw_rect(rect, color=(0, 0, 0), width=2)
    page.insert_text((420, 250), "FOTO", fontsize=12)
    
    # Rodapé
    page.insert_text((50, 700), "Este documento é válido em todo território nacional", fontsize=8)
    page.insert_text((50, 720), "Documento de Identidade nº 12.345.678-9", fontsize=8)
    
    filename = "rg_realista.pdf"
    doc.save(filename)
    doc.close()
    return filename

def create_realistic_cnh():
    """Cria uma CNH mais realista"""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    # Cabeçalho
    page.insert_text((50, 50), "REPÚBLICA FEDERATIVA DO BRASIL", fontsize=12, color=(0, 0, 1))
    page.insert_text((50, 70), "CARTEIRA NACIONAL DE HABILITAÇÃO", fontsize=14, color=(1, 0, 0))
    
    # Informações
    y_pos = 120
    line_height = 20
    
    fields = [
        ("Nome:", "PEDRO COSTA OLIVEIRA"),
        ("Data de Nascimento:", "22/07/1990"),
        ("CPF:", "987.654.321-00"),
        ("RG:", "98.765.432-1"),
        ("Categoria:", "B"),
        ("Registro:", "123456789"),
        ("Data de Expedição:", "15/06/2023"),
        ("Validade:", "15/06/2028"),
        ("Local:", "SÃO PAULO - SP")
    ]
    
    for label, value in fields:
        page.insert_text((50, y_pos), label, fontsize=9)
        page.insert_text((150, y_pos), value, fontsize=9, color=(0, 0, 1))
        y_pos += line_height
    
    # Foto simulada
    rect = fitz.Rect(400, 120, 500, 220)
    page.draw_rect(rect, color=(0, 0, 0), width=2)
    page.insert_text((420, 170), "FOTO", fontsize=10)
    
    # Observações
    page.insert_text((50, 400), "OBSERVAÇÕES:", fontsize=10, color=(1, 0, 0))
    page.insert_text((50, 420), "Primeira habilitação", fontsize=9)
    page.insert_text((50, 440), "Categoria B - Veículos de até 3.500kg", fontsize=9)
    
    filename = "cnh_realista.pdf"
    doc.save(filename)
    doc.close()
    return filename

def main():
    print("Criando documentos realistas para teste...")
    
    # Criar RG
    rg_file = create_realistic_rg()
    print(f"✓ RG criado: {rg_file}")
    
    # Criar CNH
    cnh_file = create_realistic_cnh()
    print(f"✓ CNH criada: {cnh_file}")
    
    print("\nDocumentos criados com sucesso!")
    print("Para testar:")
    print(f"  ./document_processor_textract.py {rg_file}")
    print(f"  ./document_processor_textract.py {cnh_file}")

if __name__ == "__main__":
    main()
