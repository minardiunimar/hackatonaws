#!/usr/bin/env python3
"""
Script para debugar e analisar todas as imagens extraídas de um PDF
"""

import fitz  # PyMuPDF
import cv2
import numpy as np
import os
import sys
from photo_detector_improved import ImprovedPhotoDetector

def extract_and_analyze_all_images(pdf_path: str):
    """Extrai e analisa todas as imagens do PDF"""
    print(f"Analisando todas as imagens de: {pdf_path}")
    
    detector = ImprovedPhotoDetector()
    
    try:
        doc = fitz.open(pdf_path)
        all_images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            print(f"\nPágina {page_num + 1}: {len(image_list)} imagens encontradas")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    img_array = np.frombuffer(img_data, dtype=np.uint8)
                    img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if img_cv is not None:
                        all_images.append(img_cv)
                        
                        # Salva a imagem para análise
                        filename = f"debug_img_p{page_num+1}_i{img_index}.jpg"
                        cv2.imwrite(filename, img_cv)
                        
                        # Analisa a imagem
                        metrics = detector.analyze_image_quality(img_cv)
                        is_signature = detector.is_signature_like(img_cv)
                        is_photo = detector.is_photo_like(img_cv)
                        
                        print(f"  Imagem {img_index}:")
                        print(f"    Arquivo: {filename}")
                        print(f"    Tamanho: {img_cv.shape[1]}x{img_cv.shape[0]}")
                        print(f"    É assinatura: {is_signature}")
                        print(f"    É foto: {is_photo}")
                        print(f"    Tem face: {metrics.get('has_face', False)}")
                        print(f"    Tem olhos: {metrics.get('has_eyes', False)}")
                        print(f"    Densidade: {metrics.get('density', 0):.3f}")
                        print(f"    Entropia: {metrics.get('entropy', 0):.2f}")
                        print(f"    Proporção: {metrics.get('aspect_ratio', 0):.2f}")
                
                pix = None
        
        doc.close()
        
        # Tenta detectar a melhor foto
        print(f"\n{'='*50}")
        print("ANÁLISE FINAL")
        print(f"{'='*50}")
        
        result = detector.detect_best_photo(all_images)
        if result:
            best_photo, best_metrics = result
            print("Melhor foto encontrada!")
            print(f"Métricas: {best_metrics}")
            
            # Salva a melhor foto
            cv2.imwrite("melhor_foto_detectada.jpg", best_photo)
            print("Salva como: melhor_foto_detectada.jpg")
        else:
            print("Nenhuma foto válida encontrada.")
            
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python debug_images.py <caminho_pdf>")
        sys.exit(1)
    
    extract_and_analyze_all_images(sys.argv[1])
