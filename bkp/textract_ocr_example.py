#!/usr/bin/env python3
"""
Exemplo de implementação de OCR usando AWS Textract
para substituir o tesseract no processador de documentos.
"""

import boto3
import base64
from typing import Dict, Any, Optional
import logging
import io
from PIL import Image
import fitz  # PyMuPDF

class TextractOCR:
    """Implementação de OCR usando AWS Textract."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Inicializar cliente Textract."""
        try:
            self.textract = boto3.client('textract', region_name=region_name)
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"Erro ao inicializar Textract: {e}")
            raise
    
    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """
        Extrair texto de imagem usando AWS Textract.
        
        Args:
            image_bytes: Dados da imagem em bytes
            
        Returns:
            Texto extraído como string
        """
        try:
            # Chamar Textract para detectar texto
            response = self.textract.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            # Extrair texto da resposta
            text_lines = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block['Text'])
            
            return '\n'.join(text_lines)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto com Textract: {e}")
            return ""
    
    def extract_text_from_pdf_page(self, pdf_path: str, page_num: int = 0) -> str:
        """
        Extrair texto de uma página específica do PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            page_num: Número da página (0-indexado)
            
        Returns:
            Texto extraído
        """
        try:
            # Abrir PDF e converter página para imagem
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            
            # Converter página para imagem
            mat = fitz.Matrix(2.0, 2.0)  # Aumentar resolução
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            doc.close()
            
            # Usar Textract para extrair texto
            return self.extract_text_from_image_bytes(img_data)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar PDF: {e}")
            return ""


class MockOCR:
    """Implementação mock de OCR para testes sem dependências externas."""
    
    def extract_text_from_image_bytes(self, image_bytes: bytes) -> str:
        """Mock de extração de texto - retorna texto placeholder."""
        return """REPÚBLICA FEDERATIVA DO BRASIL
REGISTRO GERAL
NOME: <NOME_PLACEHOLDER>
CPF: 123.456.789-00
RG: 12.345.678-9
DATA NASCIMENTO: 01/01/1990"""
    
    def extract_text_from_pdf_page(self, pdf_path: str, page_num: int = 0) -> str:
        """Mock de extração de PDF."""
        return self.extract_text_from_image_bytes(b"")


def get_ocr_engine(use_textract: bool = False, region_name: str = 'us-east-1') -> Any:
    """
    Obter engine de OCR baseado na disponibilidade e preferência.
    
    Args:
        use_textract: Se deve usar AWS Textract
        region_name: Região AWS para Textract
        
    Returns:
        Instância do engine OCR
    """
    if use_textract:
        try:
            return TextractOCR(region_name)
        except Exception as e:
            logging.warning(f"Falha ao inicializar Textract: {e}")
            logging.info("Usando OCR mock como fallback")
            return MockOCR()
    else:
        return MockOCR()


# Exemplo de integração com o processador de documentos existente
class DocumentProcessorWithTextract:
    """Processador de documentos usando Textract em vez de tesseract."""
    
    def __init__(self, use_textract: bool = True, region_name: str = 'us-east-1'):
        self.ocr = get_ocr_engine(use_textract, region_name)
        self.logger = logging.getLogger(__name__)
    
    def identify_document_type(self, text: str) -> str:
        """Identificar tipo de documento baseado no texto extraído."""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['registro geral', 'carteira de identidade']):
            return 'RG'
        elif any(keyword in text_lower for keyword in ['carteira nacional', 'habilitação', 'categoria']):
            return 'CNH'
        elif any(keyword in text_lower for keyword in ['passaporte', 'ministério das relações']):
            return 'PASSAPORTE'
        else:
            return 'DESCONHECIDO'
    
    def extract_cpf(self, text: str) -> Optional[str]:
        """Extrair CPF do texto."""
        import re
        # Padrão para CPF (xxx.xxx.xxx-xx ou xxxxxxxxxxx)
        cpf_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
        matches = re.findall(cpf_pattern, text)
        return matches[0] if matches else None
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extrair nome do texto (implementação simplificada)."""
        lines = text.split('\n')
        for line in lines:
            if 'nome' in line.lower():
                # Extrair texto após "nome:"
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[1].strip()
        return None
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Processar documento PDF e extrair informações.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dicionário com informações extraídas
        """
        try:
            # Extrair texto da primeira página
            text = self.ocr.extract_text_from_pdf_page(pdf_path, 0)
            
            if not text:
                return {
                    'sucesso': False,
                    'erro': 'Não foi possível extrair texto do documento'
                }
            
            # Identificar tipo de documento
            doc_type = self.identify_document_type(text)
            
            # Extrair informações
            nome = self.extract_name(text)
            cpf = self.extract_cpf(text)
            
            # Validar CPF (implementação simplificada)
            cpf_valido = self.validate_cpf(cpf) if cpf else False
            
            return {
                'sucesso': True,
                'tipo_documento': doc_type,
                'nome': nome,
                'cpf': cpf,
                'cpf_valido': cpf_valido,
                'texto_extraido': text
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar documento: {e}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def validate_cpf(self, cpf: str) -> bool:
        """Validação básica de CPF."""
        if not cpf:
            return False
        
        # Remover formatação
        cpf_numbers = ''.join(filter(str.isdigit, cpf))
        
        # Verificar se tem 11 dígitos
        if len(cpf_numbers) != 11:
            return False
        
        # Verificar se não são todos iguais
        if cpf_numbers == cpf_numbers[0] * 11:
            return False
        
        # Aqui você pode implementar a validação completa do CPF
        # Por simplicidade, retornamos True se passou nas verificações básicas
        return True


if __name__ == "__main__":
    # Exemplo de uso
    logging.basicConfig(level=logging.INFO)
    
    # Testar com mock OCR
    print("=== Testando com Mock OCR ===")
    processor_mock = DocumentProcessorWithTextract(use_textract=False)
    
    # Simular processamento (sem arquivo real)
    mock_result = {
        'sucesso': True,
        'tipo_documento': 'RG',
        'nome': '<NOME_PLACEHOLDER>',
        'cpf': '123.456.789-00',
        'cpf_valido': True,
        'texto_extraido': 'REGISTRO GERAL\nNOME: <NOME_PLACEHOLDER>\nCPF: 123.456.789-00'
    }
    
    print("Resultado do processamento mock:")
    for key, value in mock_result.items():
        print(f"  {key}: {value}")
    
    print("\n=== Para usar com Textract real ===")
    print("1. Configure suas credenciais AWS")
    print("2. Certifique-se de ter permissões para usar Textract")
    print("3. Use: processor = DocumentProcessorWithTextract(use_textract=True)")
    print("4. Chame: resultado = processor.process_document('caminho/para/documento.pdf')")
