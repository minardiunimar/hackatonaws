#!/usr/bin/env python3
"""
Script de teste para o processador de documentos com Textract
"""

import sys
import os
import logging
from document_processor_textract import DocumentProcessorTextract, CPFValidator

def test_cpf_validator():
    """Testa o validador de CPF"""
    print("=== Testando Validador de CPF ===")
    
    test_cases = [
        ("111.444.777-35", True),   # CPF válido
        ("111.111.111-11", False),  # CPF inválido (todos iguais)
        ("123.456.789-00", False),  # CPF inválido
        ("000.000.000-00", False),  # CPF inválido
        ("12345678901", False),     # CPF sem formatação inválido
    ]
    
    for cpf, expected in test_cases:
        result = CPFValidator.validate_cpf(cpf)
        status = "✓" if result == expected else "✗"
        print(f"{status} CPF {cpf}: {result} (esperado: {expected})")
    
    print()

def test_textract_connection():
    """Testa a conexão com o Textract"""
    print("=== Testando Conexão com AWS Textract ===")
    
    try:
        processor = DocumentProcessorTextract()
        print("✓ Cliente Textract inicializado com sucesso")
        print(f"✓ Região configurada: {processor.textract_ocr.region}")
        return True
    except Exception as e:
        print(f"✗ Erro ao inicializar Textract: {e}")
        print("  Verifique suas credenciais AWS:")
        print("  - aws configure")
        print("  - ou configure as variáveis de ambiente AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY")
        return False

def test_document_patterns():
    """Testa os padrões de identificação de documentos"""
    print("=== Testando Padrões de Documentos ===")
    
    processor = DocumentProcessorTextract()
    
    test_texts = {
        "RG": "REPÚBLICA FEDERATIVA DO BRASIL\nREGISTRO GERAL\nNome: João Silva\nCPF: 123.456.789-00",
        "CNH": "CARTEIRA NACIONAL DE HABILITAÇÃO\nCategoria: B\nNome: Maria Santos\nCPF: 987.654.321-00",
        "PASSAPORTE": "PASSAPORTE\nMINISTÉRIO DAS RELAÇÕES EXTERIORES\nNome: Pedro Costa\nTipo: P"
    }
    
    for expected_type, text in test_texts.items():
        detected_type = processor.identify_document_type(text)
        status = "✓" if detected_type == expected_type else "✗"
        print(f"{status} Texto de {expected_type}: detectado como {detected_type}")
    
    print()

def test_information_extraction():
    """Testa a extração de informações"""
    print("=== Testando Extração de Informações ===")
    
    processor = DocumentProcessorTextract()
    
    test_text = """
    REGISTRO GERAL
    Nome: JOÃO DA SILVA SANTOS
    CPF: 123.456.789-00
    RG: 12.345.678-9
    Data de Nascimento: 01/01/1990
    """
    
    info = processor.extract_information_from_text(test_text)
    
    print(f"Nome extraído: {info.get('nome', 'Não encontrado')}")
    print(f"CPF extraído: {info.get('cpf', 'Não encontrado')}")
    print(f"RG extraído: {info.get('rg', 'Não encontrado')}")
    
    # Validar CPF extraído
    if info.get('cpf'):
        cpf_valido = CPFValidator.validate_cpf(info['cpf'])
        print(f"CPF válido: {cpf_valido}")
    
    print()

def create_sample_pdf():
    """Cria um PDF de exemplo para teste"""
    print("=== Criando PDF de Exemplo ===")
    
    try:
        import fitz  # PyMuPDF
        
        # Criar um documento PDF simples
        doc = fitz.open()
        page = doc.new_page()
        
        # Adicionar texto de exemplo
        text = """REPÚBLICA FEDERATIVA DO BRASIL
REGISTRO GERAL

Nome: JOÃO DA SILVA SANTOS
CPF: 111.444.777-35
RG: 12.345.678-9
Data de Nascimento: 01/01/1990
Filiação: Maria Santos e José Santos
"""
        
        # Inserir texto na página
        page.insert_text((50, 100), text, fontsize=12)
        
        # Salvar PDF
        sample_path = "documento_exemplo.pdf"
        doc.save(sample_path)
        doc.close()
        
        print(f"✓ PDF de exemplo criado: {sample_path}")
        return sample_path
        
    except Exception as e:
        print(f"✗ Erro ao criar PDF de exemplo: {e}")
        return None

def main():
    """Função principal de teste"""
    print("TESTE DO PROCESSADOR DE DOCUMENTOS COM AWS TEXTRACT")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executar testes
    test_cpf_validator()
    
    textract_ok = test_textract_connection()
    
    test_document_patterns()
    test_information_extraction()
    
    # Teste com PDF real (se Textract estiver disponível)
    if textract_ok:
        sample_pdf = create_sample_pdf()
        if sample_pdf and os.path.exists(sample_pdf):
            print("=== Testando Processamento de PDF ===")
            try:
                processor = DocumentProcessorTextract()
                resultado = processor.process_document(sample_pdf)
                
                if resultado.get('sucesso'):
                    print("✓ PDF processado com sucesso!")
                    print(f"  Tipo: {resultado.get('tipo_documento', 'N/A')}")
                    print(f"  Nome: {resultado.get('nome', 'N/A')}")
                    print(f"  CPF: {resultado.get('cpf', 'N/A')}")
                    print(f"  CPF Válido: {resultado.get('cpf_valido', False)}")
                else:
                    print(f"✗ Erro no processamento: {resultado.get('erro', 'Erro desconhecido')}")
                
                # Limpar arquivo de teste
                if os.path.exists(sample_pdf):
                    os.remove(sample_pdf)
                    
            except Exception as e:
                print(f"✗ Erro durante teste de processamento: {e}")
    else:
        print("⚠ Pulando teste de processamento (Textract não disponível)")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    
    if textract_ok:
        print("\n✓ Sistema pronto para uso!")
        print("Execute: ./document_processor_textract.py seu_documento.pdf")
    else:
        print("\n⚠ Configure suas credenciais AWS antes de usar o sistema")

if __name__ == "__main__":
    main()
