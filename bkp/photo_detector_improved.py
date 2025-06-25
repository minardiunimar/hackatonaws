#!/usr/bin/env python3
"""
Detector de fotos melhorado para distinguir entre fotos reais e assinaturas
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple
import logging

class ImprovedPhotoDetector:
    """Classe para detecção inteligente de fotos em documentos"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Carrega classificadores
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    def is_signature_like(self, image: np.ndarray) -> bool:
        """
        Verifica se a imagem parece ser uma assinatura
        Returns: True se parecer assinatura, False caso contrário
        """
        if image is None or image.size == 0:
            return True
        
        # Converte para escala de cinza se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        height, width = gray.shape
        
        # 1. Verifica proporção - assinaturas tendem a ser mais largas que altas
        aspect_ratio = width / height
        if aspect_ratio > 3.0:  # Muito larga para ser uma foto
            return True
        
        # 2. Verifica densidade de pixels - assinaturas têm menos pixels preenchidos
        # Binariza a imagem
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Calcula densidade de pixels escuros (conteúdo)
        dark_pixels = np.sum(binary == 0)
        total_pixels = binary.size
        density = dark_pixels / total_pixels
        
        # Assinaturas geralmente têm baixa densidade (< 15%)
        if density < 0.15:
            return True
        
        # 3. Verifica complexidade da imagem usando gradientes
        # Assinaturas têm padrões mais simples
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # Calcula variância dos gradientes
        gradient_variance = np.var(gradient_magnitude)
        
        # Assinaturas têm menor variância de gradientes
        if gradient_variance < 1000:
            return True
        
        # 4. Verifica se tem características de texto/escrita
        # Usa detecção de contornos para identificar formas de letras
        contours, _ = cv2.findContours(255 - binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 0:
            # Calcula estatísticas dos contornos
            areas = [cv2.contourArea(c) for c in contours]
            if len(areas) > 0:
                avg_area = np.mean(areas)
                # Se tem muitos contornos pequenos, pode ser texto/assinatura
                small_contours = sum(1 for area in areas if area < avg_area * 0.5)
                if small_contours > len(contours) * 0.7:
                    return True
        
        return False
    
    def is_photo_like(self, image: np.ndarray) -> bool:
        """
        Verifica se a imagem parece ser uma foto de pessoa
        Returns: True se parecer foto, False caso contrário
        """
        if image is None or image.size == 0:
            return False
        
        # Converte para escala de cinza se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        height, width = gray.shape
        
        # 1. Verifica tamanho mínimo - fotos devem ter tamanho razoável
        if height < 80 or width < 60:
            return False
        
        # 2. Verifica proporção - fotos de documento têm proporções típicas
        aspect_ratio = width / height
        if aspect_ratio < 0.6 or aspect_ratio > 1.5:  # Fora da faixa típica de fotos 3x4
            return False
        
        # 3. Verifica densidade de pixels - fotos têm mais conteúdo
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dark_pixels = np.sum(binary == 0)
        total_pixels = binary.size
        density = dark_pixels / total_pixels
        
        # Fotos geralmente têm densidade moderada a alta (> 20%)
        if density < 0.20:
            return False
        
        # 4. Verifica variação tonal - fotos têm mais variação
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256])
        # Calcula entropia do histograma
        histogram = histogram.flatten()
        histogram = histogram[histogram > 0]  # Remove zeros
        entropy = -np.sum((histogram / np.sum(histogram)) * np.log2(histogram / np.sum(histogram)))
        
        # Fotos têm maior entropia (mais variação tonal)
        if entropy < 4.0:
            return False
        
        # 5. Tenta detectar características faciais
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        if len(faces) > 0:
            # Se detectou face, verifica se também detecta olhos
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(10, 10))
                if len(eyes) >= 1:  # Pelo menos um olho detectado
                    return True
        
        return False
    
    def analyze_image_quality(self, image: np.ndarray) -> dict:
        """
        Analisa a qualidade e características da imagem
        Returns: Dicionário com métricas da imagem
        """
        if image is None or image.size == 0:
            return {"valid": False}
        
        # Converte para escala de cinza se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        height, width = gray.shape
        
        # Calcula métricas
        aspect_ratio = width / height
        
        # Densidade de pixels
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dark_pixels = np.sum(binary == 0)
        density = dark_pixels / binary.size
        
        # Variância (medida de contraste)
        variance = np.var(gray)
        
        # Entropia (medida de complexidade)
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        histogram = histogram[histogram > 0]
        entropy = -np.sum((histogram / np.sum(histogram)) * np.log2(histogram / np.sum(histogram)))
        
        # Detecção de faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        has_face = len(faces) > 0
        
        # Detecção de olhos (se tem face)
        has_eyes = False
        if has_face:
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 3, minSize=(10, 10))
                if len(eyes) >= 1:
                    has_eyes = True
                    break
        
        return {
            "valid": True,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "density": density,
            "variance": variance,
            "entropy": entropy,
            "has_face": has_face,
            "has_eyes": has_eyes,
            "face_count": len(faces)
        }
    
    def detect_best_photo(self, images: List[np.ndarray]) -> Optional[Tuple[np.ndarray, dict]]:
        """
        Detecta a melhor foto entre as imagens fornecidas
        Returns: Tupla (imagem, métricas) ou None se não encontrar foto válida
        """
        candidates = []
        
        for i, img in enumerate(images):
            if img is None:
                continue
            
            # Analisa a imagem
            metrics = self.analyze_image_quality(img)
            if not metrics["valid"]:
                continue
            
            # Calcula score baseado nas métricas
            score = 0
            is_signature = self.is_signature_like(img)
            is_photo = self.is_photo_like(img)
            
            # Se tem características de foto (especialmente face), prioriza sobre assinatura
            if metrics["has_face"] and metrics["has_eyes"]:
                score += 100  # Forte indicador de foto
                is_signature = False  # Override - se tem face e olhos, não é assinatura
            elif metrics["has_face"]:
                score += 70
                # Se tem face mas densidade baixa, pode ser assinatura estilizada
                if metrics["density"] > 0.15:
                    is_signature = False
            
            # Se foi identificado como assinatura E não tem características faciais fortes, ignora
            if is_signature and not (metrics["has_face"] and metrics["density"] > 0.15):
                self.logger.info(f"Imagem {i} identificada como assinatura - ignorando")
                continue
            
            # Verifica se parece foto (mais flexível agora)
            if not is_photo and not metrics["has_face"]:
                self.logger.info(f"Imagem {i} não parece ser uma foto - ignorando")
                continue
            
            # Pontuação por tamanho adequado
            if 80 <= metrics["height"] <= 400 and 60 <= metrics["width"] <= 350:
                score += 20
            
            # Pontuação por proporção adequada (mais flexível)
            if 0.6 <= metrics["aspect_ratio"] <= 1.8:
                score += 15
            
            # Pontuação por densidade adequada
            if 0.20 <= metrics["density"] <= 0.70:
                score += 10
            elif 0.15 <= metrics["density"] < 0.20:
                score += 5  # Densidade um pouco baixa mas aceitável
            
            # Pontuação por complexidade adequada
            if metrics["entropy"] > 4.5:
                score += 10
            elif metrics["entropy"] > 3.0:
                score += 5
            
            # Pontuação por contraste adequado
            if metrics["variance"] > 1000:
                score += 5
            
            candidates.append((img, metrics, score))
            self.logger.info(f"Imagem {i} - Score: {score}, É foto: {is_photo}, É assinatura: {is_signature}, Métricas: {metrics}")
        
        if not candidates:
            self.logger.warning("Nenhuma foto válida encontrada")
            return None
        
        # Retorna a imagem com maior score
        best_candidate = max(candidates, key=lambda x: x[2])
        self.logger.info(f"Melhor foto selecionada com score: {best_candidate[2]}")
        
        return best_candidate[0], best_candidate[1]
