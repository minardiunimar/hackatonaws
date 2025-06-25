#!/usr/bin/env python3
"""
Script para comparar os resultados entre o processador original (Tesseract) 
e a nova versão com AWS Textract
"""

import sys
import os
import time
from document_processor import DocumentProcessor  # Versão original
from document_processor_textract import DocumentProcessorTextract  # Nova versão

def compare_processors(pdf_path):
    """
    Compara os resultados dos dois processadores
    """
    print(f"Comparando processadores para: {pdf_path}")
    print("=" * 60)
    
    # Processar com versão original (Tesseract)
    print("Processando com Tesseract...")
    start_time = time.time()
    try:
        processor_old = DocumentProcessor()
        result_old = processor_old.process_document(pdf_path)
        time_old = time.time() - start_time
        success_old = result_old.get('sucesso', False)
    except Exception as e:
        print(f"Erro no processador Tesseract: {e}")
        result_old = {'erro': str(e), 'sucesso': False}
        time_old = time.time() - start_time
        success_old = False
    
    # Processar com Textract
    print("Processando com AWS Textract...")
    start_time = time.time()
    try:
        processor_new = DocumentProcessorTextract()
        result_new = processor_new.process_document(pdf_path)
        time_new = time.time() - start_time
        success_new = result_new.get('sucesso', False)
    except Exception as e:
        print(f"Erro no processador Textract: {e}")
        result_new = {'erro': str(e), 'sucesso': False}
        time_new = time.time() - start_time
        success_new = False
    
    # Comparar resultados
    print("\n" + "=" * 60)
    print("COMPARAÇÃO DE RESULTADOS")
    print("=" * 60)
    
    print(f"{'Campo':<20} {'Tesseract':<25} {'Textract':<25}")
    print("-" * 70)
    
    # Status
    status_old = "✓ Sucesso" if success_old else "✗ Erro"
    status_new = "✓ Sucesso" if success_new else "✗ Erro"
    print(f"{'Status':<20} {status_old:<25} {status_new:<25}")
    
    # Tempo de processamento
    print(f"{'Tempo (s)':<20} {time_old:.2f}s{'':<18} {time_new:.2f}s{'':<18}")
    
    if success_old and success_new:
        # Comparar campos específicos
        fields = ['tipo_documento', 'nome', 'cpf', 'cpf_valido']
        
        for field in fields:
            val_old = result_old.get(field, 'N/A')
            val_new = result_new.get(field, 'N/A')
            
            # Truncar valores longos para exibição
            val_old_str = str(val_old)[:22] + "..." if len(str(val_old)) > 25 else str(val_old)
            val_new_str = str(val_new)[:22] + "..." if len(str(val_new)) > 25 else str(val_new)
            
            print(f"{field.replace('_', ' ').title():<20} {val_old_str:<25} {val_new_str:<25}")
        
        # Mostrar campos únicos do Textract
        if 'rg' in result_new:
            print(f"{'RG':<20} {'N/A':<25} {str(result_new['rg']):<25}")
        
        if 'campos_estruturados' in result_new:
            num_campos = len(result_new['campos_estruturados'])
            print(f"{'Campos Estruturados':<20} {'N/A':<25} {f'{num_campos} campos':<25}")
    
    # Mostrar erros se houver
    if not success_old:
        print(f"\nErro Tesseract: {result_old.get('erro', 'Erro desconhecido')}")
    
    if not success_new:
        print(f"\nErro Textract: {result_new.get('erro', 'Erro desconhecido')}")
    
    print("\n" + "=" * 60)
    print("ANÁLISE")
    print("=" * 60)
    
    if success_new and not success_old:
        print("✓ Textract processou com sucesso onde Tesseract falhou")
    elif success_old and not success_new:
        print("⚠ Tesseract processou com sucesso onde Textract falhou")
    elif success_old and success_new:
        print("✓ Ambos processaram com sucesso")
        
        # Comparar qualidade dos resultados
        if result_old.get('nome') != result_new.get('nome'):
            print("• Nomes extraídos são diferentes")
        
        if result_old.get('cpf') != result_new.get('cpf'):
            print("• CPFs extraídos são diferentes")
        
        if result_new.get('campos_estruturados'):
            print(f"• Textract identificou {len(result_new['campos_estruturados'])} campos estruturados adicionais")
    else:
        print("✗ Ambos falharam no processamento")
    
    # Comparar tempo
    if time_new < time_old:
        print(f"• Textract foi {time_old/time_new:.1f}x mais rápido")
    elif time_old < time_new:
        print(f"• Tesseract foi {time_new/time_old:.1f}x mais rápido")
    else:
        print("• Tempos de processamento similares")

def main():
    if len(sys.argv) != 2:
        print("Uso: python compare_processors.py <caminho_do_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Erro: Arquivo não encontrado: {pdf_path}")
        sys.exit(1)
    
    compare_processors(pdf_path)

if __name__ == "__main__":
    main()
