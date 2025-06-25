#!/usr/bin/env python3
"""
Processador de Documentos Pessoais - Versão com Detecção Avançada de Rostos
Inclui múltiplos métodos de detecção e fallback para imagem completa
"""

import re
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import boto3
import base64
from typing import Dict, List, Optional, Tuple, Any
import argparse
import sys
import os
import logging
import json
import gc  # Garbage collector
from botocore.exceptions import ClientError, NoCredentialsError

class CPFValidator:
    """Classe para validação de CPF"""
    
    @staticmethod
    def clean_cpf(cpf: str) -> str:
        """Remove caracteres não numéricos do CPF"""
        return re.sub(r'[^0-9]', '', cpf)
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida CPF usando o algoritmo oficial
        Returns: True se válido, False caso contrário
        """
        cpf = CPFValidator.clean_cpf(cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        # Calcula segundo dígito verificador
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        # Verifica se os dígitos calculados conferem
        return cpf[9] == str(digit1) and cpf[10] == str(digit2)

class AdvancedFaceDetector:
    """Detector avançado de rostos com múltiplos métodos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Carrega diferentes classificadores Haar
        self.face_cascades = []
        
        # Classificador frontal padrão
        try:
            frontal_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if not frontal_face.empty():
                self.face_cascades.append(('frontal_default', frontal_face))
        except:
            pass
        
        # Classificador frontal alternativo
        try:
            frontal_alt = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
            if not frontal_alt.empty():
                self.face_cascades.append(('frontal_alt', frontal_alt))
        except:
            pass
        
        # Classificador de perfil
        try:
            profile_face = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            if not profile_face.empty():
                self.face_cascades.append(('profile', profile_face))
        except:
            pass
        
        self.logger.info(f"Carregados {len(self.face_cascades)} classificadores de face")
    
    def detect_faces_multiple_methods(self, image: np.ndarray) -> List[Tuple[int, int, int, int, str]]:
        """
        Detecta faces usando múltiplos métodos
        Returns: Lista de (x, y, w, h, method_name)
        """
        all_faces = []
        
        if image is None or image.size == 0:
            return all_faces
        
        # Converte para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Aplica diferentes métodos de detecção
        for method_name, cascade in self.face_cascades:
            try:
                # Parâmetros otimizados para cada método
                if method_name == 'frontal_default':
                    faces = cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1, 
                        minNeighbors=4, 
                        minSize=(30, 30),
                        maxSize=(500, 500)
                    )
                elif method_name == 'frontal_alt':
                    faces = cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.05, 
                        minNeighbors=3, 
                        minSize=(25, 25),
                        maxSize=(400, 400)
                    )
                elif method_name == 'profile':
                    faces = cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1, 
                        minNeighbors=5, 
                        minSize=(30, 30),
                        maxSize=(300, 300)
                    )
                
                # Adiciona faces encontradas
                for (x, y, w, h) in faces:
                    all_faces.append((x, y, w, h, method_name))
                    
            except Exception as e:
                self.logger.warning(f"Erro no método {method_name}: {e}")
                continue
        
        # Remove duplicatas (faces muito próximas)
        unique_faces = self.remove_duplicate_faces(all_faces)
        
        self.logger.info(f"Detectadas {len(unique_faces)} faces únicas usando {len(self.face_cascades)} métodos")
        return unique_faces
    
    def remove_duplicate_faces(self, faces: List[Tuple[int, int, int, int, str]]) -> List[Tuple[int, int, int, int, str]]:
        """Remove faces duplicadas (muito próximas)"""
        if len(faces) <= 1:
            return faces
        
        unique_faces = []
        
        for face in faces:
            x1, y1, w1, h1, method1 = face
            is_duplicate = False
            
            for unique_face in unique_faces:
                x2, y2, w2, h2, method2 = unique_face
                
                # Calcula sobreposição
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                area1 = w1 * h1
                area2 = w2 * h2
                
                # Se sobreposição > 50%, considera duplicata
                if overlap_area > 0.5 * min(area1, area2):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_faces.append(face)
        
        return unique_faces
    
    def enhance_image_for_detection(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Cria versões melhoradas da imagem para detecção
        """
        enhanced_images = [image]  # Imagem original
        
        try:
            # Versão com equalização de histograma
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            equalized = cv2.equalizeHist(gray)
            if len(image.shape) == 3:
                equalized_bgr = cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
                enhanced_images.append(equalized_bgr)
            else:
                enhanced_images.append(equalized)
            
            # Versão com ajuste de contraste
            alpha = 1.2  # Contraste
            beta = 10    # Brilho
            contrast_adjusted = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
            enhanced_images.append(contrast_adjusted)
            
            # Versão com desfoque gaussiano leve (remove ruído)
            blurred = cv2.GaussianBlur(image, (3, 3), 0)
            enhanced_images.append(blurred)
            
        except Exception as e:
            self.logger.warning(f"Erro ao melhorar imagem: {e}")
        
        return enhanced_images

class DocumentProcessor:
    """Processador principal de documentos com detecção avançada"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.textract_client = None
        self.logger = logging.getLogger(__name__)
        self.face_detector = AdvancedFaceDetector()
        
        # Configurações de memória
        self.max_image_size = 2048
        self.max_render_resolution = 1.5
        
        # Padrões para identificação de tipos de documento
        self.document_patterns = {
            'RG': [
                r'registro\s+geral',
                r'carteira\s+de\s+identidade',
                r'república\s+federativa\s+do\s+brasil',
                r'secretaria\s+de\s+segurança',
                r'instituto\s+de\s+identificação'
            ],
            'CNH': [
                r'carteira\s+nacional\s+de\s+habilitação',
                r'categoria',
                r'condutor',
                r'habilitação',
                r'detran'
            ],
            'PASSAPORTE': [
                r'passaporte',
                r'passport',
                r'ministério\s+das\s+relações\s+exteriores',
                r'república\s+federativa\s+do\s+brasil'
            ]
        }
        
        # Padrões para extração de informações
        self.info_patterns = {
            'nome': [
                r'nome[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+)',
                r'name[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+)',
                r'^([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]{10,})$'
            ],
            'cpf': [
                r'cpf[:\s]*(\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2})',
                r'(\d{3}\.?\d{3}\.?\d{3}[-\.]?\d{2})',
                r'cpf[:\s]*(\d{11})'
            ],
            'rg': [
                r'rg[:\s]*(\d+\.?\d+\.?\d+[-\.]?\d*)',
                r'registro\s+geral[:\s]*(\d+\.?\d+\.?\d+[-\.]?\d*)',
                r'identidade[:\s]*(\d+\.?\d+\.?\d+[-\.]?\d*)'
            ]
        }
    
    def initialize_textract(self):
        """Inicializa o cliente Textract"""
        try:
            self.textract_client = boto3.client('textract', region_name=self.region)
            self.logger.info("Cliente Textract inicializado com sucesso")
        except NoCredentialsError:
            self.logger.error("Credenciais AWS não encontradas")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao inicializar Textract: {e}")
            raise
    def extract_text_with_textract(self, pdf_path: str) -> Tuple[str, Dict]:
        """Extrai texto usando AWS Textract"""
        if not self.textract_client:
            self.initialize_textract()
        
        try:
            with open(pdf_path, 'rb') as document:
                document_bytes = document.read()
            
            # Análise de texto simples
            response = self.textract_client.detect_document_text(
                Document={'Bytes': document_bytes}
            )
            
            # Extrai texto
            text = ""
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text += block['Text'] + '\n'
            
            # Análise de formulários estruturados
            try:
                form_response = self.textract_client.analyze_document(
                    Document={'Bytes': document_bytes},
                    FeatureTypes=['FORMS']
                )
                
                # Extrai campos estruturados
                structured_data = self.extract_structured_data(form_response)
                
            except Exception as e:
                self.logger.warning(f"Erro na análise de formulários: {e}")
                structured_data = {}
            
            return text, structured_data
            
        except ClientError as e:
            self.logger.error(f"Erro do Textract: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao processar documento: {e}")
            raise
    
    def extract_structured_data(self, response: Dict) -> Dict[str, str]:
        """Extrai dados estruturados da resposta do Textract"""
        structured_data = {}
        
        # Mapeia blocos por ID
        blocks = {block['Id']: block for block in response['Blocks']}
        
        # Processa pares chave-valor
        for block in response['Blocks']:
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    # É uma chave
                    key_text = self.get_text_from_block(block, blocks)
                    
                    # Procura o valor correspondente
                    if 'Relationships' in block:
                        for relationship in block['Relationships']:
                            if relationship['Type'] == 'VALUE':
                                for value_id in relationship['Ids']:
                                    if value_id in blocks:
                                        value_block = blocks[value_id]
                                        value_text = self.get_text_from_block(value_block, blocks)
                                        
                                        # Limpa e armazena
                                        clean_key = re.sub(r'[:\s]+$', '', key_text.lower().strip())
                                        structured_data[clean_key] = value_text.strip()
        
        return structured_data
    
    def get_text_from_block(self, block: Dict, blocks: Dict) -> str:
        """Extrai texto de um bloco"""
        text = ""
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        if child_id in blocks:
                            child_block = blocks[child_id]
                            if child_block['BlockType'] == 'WORD':
                                text += child_block['Text'] + ' '
        return text.strip()
    
    def resize_image_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Redimensiona imagem se for muito grande"""
        if image is None or image.size == 0:
            return image
            
        height, width = image.shape[:2]
        max_dimension = max(height, width)
        
        if max_dimension > self.max_image_size:
            scale = self.max_image_size / max_dimension
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            self.logger.info(f"Imagem redimensionada de {width}x{height} para {new_width}x{new_height}")
            return resized
        
        return image
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai imagens embutidas do PDF"""
        images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 5)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.width * pix.height > 4000000:
                            self.logger.warning(f"Imagem muito grande ignorada: {pix.width}x{pix.height}")
                            pix = None
                            continue
                        
                        if pix.n - pix.alpha < 4:
                            img_data = pix.tobytes("png")
                            nparr = np.frombuffer(img_data, np.uint8)
                            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if cv_img is not None and cv_img.shape[0] > 50 and cv_img.shape[1] > 50:
                                cv_img = self.resize_image_if_needed(cv_img)
                                images.append(cv_img)
                        
                        pix = None
                        
                        if len(images) >= 10:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair imagem {img_index} da página {page_num}: {e}")
                        continue
                
                gc.collect()
                
                if len(images) >= 10:
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagens do PDF: {e}")
        finally:
            if doc:
                doc.close()
        
        return images
    
    def extract_full_page_images(self, pdf_path: str) -> List[np.ndarray]:
        """
        Extrai imagens completas das páginas do documento
        Usado como fallback quando não encontra rostos
        """
        page_images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            self.logger.info(f"Extraindo imagens completas de {min(len(doc), 3)} páginas")
            
            for page_num in range(min(len(doc), 3)):  # Máximo 3 páginas
                page = doc.load_page(page_num)
                
                # Renderiza com resolução moderada
                mat = fitz.Matrix(1.2, 1.2)  # Resolução menor para economizar memória
                pix = page.get_pixmap(matrix=mat)
                
                if pix.width * pix.height > 8000000:  # Máximo 8MP para páginas completas
                    self.logger.warning(f"Página {page_num} muito grande, reduzindo resolução")
                    mat = fitz.Matrix(0.8, 0.8)  # Resolução ainda menor
                    pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if cv_img is not None:
                    # Redimensiona se necessário
                    cv_img = self.resize_image_if_needed(cv_img)
                    
                    # Aplica crop inteligente para remover bordas excessivas
                    cropped_page = self.smart_crop_page(cv_img)
                    if cropped_page is not None:
                        page_images.append(cropped_page)
                    else:
                        page_images.append(cv_img)
                
                pix = None
                cv_img = None
                gc.collect()
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair páginas completas: {e}")
        finally:
            if doc:
                doc.close()
        
        return page_images
    
    def smart_crop_page(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Aplica crop inteligente na página para remover bordas desnecessárias
        """
        try:
            # Converte para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplica threshold para encontrar conteúdo
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            
            # Encontra contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Encontra o maior contorno (conteúdo principal)
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Adiciona margem de 5%
                margin_x = int(w * 0.05)
                margin_y = int(h * 0.05)
                
                x = max(0, x - margin_x)
                y = max(0, y - margin_y)
                w = min(image.shape[1] - x, w + 2 * margin_x)
                h = min(image.shape[0] - y, h + 2 * margin_y)
                
                # Crop a região
                cropped = image[y:y+h, x:x+w]
                
                # Redimensiona para tamanho padrão mantendo proporção
                target_height = 600
                aspect_ratio = w / h
                target_width = int(target_height * aspect_ratio)
                
                if target_width > 800:  # Limita largura máxima
                    target_width = 800
                    target_height = int(target_width / aspect_ratio)
                
                resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_AREA)
                return resized
            
        except Exception as e:
            self.logger.warning(f"Erro no crop inteligente: {e}")
        
        return None
    
    def detect_faces_advanced(self, images: List[np.ndarray]) -> List[Tuple[np.ndarray, str, float]]:
        """
        Detecta faces usando métodos avançados
        Returns: Lista de (face_image, detection_method, confidence_score)
        """
        all_faces = []
        
        for img_idx, img in enumerate(images):
            if img is None or img.size == 0:
                continue
            
            self.logger.info(f"Analisando imagem {img_idx + 1}/{len(images)} para detecção de faces")
            
            # Cria versões melhoradas da imagem
            enhanced_images = self.face_detector.enhance_image_for_detection(img)
            
            for enh_idx, enhanced_img in enumerate(enhanced_images):
                # Detecta faces com múltiplos métodos
                faces = self.face_detector.detect_faces_multiple_methods(enhanced_img)
                
                for face_data in faces:
                    x, y, w, h, method = face_data
                    
                    # Calcula score de confiança baseado no tamanho e método
                    face_area = w * h
                    confidence = face_area / (enhanced_img.shape[0] * enhanced_img.shape[1])
                    
                    # Bonus para métodos mais confiáveis
                    if method == 'frontal_default':
                        confidence *= 1.2
                    elif method == 'frontal_alt':
                        confidence *= 1.1
                    
                    # Bonus para imagem original (não melhorada)
                    if enh_idx == 0:
                        confidence *= 1.1
                    
                    # Extrai e processa a face
                    try:
                        face_region = self.crop_face_3x4(enhanced_img, x, y, w, h)
                        if face_region is not None:
                            detection_info = f"{method}_enh{enh_idx}"
                            all_faces.append((face_region, detection_info, confidence))
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair face: {e}")
                        continue
        
        # Ordena por confiança (maior primeiro)
        all_faces.sort(key=lambda x: x[2], reverse=True)
        
        self.logger.info(f"Total de faces detectadas: {len(all_faces)}")
        return all_faces
    
    def crop_face_3x4(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> Optional[np.ndarray]:
        """Corta a imagem para formato 3x4 focando no rosto"""
        try:
            img_height, img_width = image.shape[:2]
            aspect_ratio = 3.0 / 4.0
            
            # Margens otimizadas
            top_margin = int(h * 0.3)
            bottom_margin = int(h * 0.2)
            side_margin = int(w * 0.1)
            
            # Calcular nova área expandida
            expanded_x = max(0, x - side_margin)
            expanded_y = max(0, y - top_margin)
            expanded_w = min(img_width - expanded_x, w + 2 * side_margin)
            expanded_h = min(img_height - expanded_y, h + top_margin + bottom_margin)
            
            # Ajustar para proporção 3x4
            current_ratio = expanded_w / expanded_h
            
            if current_ratio > aspect_ratio:
                new_width = int(expanded_h * aspect_ratio)
                width_diff = expanded_w - new_width
                expanded_x += width_diff // 2
                expanded_w = new_width
            else:
                new_height = int(expanded_w / aspect_ratio)
                height_diff = expanded_h - new_height
                expanded_y += height_diff // 2
                expanded_h = new_height
            
            # Garantir limites
            expanded_x = max(0, expanded_x)
            expanded_y = max(0, expanded_y)
            expanded_w = min(img_width - expanded_x, expanded_w)
            expanded_h = min(img_height - expanded_y, expanded_h)
            
            # Extrair região
            cropped_face = image[expanded_y:expanded_y + expanded_h, 
                               expanded_x:expanded_x + expanded_w]
            
            # Redimensionar para tamanho padrão
            if cropped_face.size > 0:
                resized_face = cv2.resize(cropped_face, (200, 267), interpolation=cv2.INTER_AREA)
                return resized_face
            
        except Exception as e:
            self.logger.error(f"Erro ao cortar face 3x4: {e}")
        
        return None
    def detect_best_photo_or_fallback(self, images: List[np.ndarray], pdf_path: str) -> Tuple[Optional[np.ndarray], str]:
        """
        Detecta a melhor foto com rosto ou usa fallback para imagem completa
        Returns: (image, extraction_type)
        """
        extraction_type = "none"
        
        # Primeiro: tenta detectar rostos com métodos avançados
        print("🔍 Iniciando detecção avançada de rostos...")
        faces_detected = self.detect_faces_advanced(images)
        
        if faces_detected:
            best_face, method, confidence = faces_detected[0]
            print(f"✅ Melhor rosto detectado com {method} (confiança: {confidence:.3f})")
            return best_face, f"face_detected_{method}"
        
        print("⚠️  Nenhum rosto detectado em imagens embutidas")
        
        # Segundo: tenta detectar rostos em páginas renderizadas
        print("🔍 Procurando rostos em páginas renderizadas...")
        try:
            rendered_images = self.extract_faces_from_rendered_pages(pdf_path)
            if rendered_images:
                rendered_faces = self.detect_faces_advanced(rendered_images)
                if rendered_faces:
                    best_face, method, confidence = rendered_faces[0]
                    print(f"✅ Rosto encontrado em página renderizada com {method} (confiança: {confidence:.3f})")
                    return best_face, f"face_rendered_{method}"
            
            # Limpa memória
            rendered_images = None
            gc.collect()
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar páginas renderizadas: {e}")
        
        print("⚠️  Nenhum rosto detectado em páginas renderizadas")
        
        # Terceiro: fallback para imagem completa do documento
        print("📄 Extraindo imagem completa do documento como fallback...")
        try:
            page_images = self.extract_full_page_images(pdf_path)
            if page_images:
                # Seleciona a primeira página (geralmente a principal)
                best_page = page_images[0]
                print(f"✅ Imagem completa extraída: {best_page.shape[1]}x{best_page.shape[0]} pixels")
                return best_page, "full_document"
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagem completa: {e}")
        
        print("❌ Não foi possível extrair nenhuma imagem")
        return None, "none"
    
    def extract_faces_from_rendered_pages(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai faces das páginas renderizadas"""
        faces = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 3)):
                page = doc.load_page(page_num)
                
                mat = fitz.Matrix(self.max_render_resolution, self.max_render_resolution)
                pix = page.get_pixmap(matrix=mat)
                
                if pix.width * pix.height > 6000000:
                    self.logger.warning(f"Página {page_num} muito grande, pulando")
                    pix = None
                    continue
                
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if cv_img is not None:
                    cv_img = self.resize_image_if_needed(cv_img)
                    faces.append(cv_img)
                
                pix = None
                cv_img = None
                gc.collect()
                
                if len(faces) >= 3:
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair faces das páginas renderizadas: {e}")
        finally:
            if doc:
                doc.close()
        
        return faces
    
    def save_photo(self, photo: np.ndarray, output_path: str) -> bool:
        """Salva a foto extraída"""
        try:
            cv2.imwrite(output_path, photo)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar foto: {e}")
            return False
    
    def identify_document_type(self, text: str) -> Optional[str]:
        """Identifica o tipo de documento baseado no texto"""
        text = text.lower()
        
        scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            scores[doc_type] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return None
    
    def extract_information_from_text(self, text: str) -> Dict[str, str]:
        """Extrai informações do texto usando regex"""
        info = {}
        
        for field, patterns in self.info_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if field == 'cpf':
                        cpf = re.sub(r'[^\d]', '', matches[0])
                        if len(cpf) == 11:
                            formatted_cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
                            info[field] = formatted_cpf
                            break
                    else:
                        info[field] = matches[0].strip()
                        break
        
        return info
    
    def process_document(self, pdf_path: str, output_dir: str = "./") -> Dict[str, Any]:
        """Processa um documento PDF completo com detecção avançada"""
        try:
            self.logger.info(f"Processando documento: {pdf_path}")
            
            # Extrai texto com Textract
            print("📝 Extraindo texto com AWS Textract...")
            text, structured_data = self.extract_text_with_textract(pdf_path)
            
            if structured_data:
                print("📋 Analisando formulários estruturados...")
            
            # Identifica tipo de documento
            doc_type = self.identify_document_type(text)
            print(f"📄 Tipo de documento identificado: {doc_type}")
            
            # Extrai informações do texto
            extracted_info = self.extract_information_from_text(text)
            
            # Combina informações estruturadas
            if structured_data:
                field_mapping = {
                    'nome': ['nome', 'name'],
                    'cpf': ['cpf'],
                    'rg': ['rg', 'registro geral', 'identidade']
                }
                
                for our_key, possible_keys in field_mapping.items():
                    if not extracted_info.get(our_key):
                        for key in possible_keys:
                            if key in structured_data:
                                value = structured_data[key]
                                if our_key == 'cpf' and value:
                                    clean_cpf = re.sub(r'[^\d]', '', value)
                                    if len(clean_cpf) == 11 and CPFValidator.validate_cpf(clean_cpf):
                                        formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"
                                        extracted_info[our_key] = formatted_cpf
                                elif value:
                                    extracted_info[our_key] = value
                                break
            
            print(f"ℹ️  Informações extraídas: {extracted_info}")
            
            # Valida CPF
            cpf_valid = False
            if extracted_info.get('cpf'):
                cpf_valid = CPFValidator.validate_cpf(extracted_info['cpf'])
            print(f"✅ CPF válido: {cpf_valid}")
            
            # Extrai fotos com detecção avançada e fallback
            print("🖼️  Iniciando extração de imagens...")
            photo_path = None
            extraction_method = "none"
            
            try:
                # Extrai imagens embutidas
                embedded_images = self.extract_images_from_pdf(pdf_path)
                
                # Detecta melhor foto ou usa fallback
                best_image, extraction_method = self.detect_best_photo_or_fallback(embedded_images, pdf_path)
                
                # Limpa memória
                embedded_images = None
                gc.collect()
                
                if best_image is not None:
                    photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                    photo_path = os.path.join(output_dir, photo_filename)
                    
                    if self.save_photo(best_image, photo_path):
                        if extraction_method.startswith('face_'):
                            print(f"📸 Foto 3x4 com rosto salva: {photo_path}")
                        else:
                            print(f"📄 Imagem completa do documento salva: {photo_path}")
                    else:
                        photo_path = None
                else:
                    print("❌ Nenhuma imagem pôde ser extraída")
                    
            except Exception as photo_error:
                self.logger.error(f"Erro no processamento de imagens: {photo_error}")
                print("⚠️  Erro ao processar imagens, continuando sem foto...")
            
            # Força limpeza final
            gc.collect()
            
            # Monta resultado
            result = {
                'tipo_documento': doc_type,
                'nome': extracted_info.get('nome', ''),
                'cpf': extracted_info.get('cpf', ''),
                'rg': extracted_info.get('rg', ''),
                'cpf_valido': cpf_valid,
                'foto_extraida': photo_path,
                'extraction_method': extraction_method,
                'sucesso': True,
                'campos_estruturados': structured_data
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao processar documento: {e}")
            return {
                'tipo_documento': None,
                'nome': '',
                'cpf': '',
                'rg': '',
                'cpf_valido': False,
                'foto_extraida': None,
                'extraction_method': 'error',
                'sucesso': False,
                'erro': str(e)
            }

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Processador Avançado de Documentos')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='./', help='Diretório de saída')
    parser.add_argument('-r', '--region', default='us-east-1', help='Região AWS')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    processor = DocumentProcessor(region=args.region)
    result = processor.process_document(args.pdf_path, args.output)
    
    print("\n" + "="*60)
    print("🎯 RESULTADO DO PROCESSAMENTO AVANÇADO")
    print("="*60)
    print(f"📄 Tipo de Documento: {result['tipo_documento']}")
    print(f"👤 Nome: {result['nome']}")
    print(f"🆔 CPF: {result['cpf']}")
    print(f"🆔 RG: {result['rg']}")
    print(f"✅ CPF Válido: {'Sim' if result['cpf_valido'] else 'Não'}")
    print(f"📸 Imagem Extraída: {result['foto_extraida'] or 'Não encontrada'}")
    print(f"🔍 Método de Extração: {result.get('extraction_method', 'N/A')}")
    print(f"📋 Campos Estruturados: {len(result.get('campos_estruturados', {}))}")
    print("="*60)

if __name__ == "__main__":
    main()
