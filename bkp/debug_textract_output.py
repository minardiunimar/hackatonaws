#!/usr/bin/env python3
"""
Script para debugar a saída do Textract e entender o formato do texto
"""

from document_processor_textract import DocumentProcessorTextract
import sys

def debug_textract_output(pdf_path):
    """Debug da saída do Textract"""
    
    processor = DocumentProcessorTextract()
    
    # Converte PDF para imagens
    page_images = processor.pdf_to_images(pdf_path)
    if not page_images:
        print("Erro: Não foi possível converter PDF")
        return
    
    # Extrai texto com Textract
    textract_result = processor.textract_ocr.extract_text_from_bytes(page_images[0])
    
    print("=== TEXTO COMPLETO EXTRAÍDO ===")
    print(repr(textract_result['text']))
    print("\n=== TEXTO FORMATADO ===")
    print(textract_result['text'])
    
    print("\n=== LINHAS INDIVIDUAIS ===")
    for i, line in enumerate(textract_result['lines'], 1):
        print(f"Linha {i}: '{line}'")
    
    print("\n=== PALAVRAS INDIVIDUAIS ===")
    for i, word in enumerate(textract_result['words'], 1):
        print(f"Palavra {i}: '{word['text']}' (confiança: {word['confidence']:.1f}%)")
    
    # Testa padrões de CPF no texto
    print("\n=== TESTE DE PADRÕES CPF ===")
    import re
    
    text = textract_result['text']
    
    cpf_patterns = [
        r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'cpf\s+(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'cpf\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'cpf\s*\n\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
        r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',  # Qualquer número no formato CPF
    ]
    
    for i, pattern in enumerate(cpf_patterns, 1):
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        print(f"Padrão {i} ('{pattern}'): {matches}")
    
    # Analisa formulários estruturados
    print("\n=== FORMULÁRIOS ESTRUTURADOS ===")
    forms_result = processor.textract_ocr.analyze_document_forms(page_images[0])
    
    if forms_result['key_value_pairs']:
        for key, value in forms_result['key_value_pairs'].items():
            print(f"'{key}' -> '{value}'")
    else:
        print("Nenhum campo estruturado encontrado")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 debug_textract_output.py <arquivo.pdf>")
        sys.exit(1)
    
    debug_textract_output(sys.argv[1])
