#!/usr/bin/env python3
"""
Processador de Documentos Pessoais usando AWS Textract - Versão Otimizada para Memória
Inclui detecção de fotos com controle de memória e crop 3x4
Otimizado para instâncias com pouca RAM
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

class DocumentProcessor:
    """Processador principal de documentos - Versão Otimizada"""
    
    def __init__(self, region='us-east-1'):
        self.region = region
        self.textract_client = None
        self.logger = logging.getLogger(__name__)
        
        # Configurações de memória
        self.max_image_size = 2048  # Máximo 2048x2048 pixels
        self.max_render_resolution = 1.5  # Reduzido de 2.0 para 1.5
        
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
        """Redimensiona imagem se for muito grande para economizar memória"""
        if image is None or image.size == 0:
            return image
            
        height, width = image.shape[:2]
        max_dimension = max(height, width)
        
        if max_dimension > self.max_image_size:
            # Calcula nova dimensão mantendo proporção
            scale = self.max_image_size / max_dimension
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Redimensiona com interpolação de alta qualidade
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            self.logger.info(f"Imagem redimensionada de {width}x{height} para {new_width}x{new_height}")
            return resized
        
        return image
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai imagens embutidas do PDF com controle de memória"""
        images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 5)):  # Limita a 5 páginas para economizar memória
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        # Verifica se a imagem não é muito grande
                        if pix.width * pix.height > 4000000:  # Máximo 4MP
                            self.logger.warning(f"Imagem muito grande ignorada: {pix.width}x{pix.height}")
                            pix = None
                            continue
                        
                        if pix.n - pix.alpha < 4:  # GRAY ou RGB
                            img_data = pix.tobytes("png")
                            nparr = np.frombuffer(img_data, np.uint8)
                            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if cv_img is not None and cv_img.shape[0] > 50 and cv_img.shape[1] > 50:
                                # Redimensiona se necessário
                                cv_img = self.resize_image_if_needed(cv_img)
                                images.append(cv_img)
                        
                        pix = None
                        
                        # Força limpeza de memória
                        if len(images) >= 10:  # Limita número de imagens
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair imagem {img_index} da página {page_num}: {e}")
                        continue
                
                # Força garbage collection a cada página
                gc.collect()
                
                if len(images) >= 10:  # Limita total de imagens
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagens do PDF: {e}")
        finally:
            if doc:
                doc.close()
        
        return images
    
    def extract_faces_from_rendered_pages(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai faces das páginas renderizadas do PDF com controle de memória"""
        faces = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            # Processa apenas as primeiras 3 páginas para economizar memória
            for page_num in range(min(len(doc), 3)):
                page = doc.load_page(page_num)
                
                # Renderiza com resolução reduzida
                mat = fitz.Matrix(self.max_render_resolution, self.max_render_resolution)
                pix = page.get_pixmap(matrix=mat)
                
                # Verifica tamanho antes de processar
                if pix.width * pix.height > 6000000:  # Máximo 6MP para páginas renderizadas
                    self.logger.warning(f"Página {page_num} muito grande, pulando: {pix.width}x{pix.height}")
                    pix = None
                    continue
                
                img_data = pix.tobytes("png")
                
                # Converte para OpenCV
                nparr = np.frombuffer(img_data, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if cv_img is not None:
                    # Redimensiona se necessário
                    cv_img = self.resize_image_if_needed(cv_img)
                    
                    # Detecta faces na página renderizada
                    detected_faces = self.detect_faces_in_image(cv_img)
                    faces.extend(detected_faces)
                
                pix = None
                cv_img = None
                
                # Força limpeza de memória
                gc.collect()
                
                if len(faces) >= 5:  # Limita número de faces
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair faces das páginas renderizadas: {e}")
        finally:
            if doc:
                doc.close()
        
        return faces
    
    def detect_faces_in_image(self, image: np.ndarray) -> List[np.ndarray]:
        """Detecta e extrai faces de uma imagem com controle de memória"""
        faces = []
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detecta faces
            detected_faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(50, 50))
            
            for (x, y, w, h) in detected_faces:
                # Extrai a região da face com crop 3x4
                face_region = self.crop_face_3x4(image, x, y, w, h)
                if face_region is not None:
                    faces.append(face_region)
                
                # Limita número de faces por imagem
                if len(faces) >= 3:
                    break
        
        except Exception as e:
            self.logger.error(f"Erro ao detectar faces: {e}")
        
        return faces
    
    def crop_face_3x4(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> Optional[np.ndarray]:
        """
        Corta a imagem para formato 3x4 focando no rosto
        Versão otimizada para memória
        """
        try:
            img_height, img_width = image.shape[:2]
            
            # Proporção 3x4 (largura:altura = 3:4)
            aspect_ratio = 3.0 / 4.0
            
            # Expandir a área da face (margens reduzidas para economizar memória)
            top_margin = int(h * 0.3)      # Reduzido de 0.4 para 0.3
            bottom_margin = int(h * 0.2)   # Reduzido de 0.3 para 0.2
            side_margin = int(w * 0.1)     # Reduzido de 0.15 para 0.1
            
            # Calcular nova área expandida
            expanded_x = max(0, x - side_margin)
            expanded_y = max(0, y - top_margin)
            expanded_w = min(img_width - expanded_x, w + 2 * side_margin)
            expanded_h = min(img_height - expanded_y, h + top_margin + bottom_margin)
            
            # Ajustar para proporção 3x4
            current_ratio = expanded_w / expanded_h
            
            if current_ratio > aspect_ratio:
                # Muito largo, ajustar largura
                new_width = int(expanded_h * aspect_ratio)
                width_diff = expanded_w - new_width
                expanded_x += width_diff // 2
                expanded_w = new_width
            else:
                # Muito alto, ajustar altura
                new_height = int(expanded_w / aspect_ratio)
                height_diff = expanded_h - new_height
                expanded_y += height_diff // 2
                expanded_h = new_height
            
            # Garantir que não saia dos limites da imagem
            expanded_x = max(0, expanded_x)
            expanded_y = max(0, expanded_y)
            expanded_w = min(img_width - expanded_x, expanded_w)
            expanded_h = min(img_height - expanded_y, expanded_h)
            
            # Extrair a região
            cropped_face = image[expanded_y:expanded_y + expanded_h, 
                               expanded_x:expanded_x + expanded_w]
            
            # Redimensionar para tamanho menor (200x267 ao invés de 300x400)
            if cropped_face.size > 0:
                resized_face = cv2.resize(cropped_face, (200, 267), interpolation=cv2.INTER_AREA)
                return resized_face
            
        except Exception as e:
            self.logger.error(f"Erro ao cortar face 3x4: {e}")
        
        return None
    
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
            
            try:
                # Converte para escala de cinza se necessário
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
                
                # Detecta faces
                faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
                
                if len(faces) > 0:
                    # Pega a maior face detectada
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    x, y, w, h = largest_face
                    
                    # Calcula score baseado no tamanho da face
                    face_area = w * h
                    score = face_area
                    
                    if score > best_score:
                        best_score = score
                        # Aplica crop 3x4 na melhor face
                        cropped_face = self.crop_face_3x4(img, x, y, w, h)
                        if cropped_face is not None:
                            best_photo = cropped_face
            
            except Exception as e:
                self.logger.warning(f"Erro ao processar imagem: {e}")
                continue
        
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
        info = {}
        
        for field, patterns in self.info_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if field == 'cpf':
                        # Limpa e formata CPF
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
        """Processa um documento PDF completo com controle de memória"""
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
            
            print(f"Informações extraídas: {extracted_info}")
            
            # Valida CPF
            cpf_valid = False
            if extracted_info.get('cpf'):
                cpf_valid = CPFValidator.validate_cpf(extracted_info['cpf'])
            print(f"CPF válido: {cpf_valid}")
            
            # Extrai fotos com controle de memória
            print("Procurando fotos (modo otimizado)...")
            photo_path = None
            
            try:
                # Primeiro tenta imagens embutidas
                embedded_images = self.extract_images_from_pdf(pdf_path)
                best_photo = self.detect_best_photo(embedded_images)
                
                # Limpa memória
                embedded_images = None
                gc.collect()
                
                # Se não encontrar, tenta páginas renderizadas
                if best_photo is None:
                    print("Procurando faces nas páginas renderizadas...")
                    rendered_faces = self.extract_faces_from_rendered_pages(pdf_path)
                    best_photo = self.detect_best_photo(rendered_faces)
                    
                    # Limpa memória
                    rendered_faces = None
                    gc.collect()
                
                if best_photo is not None:
                    photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                    photo_path = os.path.join(output_dir, photo_filename)
                    
                    if self.save_photo(best_photo, photo_path):
                        print(f"Foto 3x4 otimizada salva em: {photo_path}")
                    else:
                        photo_path = None
                else:
                    print("Nenhuma foto com rosto detectada")
                    
            except Exception as photo_error:
                self.logger.error(f"Erro no processamento de fotos: {photo_error}")
                print("Erro ao processar fotos, continuando sem foto...")
            
            # Força limpeza final de memória
            gc.collect()
            
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
    """Função principal para uso via linha de comando"""
    parser = argparse.ArgumentParser(description='Processador de Documentos Pessoais Otimizado')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='./', help='Diretório de saída (padrão: ./)')
    parser.add_argument('-r', '--region', default='us-east-1', help='Região AWS (padrão: us-east-1)')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Processar documento
    processor = DocumentProcessor(region=args.region)
    result = processor.process_document(args.pdf_path, args.output)
    
    # Exibir resultado
    print("\n" + "="*50)
    print("RESULTADO DO PROCESSAMENTO")
    print("="*50)
    print(f"Tipo de Documento: {result['tipo_documento']}")
    print(f"Nome: {result['nome']}")
    print(f"CPF: {result['cpf']}")
    print(f"RG: {result['rg']}")
    print(f"CPF Válido: {'Sim' if result['cpf_valido'] else 'Não'}")
    print(f"Foto 3x4 Extraída: {result['foto_extraida'] or 'Não encontrada'}")
    print(f"Campos Estruturados: {len(result.get('campos_estruturados', {}))}")
    print("="*50)

if __name__ == "__main__":
    main()
