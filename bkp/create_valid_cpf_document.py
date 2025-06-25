#!/usr/bin/env python3
"""
Cria um documento PDF de teste com CPF válido
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

def create_test_document():
    """Cria documento de teste com CPF válido"""
    
    filename = "documento_cpf_valido.pdf"
    
    # Criar PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "REGISTRO GERAL")
    
    # Informações
    c.setFont("Helvetica", 12)
    y_pos = height - 150
    
    # Nome
    c.drawString(100, y_pos, "Nome: JOÃO DA SILVA SANTOS")
    y_pos -= 30
    
    # CPF válido (111.444.777-35)
    c.drawString(100, y_pos, "CPF 111.444.777-35")
    y_pos -= 30
    
    # RG
    c.drawString(100, y_pos, "RG: 12.345.678-9")
    y_pos -= 30
    
    # Data de nascimento
    c.drawString(100, y_pos, "Data de Nascimento: 01/01/1990")
    y_pos -= 30
    
    # Órgão expedidor
    c.drawString(100, y_pos, "Órgão Expedidor: SSP/SP")
    
    c.save()
    print(f"Documento criado: {filename}")
    
    return filename

def create_test_document_with_colon():
    """Cria documento de teste com CPF válido usando dois pontos"""
    
    filename = "documento_cpf_valido_colon.pdf"
    
    # Criar PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "CARTEIRA DE IDENTIDADE")
    
    # Informações
    c.setFont("Helvetica", 12)
    y_pos = height - 150
    
    # Nome
    c.drawString(100, y_pos, "Nome: MARIA SILVA SANTOS")
    y_pos -= 30
    
    # CPF válido com dois pontos
    c.drawString(100, y_pos, "CPF: 111.444.777-35")
    y_pos -= 30
    
    # RG
    c.drawString(100, y_pos, "RG: 98.765.432-1")
    y_pos -= 30
    
    # Data de nascimento
    c.drawString(100, y_pos, "Data de Nascimento: 15/05/1985")
    y_pos -= 30
    
    # Órgão expedidor
    c.drawString(100, y_pos, "Órgão Expedidor: SSP/RJ")
    
    c.save()
    print(f"Documento criado: {filename}")
    
    return filename

if __name__ == "__main__":
    # Instalar reportlab se necessário
    try:
        from reportlab.pdfgen import canvas
    except ImportError:
        print("Instalando reportlab...")
        os.system("pip3 install reportlab")
        from reportlab.pdfgen import canvas
    
    doc1 = create_test_document()
    doc2 = create_test_document_with_colon()
    
    print(f"\nDocumentos criados:")
    print(f"1. {doc1} - CPF sem dois pontos")
    print(f"2. {doc2} - CPF com dois pontos")
