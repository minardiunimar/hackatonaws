#!/usr/bin/env python3
"""
Script para diagnosticar a extração de imagens do PDF
"""

import fitz
import cv2
import numpy as np
import os
import sys

def debug_image_extraction(pdf_path):
    """Debug da extração de imagens"""
    print(f"Analisando PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Arquivo não encontrado: {pdf_path}")
        return
    
    try:
        doc = fitz.open(pdf_path)
        print(f"PDF aberto com sucesso. Páginas: {len(doc)}")
        
        total_images = 0
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            print(f"\nPágina {page_num + 1}:")
            print(f"  Imagens encontradas: {len(image_list)}")
            
            for img_index, img in enumerate(image_list):
                print(f"  Imagem {img_index + 1}:")
                print(f"    xref: {img[0]}")
                print(f"    smask: {img[1]}")
                print(f"    width: {img[2]}")
                print(f"    height: {img[3]}")
                print(f"    bpc: {img[4]}")
                print(f"    colorspace: {img[5]}")
                print(f"    alt: {img[6]}")
                print(f"    name: {img[7]}")
                print(f"    filter: {img[8]}")
                
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    print(f"    Pixmap info:")
                    print(f"      width: {pix.width}")
                    print(f"      height: {pix.height}")
                    print(f"      n: {pix.n}")
                    print(f"      alpha: {pix.alpha}")
                    print(f"      colorspace: {pix.colorspace}")
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        img_array = np.frombuffer(img_data, dtype=np.uint8)
                        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        if img_cv is not None:
                            print(f"      OpenCV shape: {img_cv.shape}")
                            
                            # Salva a imagem para inspeção
                            output_path = f"debug_img_p{page_num + 1}_i{img_index}.jpg"
                            cv2.imwrite(output_path, img_cv)
                            print(f"      Imagem salva: {output_path}")
                            
                            # Tenta detectar faces
                            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv
                            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                            print(f"      Faces detectadas: {len(faces)}")
                            
                            if len(faces) > 0:
                                print(f"      Coordenadas das faces: {faces}")
                                # Salva imagem com faces marcadas
                                img_with_faces = img_cv.copy()
                                for (x, y, w, h) in faces:
                                    cv2.rectangle(img_with_faces, (x, y), (x+w, y+h), (255, 0, 0), 2)
                                face_output_path = f"debug_faces_p{page_num + 1}_i{img_index}.jpg"
                                cv2.imwrite(face_output_path, img_with_faces)
                                print(f"      Imagem com faces marcadas: {face_output_path}")
                            
                            total_images += 1
                        else:
                            print(f"      Erro: Não foi possível decodificar a imagem")
                    else:
                        print(f"      Pulando: Colorspace não suportado")
                    
                    pix = None
                    
                except Exception as e:
                    print(f"    Erro ao processar imagem: {e}")
        
        doc.close()
        print(f"\nTotal de imagens extraídas: {total_images}")
        
    except Exception as e:
        print(f"Erro ao abrir PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python debug_image_extraction.py <caminho_do_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    debug_image_extraction(pdf_path)
