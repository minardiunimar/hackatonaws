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
