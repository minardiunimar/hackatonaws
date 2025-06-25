#!/usr/bin/env python3
"""
Script avançado para extrair todas as imagens possíveis do PDF
"""

import fitz
import cv2
import numpy as np
import os
import sys
from PIL import Image

def extract_all_images(pdf_path):
    """Extrai todas as imagens possíveis do PDF"""
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
            
            # Método 1: Imagens embutidas
            image_list = page.get_images()
            print(f"\nPágina {page_num + 1} - Imagens embutidas: {len(image_list)}")
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    print(f"  Imagem embutida {img_index + 1}: {pix.width}x{pix.height}")
                    
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                        img_array = np.frombuffer(img_data, dtype=np.uint8)
                        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        if img_cv is not None:
                            output_path = f"embedded_p{page_num + 1}_i{img_index}.jpg"
                            cv2.imwrite(output_path, img_cv)
                            print(f"    Salva: {output_path}")
                            
                            # Detecta faces
                            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                            print(f"    Faces: {len(faces)}")
                            
                            total_images += 1
                    
                    pix = None
                    
                except Exception as e:
                    print(f"    Erro: {e}")
            
            # Método 2: Renderizar página como imagem e procurar por regiões
            print(f"\nPágina {page_num + 1} - Renderizando página completa...")
            
            # Renderiza a página em alta resolução
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img_array = np.frombuffer(img_data, dtype=np.uint8)
            page_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if page_img is not None:
                output_path = f"page_render_p{page_num + 1}.jpg"
                cv2.imwrite(output_path, page_img)
                print(f"  Página renderizada salva: {output_path}")
                
                # Detecta faces na página completa
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                print(f"  Faces detectadas na página: {len(faces)}")
                
                if len(faces) > 0:
                    print(f"  Coordenadas das faces: {faces}")
                    # Salva imagem com faces marcadas
                    img_with_faces = page_img.copy()
                    for i, (x, y, w, h) in enumerate(faces):
                        cv2.rectangle(img_with_faces, (x, y), (x+w, y+h), (0, 255, 0), 3)
                        
                        # Extrai a região da face
                        face_region = page_img[y:y+h, x:x+w]
                        face_output = f"face_p{page_num + 1}_f{i}.jpg"
                        cv2.imwrite(face_output, face_region)
                        print(f"    Face {i+1} extraída: {face_output}")
                    
                    faces_marked_path = f"faces_marked_p{page_num + 1}.jpg"
                    cv2.imwrite(faces_marked_path, img_with_faces)
                    print(f"  Faces marcadas: {faces_marked_path}")
                
                # Método 3: Procurar por regiões que podem ser fotos
                print(f"  Procurando regiões de foto...")
                
                # Converte para escala de cinza
                gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)
                
                # Detecta contornos
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Filtra contornos por tamanho (possíveis fotos)
                min_area = 5000  # área mínima para ser considerada uma foto
                photo_candidates = []
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > min_area:
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = w / h
                        
                        # Filtros para identificar possíveis fotos
                        if 0.5 <= aspect_ratio <= 2.0 and w > 80 and h > 80:
                            photo_candidates.append((x, y, w, h, area))
                
                print(f"  Candidatos a foto encontrados: {len(photo_candidates)}")
                
                if photo_candidates:
                    # Ordena por área (maior primeiro)
                    photo_candidates.sort(key=lambda x: x[4], reverse=True)
                    
                    img_with_candidates = page_img.copy()
                    for i, (x, y, w, h, area) in enumerate(photo_candidates):
                        cv2.rectangle(img_with_candidates, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        
                        # Extrai a região candidata
                        candidate_region = page_img[y:y+h, x:x+w]
                        candidate_output = f"candidate_p{page_num + 1}_c{i}.jpg"
                        cv2.imwrite(candidate_output, candidate_region)
                        print(f"    Candidato {i+1}: {candidate_output} (área: {area})")
                        
                        # Tenta detectar face na região candidata
                        candidate_gray = cv2.cvtColor(candidate_region, cv2.COLOR_BGR2GRAY)
                        candidate_faces = face_cascade.detectMultiScale(candidate_gray, 1.1, 4, minSize=(20, 20))
                        print(f"      Faces no candidato: {len(candidate_faces)}")
                    
                    candidates_marked_path = f"candidates_marked_p{page_num + 1}.jpg"
                    cv2.imwrite(candidates_marked_path, img_with_candidates)
                    print(f"  Candidatos marcados: {candidates_marked_path}")
            
            pix = None
        
        doc.close()
        print(f"\nProcessamento concluído!")
        
    except Exception as e:
        print(f"Erro ao processar PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 advanced_image_extraction.py <caminho_do_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    extract_all_images(pdf_path)
