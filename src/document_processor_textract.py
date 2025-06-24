#!/usr/bin/env python3
"""
Processador de Documentos Pessoais usando AWS Textract
Versão melhorada que substitui tesseract por AWS Textract para maior precisão
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

class TextractOCR:
    """Classe para OCR usando AWS Textract"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Inicializa o cliente Textract"""
        try:
            self.textract = boto3.client('textract', region_name=region_name)
            self.logger = logging.getLogger(__name__)
            self.region = region_name
        except NoCredentialsError:
            raise Exception("Credenciais AWS não encontradas. Configure suas credenciais AWS.")
        except Exception as e:
            raise Exception(f"Erro ao inicializar Textract: {e}")
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extrai texto de imagem usando Textract
        Returns: Dicionário com texto e dados estruturados
        """
        try:
            # Usar detect_document_text para texto simples
            response = self.textract.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            # Extrair texto linha por linha
            lines = []
            words = []
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    lines.append(block['Text'])
                elif block['BlockType'] == 'WORD':
                    words.append({
                        'text': block['Text'],
                        'confidence': block.get('Confidence', 0)
                    })
            
            full_text = '\n'.join(lines)
            
            return {
                'text': full_text,
                'lines': lines,
                'words': words,
                'raw_response': response
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidParameterException':
                raise Exception("Formato de imagem inválido para Textract")
            elif error_code == 'DocumentTooLargeException':
                raise Exception("Documento muito grande para Textract")
            else:
                raise Exception(f"Erro do Textract: {e}")
        except Exception as e:
            raise Exception(f"Erro ao processar com Textract: {e}")
    
    def analyze_document_forms(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Analisa formulários e campos estruturados usando Textract
        """
        try:
            response = self.textract.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['FORMS']
            )
            
            # Extrair pares chave-valor
            key_value_pairs = {}
            
            # Mapear blocos por ID
            blocks_by_id = {block['Id']: block for block in response.get('Blocks', [])}
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'KEY_VALUE_SET':
                    if block.get('EntityTypes') and 'KEY' in block['EntityTypes']:
                        # Este é um bloco de chave
                        key_text = self._get_text_from_relationships(block, blocks_by_id)
                        
                        # Encontrar o valor correspondente
                        if 'Relationships' in block:
                            for relationship in block['Relationships']:
                                if relationship['Type'] == 'VALUE':
                                    for value_id in relationship['Ids']:
                                        value_block = blocks_by_id.get(value_id)
                                        if value_block:
                                            value_text = self._get_text_from_relationships(value_block, blocks_by_id)
                                            if key_text and value_text:
                                                key_value_pairs[key_text.lower()] = value_text
            
            return {
                'key_value_pairs': key_value_pairs,
                'raw_response': response
            }
            
        except Exception as e:
            self.logger.warning(f"Erro na análise de formulários: {e}")
            return {'key_value_pairs': {}, 'raw_response': None}
    
    def _get_text_from_relationships(self, block: Dict, blocks_by_id: Dict) -> str:
        """Extrai texto de um bloco seguindo suas relações"""
        text_parts = []
        
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = blocks_by_id.get(child_id)
                        if child_block and child_block['BlockType'] == 'WORD':
                            text_parts.append(child_block['Text'])
        
        return ' '.join(text_parts)

class DocumentProcessorTextract:
    """Classe principal para processamento de documentos usando Textract"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.textract_ocr = TextractOCR(region_name)
        self.logger = logging.getLogger(__name__)
        
        # Padrões para identificação de documentos
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
        
        # Padrões melhorados para extração de informações
        self.info_patterns = {
            'nome': [
                r'nome\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                r'name\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                r'titular\s*:?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]+)',
                r'^([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-záàâãéêíóôõúç\s]{10,})$',  # Nome em linha própria
            ],
            'cpf': [
                # Padrões específicos com contexto "CPF" seguido do número
                r'cpf\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cpf\s*:?\s*(\d{11})',  # CPF sem formatação
                r'cpf\s+(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',  # CPF com espaço
                r'cpf\s+(\d{11})',  # CPF sem formatação com espaço
                r'c\.p\.f\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'c\.p\.f\s*:?\s*(\d{11})',
                r'cadastro\s+de\s+pessoa\s+física\s*:?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cadastro\s+de\s+pessoa\s+física\s*:?\s*(\d{11})',
                # Padrões mais flexíveis para capturar CPF logo após "CPF"
                r'cpf\s*[:\-]?\s*(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?\d{2})',
                r'c\.p\.f\s*[:\-]?\s*(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[\-\s]?\d{2})',
            ],
            'rg': [
                r'rg\s*:?\s*(\d+\.?\d*\.?\d*-?\d*)',
                r'registro\s*:?\s*(\d+\.?\d*\.?\d*-?\d*)',
                r'identidade\s*:?\s*(\d+\.?\d*\.?\d*-?\d*)',
            ],
            'nis_pis_pasep': [
                r'nis\s*:?\s*(\d{11})',
                r'pis\s*:?\s*(\d{11})',
                r'pasep\s*:?\s*(\d{11})',
                r'nis/pis/pasep\s*:?\s*(\d{11})',
                r'pis/pasep\s*:?\s*(\d{11})',
            ]
        }
    
    def pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[bytes]:
        """Converte páginas do PDF em imagens para processamento pelo Textract"""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Aumentar resolução para melhor OCR
                mat = fitz.Matrix(dpi/72, dpi/72)
                pix = page.get_pixmap(matrix=mat)
                
                # Converter para bytes PNG
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
                
            doc.close()
            return images
            
        except Exception as e:
            self.logger.error(f"Erro ao converter PDF para imagens: {e}")
            return []
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai imagens embutidas do PDF para detecção de fotos"""
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
            self.logger.error(f"Erro ao extrair imagens: {e}")
        
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
    
    def extract_information_from_text(self, text: str) -> Dict[str, str]:
        """Extrai informações do texto usando regex"""
        info = {'nome': '', 'cpf': '', 'rg': ''}
        
        # Primeiro, identifica e remove números de NIS/PIS/PASEP para evitar confusão
        nis_pis_numbers = []
        for pattern in self.info_patterns['nis_pis_pasep']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            nis_pis_numbers.extend(matches)
        
        # Extrai nome
        for pattern in self.info_patterns['nome']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                nome = match.group(1).strip()
                # Limpa e valida o nome
                nome = re.sub(r'[^A-Za-záàâãéêíóôõúç\s]', '', nome)
                nome = ' '.join(nome.split())  # Remove espaços extras
                if len(nome) > 5 and not nome.isdigit():  # Nome deve ter pelo menos 5 caracteres
                    info['nome'] = nome.title()
                    break
        
        # Extrai CPF com validação mais rigorosa e padrões melhorados
        cpf_candidates = []
        
        # Primeiro tenta padrões específicos com contexto
        for pattern in self.info_patterns['cpf']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cpf = match if isinstance(match, str) else match[0] if match else ""
                cpf_clean = CPFValidator.clean_cpf(cpf)
                if len(cpf_clean) == 11:
                    # Verifica se não é um número de NIS/PIS/PASEP
                    if cpf_clean not in nis_pis_numbers:
                        # Valida o CPF antes de aceitar
                        if CPFValidator.validate_cpf(cpf_clean):
                            cpf_candidates.append(cpf_clean)
        
        # Padrão específico para "CPF" seguido diretamente do número (sem dois pontos)
        if not cpf_candidates:
            # Procura por "CPF" seguido de espaços e números
            cpf_direct_patterns = [
                r'cpf\s+(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cpf\s+(\d{11})',
                r'cpf\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cpf\s*(\d{11})',
                # Padrões com quebras de linha
                r'cpf\s*\n\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})',
                r'cpf\s*\n\s*(\d{11})',
            ]
            
            for pattern in cpf_direct_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    cpf_clean = CPFValidator.clean_cpf(match)
                    if len(cpf_clean) == 11:
                        if cpf_clean not in nis_pis_numbers:
                            if CPFValidator.validate_cpf(cpf_clean):
                                cpf_candidates.append(cpf_clean)
        
        # Se não encontrou CPF específico, procura por padrão genérico mas com validação
        if not cpf_candidates:
            # Procura por números no formato XXX.XXX.XXX-XX ou XXXXXXXXXXX
            generic_patterns = [
                r'\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b',
                r'\b(\d{11})\b'
            ]
            
            for pattern in generic_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    cpf_clean = CPFValidator.clean_cpf(match)
                    if len(cpf_clean) == 11:
                        # Verifica se não é NIS/PIS/PASEP
                        if cpf_clean not in nis_pis_numbers:
                            # Valida o CPF
                            if CPFValidator.validate_cpf(cpf_clean):
                                # Verifica contexto - deve estar próximo de palavras relacionadas a CPF
                                context_window = 50
                                match_pos = text.find(match)
                                if match_pos != -1:
                                    context_before = text[max(0, match_pos-context_window):match_pos].lower()
                                    context_after = text[match_pos:match_pos+len(match)+context_window].lower()
                                    context = context_before + context_after
                                    
                                    # Verifica se está próximo de indicadores de CPF
                                    cpf_indicators = ['cpf', 'c.p.f', 'cadastro', 'pessoa', 'física']
                                    nis_indicators = ['nis', 'pis', 'pasep']
                                    
                                    has_cpf_context = any(indicator in context for indicator in cpf_indicators)
                                    has_nis_context = any(indicator in context for indicator in nis_indicators)
                                    
                                    # Aceita se tem contexto de CPF e não tem contexto de NIS/PIS/PASEP
                                    if has_cpf_context and not has_nis_context:
                                        cpf_candidates.append(cpf_clean)
                                    elif not has_nis_context and not cpf_candidates:
                                        # Se não tem contexto específico mas é um CPF válido, aceita como último recurso
                                        cpf_candidates.append(cpf_clean)
        
        # Usa o primeiro CPF válido encontrado
        if cpf_candidates:
            cpf_clean = cpf_candidates[0]
            info['cpf'] = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        
        # Extrai RG
        for pattern in self.info_patterns['rg']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rg = match.group(1) if len(match.groups()) > 0 else match.group(0)
                info['rg'] = rg.strip()
                break
        
        return info
    
    def extract_information_from_forms(self, key_value_pairs: Dict[str, str]) -> Dict[str, str]:
        """Extrai informações dos pares chave-valor identificados pelo Textract"""
        info = {'nome': '', 'cpf': '', 'rg': ''}
        
        # Mapear chaves comuns para nossos campos
        key_mappings = {
            'nome': ['nome', 'name', 'titular'],
            'cpf': ['cpf', 'c.p.f', 'cadastro de pessoa física'],
            'rg': ['rg', 'registro geral', 'identidade', 'registro'],
            'nis_pis_pasep': ['nis', 'pis', 'pasep', 'nis/pis/pasep', 'pis/pasep']
        }
        
        # Primeiro identifica números de NIS/PIS/PASEP
        nis_pis_numbers = []
        for key, value in key_value_pairs.items():
            if any(pk in key.lower() for pk in key_mappings['nis_pis_pasep']):
                # Extrai número de 11 dígitos
                nis_match = re.search(r'\d{11}', value)
                if nis_match:
                    nis_pis_numbers.append(nis_match.group(0))
        
        for field, possible_keys in key_mappings.items():
            if field == 'nis_pis_pasep':
                continue  # Já processado acima
                
            for key, value in key_value_pairs.items():
                if any(pk in key.lower() for pk in possible_keys):
                    if field == 'cpf':
                        # Limpar caracteres especiais que o OCR pode ter introduzido
                        cpf_value = value
                        # Remove caracteres comuns de erro de OCR
                        cpf_value = re.sub(r'[~`!@#$%^&*()_+=\[\]{}|\\:";\'<>?,./]', '', cpf_value)
                        cpf_value = re.sub(r'[O]', '0', cpf_value)  # O maiúsculo -> 0
                        cpf_value = re.sub(r'[l]', '1', cpf_value)  # l minúsculo -> 1
                        cpf_value = re.sub(r'[S]', '5', cpf_value)  # S maiúsculo -> 5
                        cpf_value = re.sub(r'[Z]', '2', cpf_value)  # Z maiúsculo -> 2
                        
                        # Procura por sequência de 11 dígitos
                        cpf_match = re.search(r'\d{11}', cpf_value)
                        if cpf_match:
                            cpf_clean = cpf_match.group(0)
                            if len(cpf_clean) == 11:
                                # Verifica se não é um número de NIS/PIS/PASEP
                                if cpf_clean not in nis_pis_numbers:
                                    # Valida o CPF
                                    if CPFValidator.validate_cpf(cpf_clean):
                                        info['cpf'] = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
                                        break
                        
                        # Se não encontrou com limpeza, tenta padrão tradicional
                        if not info['cpf']:
                            cpf_match = re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', value)
                            if cpf_match:
                                cpf_clean = CPFValidator.clean_cpf(cpf_match.group(0))
                                if len(cpf_clean) == 11:
                                    if cpf_clean not in nis_pis_numbers:
                                        if CPFValidator.validate_cpf(cpf_clean):
                                            info['cpf'] = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
                                            break
                    elif field == 'nome':
                        # Limpar e validar nome
                        nome = re.sub(r'[^A-Za-záàâãéêíóôõúç\s]', '', value)
                        nome = ' '.join(nome.split())
                        if len(nome) > 5:
                            info['nome'] = nome.title()
                            break
                    else:
                        info[field] = value.strip()
                        break
        
        return info
    
    def detect_face_in_images(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """Detecta e extrai foto/rosto das imagens usando detector melhorado"""
        from photo_detector_improved import ImprovedPhotoDetector
        
        detector = ImprovedPhotoDetector()
        result = detector.detect_best_photo(images)
        
        if result:
            best_photo, metrics = result
            self.logger.info(f"Foto selecionada com métricas: {metrics}")
            
            # Se detectou face, extrai apenas a região da face
            if metrics.get("has_face", False):
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                gray = cv2.cvtColor(best_photo, cv2.COLOR_BGR2GRAY) if len(best_photo.shape) == 3 else best_photo
                faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                
                if len(faces) > 0:
                    # Retorna a primeira face encontrada
                    (x, y, w, h) = faces[0]
                    # Adiciona uma margem ao redor da face
                    margin = 10
                    x = max(0, x - margin)
                    y = max(0, y - margin)
                    w = min(best_photo.shape[1] - x, w + 2*margin)
                    h = min(best_photo.shape[0] - y, h + 2*margin)
                    
                    face_img = best_photo[y:y+h, x:x+w]
                    return face_img
            
            # Se não detectou face específica, retorna a imagem completa
            return best_photo
        
        self.logger.warning("Nenhuma foto válida encontrada nas imagens")
        return None
    
    def save_photo(self, photo: np.ndarray, output_path: str) -> bool:
        """Salva a foto extraída"""
        try:
            cv2.imwrite(output_path, photo)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar foto: {e}")
            return False
    
    def process_document(self, pdf_path: str, output_dir: str = ".") -> Dict:
        """Processa o documento completo usando Textract"""
        if not os.path.exists(pdf_path):
            return {"erro": "Arquivo PDF não encontrado", "sucesso": False}
        
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processando documento: {pdf_path}")
        
        try:
            # Converte PDF para imagens
            page_images = self.pdf_to_images(pdf_path)
            if not page_images:
                return {"erro": "Não foi possível converter PDF para imagens", "sucesso": False}
            
            # Processa primeira página com Textract
            print("Extraindo texto com AWS Textract...")
            textract_result = self.textract_ocr.extract_text_from_bytes(page_images[0])
            text = textract_result['text']
            
            if not text:
                return {"erro": "Não foi possível extrair texto do PDF", "sucesso": False}
            
            print("Analisando formulários estruturados...")
            forms_result = self.textract_ocr.analyze_document_forms(page_images[0])
            
            # Identifica tipo de documento
            doc_type = self.identify_document_type(text)
            print(f"Tipo de documento identificado: {doc_type or 'Não identificado'}")
            
            # Extrai informações usando ambas as abordagens
            info_text = self.extract_information_from_text(text)
            info_forms = self.extract_information_from_forms(forms_result['key_value_pairs'])
            
            # Combina resultados (prioriza formulários estruturados)
            info = {}
            for field in ['nome', 'cpf', 'rg']:
                info[field] = info_forms.get(field) or info_text.get(field, '')
            
            print(f"Informações extraídas: {info}")
            
            # Valida CPF
            cpf_valido = False
            if info['cpf']:
                cpf_valido = CPFValidator.validate_cpf(info['cpf'])
                print(f"CPF válido: {cpf_valido}")
            
            # Extrai imagens e procura por foto
            embedded_images = self.extract_images_from_pdf(pdf_path)
            photo_path = None
            
            if embedded_images:
                photo = self.detect_face_in_images(embedded_images)
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
                "rg": info['rg'],
                "cpf_valido": cpf_valido,
                "foto_extraida": photo_path,
                "texto_completo": text,
                "campos_estruturados": forms_result['key_value_pairs'],
                "sucesso": True
            }
            
            return resultado
            
        except Exception as e:
            error_msg = f"Erro durante o processamento: {str(e)}"
            self.logger.error(error_msg)
            return {"erro": error_msg, "sucesso": False}

def main():
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Processador de Documentos Pessoais com AWS Textract')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='.', help='Diretório de saída (padrão: diretório atual)')
    parser.add_argument('-r', '--region', default='us-east-1', help='Região AWS (padrão: us-east-1)')
    parser.add_argument('--debug', action='store_true', help='Ativar modo debug')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        processor = DocumentProcessorTextract(region_name=args.region)
        resultado = processor.process_document(args.pdf_path, args.output)
        
        if not resultado.get("sucesso", False):
            print(f"ERRO: {resultado.get('erro', 'Erro desconhecido')}")
            sys.exit(1)
        
        print("\n" + "="*60)
        print("RESULTADO DO PROCESSAMENTO COM AWS TEXTRACT")
        print("="*60)
        print(f"Tipo de Documento: {resultado['tipo_documento'] or 'Não identificado'}")
        print(f"Nome: {resultado['nome'] or 'Não encontrado'}")
        print(f"CPF: {resultado['cpf'] or 'Não encontrado'}")
        print(f"RG: {resultado['rg'] or 'Não encontrado'}")
        print(f"CPF Válido: {'Sim' if resultado['cpf_valido'] else 'Não'}")
        print(f"Foto Extraída: {resultado['foto_extraida'] or 'Não encontrada'}")
        
        if args.debug and resultado.get('campos_estruturados'):
            print(f"\nCampos Estruturados Detectados:")
            for key, value in resultado['campos_estruturados'].items():
                print(f"  {key}: {value}")
        
        print("="*60)
        
    except Exception as e:
        print(f"ERRO FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
