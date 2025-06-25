#!/usr/bin/env python3
"""
Processador de Documentos Simplificado - Sem dependência do Tesseract
Foca na extração de texto nativo do PDF e detecção de imagens
"""

import re
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Optional, Tuple
import argparse
import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class SimpleDocumentProcessor:
    """Processador de documentos simplificado"""
    
    def __init__(self):
        self.document_patterns = {
            'RG': [
                r'registro\s+geral',
                r'carteira\s+de\s+identidade',
                r'república\s+federativa\s+do\s+brasil',
                r'secretaria\s+de\s+segurança',
                r'rg\s*:?\s*\d+',
                r'identidade',
            ],
            'CNH': [
                r'carteira\s+nacional\s+de\s+habilitação',
                r'permissão\s+para\s+dirigir',
                r'categoria',
                r'validade',
                r'cnh\s*:?\s*\d+',
                r'registro\s*:?\s*\d+',
                r'habilitação',
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
                r'nome\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                r'name\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                r'titular\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                # Padrão mais flexível para capturar nomes em documentos
                r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç]+){1,4})',
            ],
            'cpf': [
                r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'c\.p\.f\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
            ]
        }
    
    def check_pdf_validity(self, pdf_path: str) -> Dict[str, any]:
        """Verifica se o PDF é válido e suas características"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'valid': True,
                'page_count': len(doc),
                'encrypted': doc.needs_pass,
                'metadata': doc.metadata,
                'has_text': False,
                'has_images': False
            }
            
            # Verifica se tem texto extraível
            for page in doc:
                text = page.get_text().strip()
                if text:
                    info['has_text'] = True
                    break
            
            # Verifica se tem imagens
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                if page.get_images():
                    info['has_images'] = True
                    break
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Erro ao verificar PDF: {e}")
            return {'valid': False, 'error': str(e)}
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto do PDF usando PyMuPDF com múltiplas estratégias"""
        try:
            logger.info("Extraindo texto do PDF...")
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Estratégia 1: Texto nativo
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"
                    continue
                
                # Estratégia 2: Texto com layout preservado
                page_text = page.get_text("text")
                if page_text.strip():
                    text += page_text + "\n"
                    continue
                
                # Estratégia 3: Texto em blocos
                blocks = page.get_text("blocks")
                for block in blocks:
                    if len(block) >= 5 and isinstance(block[4], str):
                        text += block[4] + "\n"
            
            doc.close()
            
            if text.strip():
                logger.info(f"Texto extraído com sucesso: {len(text)} caracteres")
                return text.lower()
            else:
                logger.warning("Nenhum texto encontrado no PDF")
                return ""
                
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
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
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            img_array = np.frombuffer(img_data, dtype=np.uint8)
                            img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                            if img_cv is not None and img_cv.size > 0:
                                images.append(img_cv)
                        pix = None
                    except Exception as e:
                        logger.warning(f"Erro ao extrair imagem {img_index}: {e}")
                        continue
            doc.close()
        except Exception as e:
            logger.error(f"Erro ao extrair imagens: {e}")
        
        logger.info(f"Extraídas {len(images)} imagens")
        return images
    
    def identify_document_type(self, text: str) -> Optional[str]:
        """Identifica o tipo de documento baseado no texto"""
        if not text:
            return None
            
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
            best_type = max(scores, key=scores.get)
            logger.info(f"Documento identificado como {best_type} (score: {scores[best_type]})")
            return best_type
        
        logger.warning("Tipo de documento não identificado")
        return None
    
    def extract_information(self, text: str) -> Dict[str, str]:
        """Extrai nome e CPF do texto"""
        info = {'nome': '', 'cpf': ''}
        
        if not text:
            return info
        
        # Extrai CPF primeiro (mais específico)
        for pattern in self.info_patterns['cpf']:
            match = re.search(pattern, text)
            if match:
                cpf = match.group(1) if len(match.groups()) > 0 else match.group(0)
                info['cpf'] = cpf
                logger.info(f"CPF encontrado: {cpf}")
                break
        
        # Extrai nome
        for pattern in self.info_patterns['nome']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                nome = match.strip().title() if isinstance(match, str) else match
                # Remove caracteres especiais e números
                nome_clean = re.sub(r'[^A-Za-zÀ-ÿ\s]', '', nome)
                
                # Verifica se é um nome válido
                if (len(nome_clean) > 5 and 
                    len(nome_clean.split()) >= 2 and 
                    not re.search(r'\d', nome_clean) and
                    nome_clean.lower() not in ['nome completo', 'titular', 'portador']):
                    info['nome'] = nome_clean
                    logger.info(f"Nome encontrado: {nome_clean}")
                    break
            
            if info['nome']:
                break
        
        return info
    
    def detect_face_in_images(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """Detecta e extrai foto/rosto das imagens"""
        if not images:
            return None
            
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            for i, img in enumerate(images):
                if img is None or img.size == 0:
                    continue
                    
                try:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    if len(faces) > 0:
                        # Retorna a primeira face encontrada
                        (x, y, w, h) = faces[0]
                        face_img = img[y:y+h, x:x+w]
                        logger.info(f"Face detectada na imagem {i+1}")
                        return face_img
                except Exception as e:
                    logger.warning(f"Erro ao detectar face na imagem {i+1}: {e}")
                    continue
            
            # Se não encontrar face, retorna a primeira imagem que pareça ser uma foto
            for i, img in enumerate(images):
                if img is not None and img.shape[0] > 100 and img.shape[1] > 100:
                    logger.info(f"Usando imagem {i+1} como foto (sem detecção de face)")
                    return img
            
        except Exception as e:
            logger.error(f"Erro no detector de faces: {e}")
        
        logger.warning("Nenhuma foto encontrada")
        return None
    
    def save_photo(self, photo: np.ndarray, output_path: str) -> bool:
        """Salva a foto extraída"""
        try:
            success = cv2.imwrite(output_path, photo)
            if success:
                logger.info(f"Foto salva: {output_path}")
                return True
            else:
                logger.error(f"Falha ao salvar foto: {output_path}")
                return False
        except Exception as e:
            logger.error(f"Erro ao salvar foto: {e}")
            return False
    
    def process_document(self, pdf_path: str, output_dir: str = ".") -> Dict:
        """Processa o documento completo"""
        if not os.path.exists(pdf_path):
            error_msg = f"Arquivo PDF não encontrado: {pdf_path}"
            logger.error(error_msg)
            return {"erro": error_msg, "sucesso": False}
        
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Processando documento: {pdf_path}")
        
        # Verifica validade do PDF
        pdf_info = self.check_pdf_validity(pdf_path)
        if not pdf_info['valid']:
            error_msg = f"PDF inválido: {pdf_info.get('error', 'Erro desconhecido')}"
            logger.error(error_msg)
            return {"erro": error_msg, "sucesso": False}
        
        logger.info(f"PDF válido: {pdf_info['page_count']} páginas, "
                   f"Texto: {pdf_info['has_text']}, Imagens: {pdf_info['has_images']}")
        
        # Extrai texto
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            error_msg = "Não foi possível extrair texto do PDF"
            logger.error(error_msg)
            return {"erro": error_msg, "sucesso": False}
        
        # Identifica tipo de documento
        doc_type = self.identify_document_type(text)
        
        # Extrai informações
        info = self.extract_information(text)
        
        # Valida CPF
        cpf_valido = False
        if info['cpf']:
            cpf_valido = CPFValidator.validate_cpf(info['cpf'])
            logger.info(f"CPF válido: {cpf_valido}")
        
        # Extrai imagens e procura por foto
        images = self.extract_images_from_pdf(pdf_path)
        photo_path = None
        
        if images:
            photo = self.detect_face_in_images(images)
            if photo is not None:
                photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                photo_path = os.path.join(output_dir, photo_filename)
                if not self.save_photo(photo, photo_path):
                    photo_path = None
        
        # Resultado final
        resultado = {
            "tipo_documento": doc_type,
            "nome": info['nome'],
            "cpf": info['cpf'],
            "cpf_valido": cpf_valido,
            "foto_extraida": photo_path,
            "sucesso": True,
            "texto_extraido_chars": len(text),
            "pdf_info": pdf_info
        }
        
        logger.info("Processamento concluído com sucesso")
        return resultado

def main():
    parser = argparse.ArgumentParser(description='Processador Simplificado de Documentos Pessoais')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='.', help='Diretório de saída (padrão: diretório atual)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verboso')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    processor = SimpleDocumentProcessor()
    resultado = processor.process_document(args.pdf_path, args.output)
    
    if not resultado.get("sucesso", False):
        print(f"ERRO: {resultado.get('erro', 'Erro desconhecido')}")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("RESULTADO DO PROCESSAMENTO")
    print("="*50)
    print(f"Tipo de Documento: {resultado['tipo_documento'] or 'Não identificado'}")
    print(f"Nome: {resultado['nome'] or 'Não encontrado'}")
    print(f"CPF: {resultado['cpf'] or 'Não encontrado'}")
    print(f"CPF Válido: {'Sim' if resultado['cpf_valido'] else 'Não'}")
    print(f"Foto Extraída: {resultado['foto_extraida'] or 'Não encontrada'}")
    print(f"Caracteres Extraídos: {resultado.get('texto_extraido_chars', 0)}")
    print("="*50)

if __name__ == "__main__":
    main()
