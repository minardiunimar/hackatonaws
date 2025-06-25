#!/usr/bin/env python3
"""
Script para criar um documento PDF de teste
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_test_document():
    """Cria um documento PDF de teste simulando um RG"""
    
    filename = "documento_teste_rg.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "REPÚBLICA FEDERATIVA DO BRASIL")
    c.drawString(50, height - 70, "REGISTRO GERAL")
    
    # Informações do documento
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, "Nome: JOÃO DA SILVA SANTOS")
    c.drawString(50, height - 140, "CPF: 123.456.789-09")
    c.drawString(50, height - 160, "RG: 12.345.678-9")
    c.drawString(50, height - 180, "Data de Nascimento: 15/03/1985")
    c.drawString(50, height - 200, "Naturalidade: São Paulo - SP")
    
    # Adicionar mais texto para simular um documento real
    c.drawString(50, height - 240, "Filiação:")
    c.drawString(70, height - 260, "Pai: JOSÉ SANTOS")
    c.drawString(70, height - 280, "Mãe: MARIA DA SILVA")
    
    c.drawString(50, height - 320, "Documento de Identidade")
    c.drawString(50, height - 340, "Carteira de Identidade")
    
    # Simular assinatura
    c.drawString(50, height - 400, "________________________________")
    c.drawString(50, height - 420, "Diretor do Instituto de Identificação")
    
    c.save()
    print(f"Documento de teste criado: {filename}")
    return filename

if __name__ == "__main__":
    create_test_document()
