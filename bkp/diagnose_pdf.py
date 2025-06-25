#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de extração de PDF
"""

import fitz
import cv2
import numpy as np
import pytesseract
import os
import sys

def diagnose_pdf(pdf_path):
    """Diagnóstica problemas com o PDF"""
    print(f"=== DIAGNÓSTICO DO PDF: {pdf_path} ===\n")
    
    # Verifica se arquivo existe
    if not os.path.exists(pdf_path):
        print("❌ ERRO: Arquivo não encontrado!")
        return False
    
    print(f"✅ Arquivo encontrado: {os.path.getsize(pdf_path)} bytes")
    
    try:
        # Abre o PDF
        doc = fitz.open(pdf_path)
        print(f"✅ PDF aberto com sucesso")
        print(f"   - Páginas: {len(doc)}")
        print(f"   - Criptografado: {doc.needs_pass}")
        print(f"   - Metadados: {doc.metadata}")
        
        # Verifica cada página
        total_text = ""
        total_images = 0
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Texto da página
            page_text = page.get_text()
            text_len = len(page_text.strip())
            total_text += page_text
            
            # Imagens da página
            images = page.get_images()
            total_images += len(images)
            
            print(f"   - Página {page_num + 1}: {text_len} chars texto, {len(images)} imagens")
            
            if text_len > 0:
                print(f"     Amostra do texto: {repr(page_text[:100])}")
        
        print(f"\n📊 RESUMO:")
        print(f"   - Total de texto: {len(total_text)} caracteres")
        print(f"   - Total de imagens: {total_images}")
        
        # Se não tem texto, tenta OCR
        if len(total_text.strip()) < 10:
            print(f"\n🔍 POUCO TEXTO ENCONTRADO - Testando OCR...")
            test_ocr(doc)
        
        doc.close()
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao abrir PDF: {e}")
        return False

def test_ocr(doc):
    """Testa OCR na primeira página"""
    try:
        page = doc.load_page(0)
        
        # Converte para imagem
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # Salva imagem temporária para debug
        with open("debug_page.png", "wb") as f:
            f.write(img_data)
        print("   - Imagem da página salva como debug_page.png")
        
        # Converte para OpenCV
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is not None:
            print(f"   - Imagem convertida: {img.shape}")
            
            # Testa OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ocr_text = pytesseract.image_to_string(gray, lang='por')
            
            print(f"   - OCR extraiu: {len(ocr_text)} caracteres")
            if ocr_text.strip():
                print(f"   - Amostra OCR: {repr(ocr_text[:100])}")
            else:
                print("   - OCR não encontrou texto")
        else:
            print("   - Erro ao converter imagem")
            
        pix = None
        
    except Exception as e:
        print(f"   - Erro no teste OCR: {e}")

def test_dependencies():
    """Testa dependências"""
    print("=== TESTE DE DEPENDÊNCIAS ===\n")
    
    try:
        import fitz
        print(f"✅ PyMuPDF: {fitz.version}")
    except ImportError as e:
        print(f"❌ PyMuPDF: {e}")
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract: {version}")
    except Exception as e:
        print(f"❌ Tesseract: {e}")
    
    try:
        from PIL import Image
        print(f"✅ Pillow: {Image.__version__}")
    except ImportError as e:
        print(f"❌ Pillow: {e}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python diagnose_pdf.py <caminho_do_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    test_dependencies()
    print()
    diagnose_pdf(pdf_path)

if __name__ == "__main__":
    main()
