#!/usr/bin/env python3
"""
Teste do AWS Textract com um exemplo real
"""

import boto3
import logging
from textract_ocr_example import DocumentProcessorWithTextract, get_ocr_engine

def test_textract_connection():
    """Testar conexão com AWS Textract"""
    try:
        print("🔍 Testando conexão com AWS Textract...")
        
        # Criar cliente Textract
        textract = boto3.client('textract', region_name='us-east-1')
        
        # Testar com uma imagem simples (1x1 pixel PNG)
        # Isso é só para verificar se a API está acessível
        simple_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        response = textract.detect_document_text(
            Document={'Bytes': simple_png}
        )
        
        print("✅ Conexão com Textract estabelecida com sucesso!")
        print(f"   Request ID: {response['ResponseMetadata']['RequestId']}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com Textract: {e}")
        return False

def test_ocr_engines():
    """Testar ambos os engines de OCR"""
    print("\n=== Testando Engines de OCR ===")
    
    # Teste Mock OCR
    print("\n1. 🎭 Testando Mock OCR:")
    mock_ocr = get_ocr_engine(use_textract=False)
    mock_text = mock_ocr.extract_text_from_image_bytes(b"dummy")
    print("   Texto extraído (mock):")
    for line in mock_text.split('\n')[:3]:
        print(f"   📄 {line}")
    
    # Teste Textract OCR
    print("\n2. ☁️  Testando Textract OCR:")
    try:
        textract_ocr = get_ocr_engine(use_textract=True)
        print("   ✅ Engine Textract inicializado com sucesso")
        
        # Testar com imagem simples
        simple_text = textract_ocr.extract_text_from_image_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        print(f"   📄 Resposta Textract: '{simple_text}' (esperado vazio para imagem 1x1)")
        
    except Exception as e:
        print(f"   ❌ Erro no Textract: {e}")

def show_integration_example():
    """Mostrar exemplo de integração"""
    print("\n=== Exemplo de Integração ===")
    print("""
Para integrar no seu processador de documentos existente:

1. 📝 Substitua a importação:
   # Antes:
   import pytesseract
   
   # Depois:
   from textract_ocr_example import get_ocr_engine

2. 🔧 Modifique a inicialização:
   # Antes:
   def __init__(self):
       pass
   
   # Depois:
   def __init__(self):
       self.ocr = get_ocr_engine(use_textract=True)

3. 🔄 Atualize as chamadas:
   # Antes:
   text = pytesseract.image_to_string(image)
   
   # Depois:
   text = self.ocr.extract_text_from_image_bytes(image_bytes)

4. 📊 Processe documentos:
   processor = DocumentProcessorWithTextract(use_textract=True)
   resultado = processor.process_document('documento.pdf')
""")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Teste Completo do AWS Textract")
    print("=" * 50)
    
    # Testar conexão
    connection_ok = test_textract_connection()
    
    # Testar engines
    test_ocr_engines()
    
    # Mostrar exemplo de integração
    show_integration_example()
    
    print("\n" + "=" * 50)
    if connection_ok:
        print("🎉 Sistema pronto para usar AWS Textract!")
        print("💡 Próximo passo: Integre no seu processador de documentos")
    else:
        print("⚠️  Use Mock OCR para desenvolvimento/testes")
        print("🔧 Configure permissões AWS para usar Textract em produção")
    
    print("\n📚 Leia o guia completo: cat migration_guide.md")
