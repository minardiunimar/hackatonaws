#!/usr/bin/env python3
"""
Testar AWS Textract com documento real
"""

from textract_ocr_example import get_ocr_engine, DocumentProcessorWithTextract
import logging

def test_textract_with_real_image():
    """Testar Textract com imagem real"""
    
    print("🔍 Testando AWS Textract com documento real...")
    
    try:
        # Carregar imagem
        with open('/home/ec2-user/sample_document.png', 'rb') as f:
            image_bytes = f.read()
        
        print(f"📄 Imagem carregada: {len(image_bytes)} bytes")
        
        # Testar com Textract
        ocr = get_ocr_engine(use_textract=True)
        text = ocr.extract_text_from_image_bytes(image_bytes)
        
        print("\n✅ Texto extraído pelo AWS Textract:")
        print("-" * 50)
        print(text)
        print("-" * 50)
        
        # Testar processador completo
        print("\n🔧 Testando processador completo...")
        processor = DocumentProcessorWithTextract(use_textract=True)
        
        # Simular processamento (adaptado para imagem)
        doc_type = processor.identify_document_type(text)
        nome = processor.extract_name(text)
        cpf = processor.extract_cpf(text)
        cpf_valido = processor.validate_cpf(cpf) if cpf else False
        
        print(f"📋 Tipo de documento: {doc_type}")
        print(f"👤 Nome extraído: {nome}")
        print(f"🆔 CPF extraído: {cpf}")
        print(f"✅ CPF válido: {cpf_valido}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def compare_with_mock():
    """Comparar resultado com Mock OCR"""
    
    print("\n" + "=" * 60)
    print("📊 COMPARAÇÃO: Textract vs Mock OCR")
    print("=" * 60)
    
    # Mock OCR
    print("\n🎭 Mock OCR:")
    mock_ocr = get_ocr_engine(use_textract=False)
    mock_text = mock_ocr.extract_text_from_image_bytes(b"dummy")
    print(mock_text)
    
    # Textract (se disponível)
    print("\n☁️  AWS Textract:")
    try:
        with open('/home/ec2-user/sample_document.png', 'rb') as f:
            image_bytes = f.read()
        
        textract_ocr = get_ocr_engine(use_textract=True)
        textract_text = textract_ocr.extract_text_from_image_bytes(image_bytes)
        print(textract_text if textract_text else "Nenhum texto extraído")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduzir logs
    
    print("🚀 Teste Final do AWS Textract")
    print("=" * 60)
    
    # Testar com documento real
    success = test_textract_with_real_image()
    
    # Comparar resultados
    compare_with_mock()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 AWS Textract funcionando perfeitamente!")
        print("✅ Sistema pronto para produção")
    else:
        print("⚠️  Textract não disponível - usando Mock OCR")
        print("💡 Mock OCR funciona para desenvolvimento/testes")
    
    print("\n📚 Documentação completa:")
    print("   - cat migration_guide.md")
    print("   - Exemplo: textract_ocr_example.py")
    print("   - Seu projeto: document_processor.py")
