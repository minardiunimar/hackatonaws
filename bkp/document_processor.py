#!/usr/bin/env python3
"""
Aplicação para processamento de documentos pessoais em PDF
Identifica tipo de documento, extrai informações e valida CPF
"""

import re
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, List, Optional, Tuple
import argparse
import sys
import os

class CPFValidator:
    """Classe para validação de CPF"""
    
    @staticmethod
    def clean_cpf(cpf: str) -> str:
        """Remove caracteres não numéricos do CPF e extrai os 11 dígitos corretos"""
        # Remove todos os caracteres não numéricos
        cleaned = re.sub(r'[^0-9]', '', cpf)
        
        # Se o CPF limpo tem mais de 11 dígitos, tenta extrair o CPF correto
        if len(cleaned) > 11:
            # Para formato como 200~262106898/76 (14 dígitos: 20026210689876)
            # O CPF correto são os últimos 11 dígitos: 26210689876
            if len(cleaned) == 14:
                # Testa os últimos 11 dígitos primeiro (mais provável)
                candidate = cleaned[-11:]
                return candidate
            else:
                # Para outros casos, pega os primeiros 11 dígitos
                cleaned = cleaned[:11]
        
        return cleaned
    
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

class DocumentProcessor:
    """Classe principal para processamento de documentos"""
    
    def __init__(self):
        self.document_patterns = {
            'RG': [
                r'registro\s+geral',
                r'carteira\s+de\s+identidade',
                r'república\s+federativa\s+do\s+brasil',
                r'secretaria\s+de\s+segurança',
                r'rg\s*:?\s*\d+',
            ],
            'CNH': [
                r'carteira\s+nacional\s+de\s+habilitação',
                r'permissão\s+para\s+dirigir',
                r'categoria',
                r'validade',
                r'cnh\s*:?\s*\d+',
                r'registro\s*:?\s*\d+',
            ],
            'PASSAPORTE': [
                r'passaporte',
                r'passport',
                r'república\s+federativa\s+do\s+brasil',
                r'ministério\s+das\s+relações\s+exteriores',
                r'tipo\s*:\s*p',
                r'país\s+de\s+emissão',
            ]
        }
        
        self.info_patterns = {
            'nome': [
                r'nome\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+)',
                r'name\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+)',
                r'titular\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ\s]+)',
            ],
            'cpf': [
                r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'c\.p\.f\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                # Formato com ~ e / (ex: 200~262106898/76)
                r'(\d{3}~\d{9}/\d{2})',
                # Formato mais flexível para capturar variações
                r'(\d{3}[~\-\.]\d{3}[\.\-]?\d{3}[\.\-/]\d{2})',
                # Padrão genérico para 11 dígitos com separadores variados
                r'(\d{3}[^\d\s]\d{6}[^\d\s]\d{2})',
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto do PDF usando PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.lower()
        except Exception as e:
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai imagens do PDF"""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        img_array = np.frombuffer(img_data, dtype=np.uint8)
                        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if img_cv is not None:
                            images.append(img_cv)
                    pix = None
            doc.close()
        except Exception as e:
            print(f"Erro ao extrair imagens: {e}")
        
        return images
    
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
        
        # Retorna o tipo com maior pontuação se > 0
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return None
    
    def extract_information(self, text: str) -> Dict[str, str]:
        """Extrai nome e CPF do texto"""
        info = {'nome': '', 'cpf': ''}
        
        # Extrai nome
        for pattern in self.info_patterns['nome']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nome = match.group(1).strip().title()
                # Remove caracteres especiais e números
                nome = re.sub(r'[^A-Za-zÀ-ÿ\s]', '', nome)
                if len(nome) > 3:  # Nome deve ter pelo menos 3 caracteres
                    info['nome'] = nome
                    break
        
        # Extrai CPF
        for pattern in self.info_patterns['cpf']:
            match = re.search(pattern, text)
            if match:
                cpf = match.group(1) if len(match.groups()) > 0 else match.group(0)
                info['cpf'] = cpf
                break
        
        return info
    
    def detect_face_in_images(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """Detecta e extrai foto/rosto das imagens"""
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        for img in images:
            if img is None:
                continue
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Retorna a primeira face encontrada
                (x, y, w, h) = faces[0]
                face_img = img[y:y+h, x:x+w]
                return face_img
        
        # Se não encontrar face, retorna a primeira imagem que pareça ser uma foto
        for img in images:
            if img is not None and img.shape[0] > 100 and img.shape[1] > 100:
                return img
        
        return None
    
    def save_photo(self, photo: np.ndarray, output_path: str) -> bool:
        """Salva a foto extraída"""
        try:
            cv2.imwrite(output_path, photo)
            return True
        except Exception as e:
            print(f"Erro ao salvar foto: {e}")
            return False
    
    def process_document(self, pdf_path: str, output_dir: str = ".") -> Dict:
        """Processa o documento completo"""
        if not os.path.exists(pdf_path):
            return {"erro": "Arquivo PDF não encontrado"}
        
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processando documento: {pdf_path}")
        
        # Extrai texto
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"erro": "Não foi possível extrair texto do PDF"}
        
        # Identifica tipo de documento
        doc_type = self.identify_document_type(text)
        print(f"Tipo de documento identificado: {doc_type or 'Não identificado'}")
        
        # Extrai informações
        info = self.extract_information(text)
        print(f"Informações extraídas: {info}")
        
        # Valida CPF
        cpf_valido = False
        if info['cpf']:
            cpf_valido = CPFValidator.validate_cpf(info['cpf'])
            print(f"CPF válido: {cpf_valido}")
        
        # Extrai imagens e procura por foto
        images = self.extract_images_from_pdf(pdf_path)
        photo_path = None
        
        if images:
            photo = self.detect_face_in_images(images)
            if photo is not None:
                photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                photo_path = os.path.join(output_dir, photo_filename)
                if self.save_photo(photo, photo_path):
                    print(f"Foto salva em: {photo_path}")
                else:
                    photo_path = None
        
        # Resultado final
        resultado = {
            "tipo_documento": doc_type,
            "nome": info['nome'],
            "cpf": info['cpf'],
            "cpf_valido": cpf_valido,
            "foto_extraida": photo_path,
            "sucesso": True
        }
        
        return resultado

def main():
    parser = argparse.ArgumentParser(description='Processador de Documentos Pessoais')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='.', help='Diretório de saída (padrão: diretório atual)')
    
    args = parser.parse_args()
    
    processor = DocumentProcessor()
    resultado = processor.process_document(args.pdf_path, args.output)
    
    if "erro" in resultado:
        print(f"ERRO: {resultado['erro']}")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("RESULTADO DO PROCESSAMENTO")
    print("="*50)
    print(f"Tipo de Documento: {resultado['tipo_documento'] or 'Não identificado'}")
    print(f"Nome: {resultado['nome'] or 'Não encontrado'}")
    print(f"CPF: {resultado['cpf'] or 'Não encontrado'}")
    print(f"CPF Válido: {'Sim' if resultado['cpf_valido'] else 'Não'}")
    print(f"Foto Extraída: {resultado['foto_extraida'] or 'Não encontrada'}")
    print("="*50)

if __name__ == "__main__":
    main()
