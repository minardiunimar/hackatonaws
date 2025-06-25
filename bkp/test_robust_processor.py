#!/usr/bin/env python3
"""
Teste do processador robusto de documentos
"""

import os
import sys
from document_processor_robust import RobustDocumentProcessor

def test_with_existing_pdfs():
    """Testa com PDFs existentes no diretório"""
    processor = RobustDocumentProcessor()
    
    # Procura por arquivos PDF no diretório atual
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ Nenhum arquivo PDF encontrado no diretório atual")
        return False
    
    print(f"📁 Encontrados {len(pdf_files)} arquivos PDF:")
    for pdf in pdf_files:
        print(f"   - {pdf}")
    
    # Testa com o primeiro PDF
    test_pdf = pdf_files[0]
    print(f"\n🧪 Testando com: {test_pdf}")
    
    try:
        resultado = processor.process_document(test_pdf, "output_test")
        
        print("\n📋 RESULTADO DO TESTE:")
        print("="*40)
        
        if resultado.get("sucesso", False):
            print("✅ Processamento bem-sucedido!")
            print(f"   - Tipo: {resultado.get('tipo_documento', 'N/A')}")
            print(f"   - Nome: {resultado.get('nome', 'N/A')}")
            print(f"   - CPF: {resultado.get('cpf', 'N/A')}")
            print(f"   - CPF Válido: {resultado.get('cpf_valido', False)}")
            print(f"   - Foto: {resultado.get('foto_extraida', 'N/A')}")
            print(f"   - Caracteres: {resultado.get('texto_extraido_chars', 0)}")
        else:
            print("❌ Processamento falhou!")
            print(f"   - Erro: {resultado.get('erro', 'Erro desconhecido')}")
        
        return resultado.get("sucesso", False)
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def main():
    print("=== TESTE DO PROCESSADOR ROBUSTO ===\n")
    
    # Verifica se o módulo pode ser importado
    try:
        from document_processor_robust import RobustDocumentProcessor
        print("✅ Módulo importado com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        return
    
    # Testa com PDFs existentes
    success = test_with_existing_pdfs()
    
    if success:
        print("\n🎉 Teste concluído com sucesso!")
    else:
        print("\n⚠️  Teste apresentou problemas")

if __name__ == "__main__":
    main()
