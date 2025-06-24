#!/usr/bin/env python3
"""
Processador de Documentos Pessoais usando AWS Textract - Versão Melhorada
Inclui detecção de fotos tanto em imagens embutidas quanto na página renderizada
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

class DocumentProcessor:
    """Processador principal de documentos"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.textract_client = None
        self.logger = logging.getLogger(__name__)
        
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
            ],
            'nis_pis_pasep': [
                r'nis[/\s]*pis[/\s]*pasep[:\s]*(\d+)',
                r'pis[/\s]*pasep[:\s]*(\d+)',
                r'nis[:\s]*(\d+)',
                r'pis[:\s]*(\d+)',
                r'pasep[:\s]*(\d+)'
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
            self.logger.error(f"Erro ao extrair imagens embutidas: {e}")
        
        return images
    
    def extract_faces_from_rendered_pages(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai faces das páginas renderizadas do PDF"""
        faces = []
        try:
            doc = fitz.open(pdf_path)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Renderiza a página em alta resolução
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom para melhor detecção
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                page_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if page_img is not None:
                    # Detecta faces na página
                    gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)
                    detected_faces = face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1, 
                        minNeighbors=4, 
                        minSize=(30, 30)
                    )
                    
                    # Extrai cada face detectada
                    for (x, y, w, h) in detected_faces:
                        # Adiciona margem ao redor da face
                        margin = 10
                        x = max(0, x - margin)
                        y = max(0, y - margin)
                        w = min(page_img.shape[1] - x, w + 2*margin)
                        h = min(page_img.shape[0] - y, h + 2*margin)
                        
                        face_img = page_img[y:y+h, x:x+w]
                        faces.append(face_img)
                        
                        self.logger.info(f"Face detectada na página {page_num + 1}: {w}x{h}")
                
                pix = None
            
            doc.close()
        except Exception as e:
            self.logger.error(f"Erro ao extrair faces das páginas renderizadas: {e}")
        
        return faces
    
    def detect_best_photo(self, images: List[np.ndarray]) -> Optional[np.ndarray]:
        """Detecta a melhor foto entre as imagens fornecidas"""
        if not images:
            return None
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        best_photo = None
        best_score = 0
        
        for img in images:
            if img is None or img.size == 0:
                continue
            
            # Converte para escala de cinza se necessário
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            
            # Detecta faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            
            if len(faces) > 0:
                # Calcula score baseado no tamanho da imagem e número de faces
                score = img.shape[0] * img.shape[1] * len(faces)
                
                if score > best_score:
                    best_score = score
                    best_photo = img
        
        return best_photo
    
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
        
        # Remove NIS/PIS/PASEP do texto temporariamente para extração de CPF
        text_without_nis = text
        for number in nis_pis_numbers:
            text_without_nis = text_without_nis.replace(number, '')
        
        # Extrai CPF (do texto sem NIS/PIS/PASEP)
        for pattern in self.info_patterns['cpf']:
            matches = re.findall(pattern, text_without_nis, re.IGNORECASE)
            for match in matches:
                # Limpa o CPF
                clean_cpf = re.sub(r'[^\d]', '', match)
                if len(clean_cpf) == 11 and CPFValidator.validate_cpf(clean_cpf):
                    # Formata o CPF
                    formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"
                    info['cpf'] = formatted_cpf
                    break
            if info['cpf']:
                break
        
        # Extrai nome
        for pattern in self.info_patterns['nome']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                clean_name = match.strip()
                if len(clean_name) > 5 and not re.search(r'\d', clean_name):
                    info['nome'] = clean_name.title()
                    break
            if info['nome']:
                break
        
        # Extrai RG
        for pattern in self.info_patterns['rg']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                clean_rg = match.strip()
                if len(clean_rg) > 5:
                    info['rg'] = clean_rg
                    break
            if info['rg']:
                break
        
        return info
    
    def process_document(self, pdf_path: str, output_dir: str = "./") -> Dict[str, Any]:
        """Processa um documento PDF completo"""
        try:
            self.logger.info(f"Processando documento: {pdf_path}")
            
            # Extrai texto com Textract
            print("Extraindo texto com AWS Textract...")
            text, structured_data = self.extract_text_with_textract(pdf_path)
            
            if structured_data:
                print("Analisando formulários estruturados...")
            
            # Identifica tipo de documento
            doc_type = self.identify_document_type(text)
            print(f"Tipo de documento identificado: {doc_type}")
            
            # Extrai informações do texto
            extracted_info = self.extract_information_from_text(text)
            
            # Combina informações estruturadas se disponíveis
            if structured_data:
                # Mapeia campos estruturados para nossas chaves
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
                                    # Valida CPF estruturado
                                    clean_cpf = re.sub(r'[^\d]', '', value)
                                    if len(clean_cpf) == 11 and CPFValidator.validate_cpf(clean_cpf):
                                        formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"
                                        extracted_info[our_key] = formatted_cpf
                                elif value:
                                    extracted_info[our_key] = value
                                break
            
            print(f"Informações extraídas: {extracted_info}")
            
            # Valida CPF
            cpf_valid = False
            if extracted_info.get('cpf'):
                cpf_valid = CPFValidator.validate_cpf(extracted_info['cpf'])
            print(f"CPF válido: {cpf_valid}")
            
            # Extrai fotos - primeiro tenta imagens embutidas
            embedded_images = self.extract_images_from_pdf(pdf_path)
            photo_path = None
            
            # Se não encontrar faces em imagens embutidas, tenta páginas renderizadas
            best_photo = self.detect_best_photo(embedded_images)
            if best_photo is None:
                print("Procurando faces nas páginas renderizadas...")
                rendered_faces = self.extract_faces_from_rendered_pages(pdf_path)
                best_photo = self.detect_best_photo(rendered_faces)
            
            if best_photo is not None:
                photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                photo_path = os.path.join(output_dir, photo_filename)
                
                if self.save_photo(best_photo, photo_path):
                    print(f"Foto salva em: {photo_path}")
                else:
                    photo_path = None
            
            # Monta resultado
            result = {
                'tipo_documento': doc_type,
                'nome': extracted_info.get('nome', ''),
                'cpf': extracted_info.get('cpf', ''),
                'rg': extracted_info.get('rg', ''),
                'cpf_valido': cpf_valid,
                'foto_extraida': photo_path,
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
                'sucesso': False,
                'erro': str(e)
            }

def main():
    parser = argparse.ArgumentParser(description='Processador de Documentos Pessoais com AWS Textract')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='./', help='Diretório de saída')
    parser.add_argument('-r', '--region', default='us-east-1', help='Região AWS')
    parser.add_argument('--debug', action='store_true', help='Ativar logs de debug')
    
    args = parser.parse_args()
    
    # Configura logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Verifica se o arquivo existe
    if not os.path.exists(args.pdf_path):
        print(f"Erro: Arquivo não encontrado: {args.pdf_path}")
        sys.exit(1)
    
    # Cria diretório de saída se não existir
    os.makedirs(args.output, exist_ok=True)
    
    # Processa documento
    processor = DocumentProcessor(region=args.region)
    result = processor.process_document(args.pdf_path, args.output)
    
    # Exibe resultado
    print("\n" + "="*60)
    print("RESULTADO DO PROCESSAMENTO COM AWS TEXTRACT")
    print("="*60)
    print(f"Tipo de Documento: {result['tipo_documento']}")
    print(f"Nome: {result['nome']}")
    print(f"CPF: {result['cpf']}")
    if result.get('rg'):
        print(f"RG: {result['rg']}")
    print(f"CPF Válido: {'Sim' if result['cpf_valido'] else 'Não'}")
    print(f"Foto Extraída: {result['foto_extraida'] if result['foto_extraida'] else 'Não encontrada'}")
    
    if result.get('campos_estruturados'):
        print(f"\nCampos Estruturados Detectados:")
        for key, value in result['campos_estruturados'].items():
            print(f"  {key}: {value}")
    
    print("="*60)
    
    if not result['sucesso']:
        print(f"Erro: {result.get('erro', 'Erro desconhecido')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
