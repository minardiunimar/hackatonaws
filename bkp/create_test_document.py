#!/usr/bin/env python3
"""
Cria um documento de teste com o formato de CPF específico
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_test_document():
    """Cria um PDF de teste com o CPF no formato problemático"""
    
    filename = "documento_teste_cpf.pdf"
    
    # Cria o PDF
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "REGISTRO GERAL")
    
    # Informações do documento
    c.setFont("Helvetica", 12)
    y_pos = height - 150
    
    # Nome
    c.drawString(100, y_pos, "Nome: JOÃO DA SILVA SANTOS")
    y_pos -= 30
    
    # CPF no formato problemático
    c.drawString(100, y_pos, "CPF: 200~262106898/76")
    y_pos -= 30
    
    # Outras informações
    c.drawString(100, y_pos, "RG: 12.345.678-9")
    y_pos -= 30
    
    c.drawString(100, y_pos, "Data de Nascimento: 01/01/1990")
    y_pos -= 30
    
    c.drawString(100, y_pos, "Órgão Expedidor: SSP/SP")
    
    # Finaliza o PDF
    c.save()
    
    print(f"Documento de teste criado: {filename}")
    return filename

if __name__ == "__main__":
    create_test_document()
