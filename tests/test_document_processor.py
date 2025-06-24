#!/usr/bin/env python3
"""
Script de teste para o processador de documentos
"""

from document_processor import DocumentProcessor, CPFValidator

def test_cpf_validator():
    """Testa o validador de CPF"""
    print("Testando validador de CPF...")
    
    # CPFs válidos para teste
    cpfs_validos = [
        "11144477735",
        "111.444.777-35",
        "12345678909",
        "123.456.789-09"
    ]
    
    # CPFs inválidos para teste
    cpfs_invalidos = [
        "11111111111",
        "12345678901",
        "000.000.000-00",
        "123.456.789-10"
    ]
    
    print("\nCPFs Válidos:")
    for cpf in cpfs_validos:
        resultado = CPFValidator.validate_cpf(cpf)
        print(f"  {cpf}: {'✓' if resultado else '✗'}")
    
    print("\nCPFs Inválidos:")
    for cpf in cpfs_invalidos:
        resultado = CPFValidator.validate_cpf(cpf)
        print(f"  {cpf}: {'✓' if resultado else '✗'}")

def create_sample_pdf():
    """Cria um PDF de exemplo para teste"""
    try:
        import fitz
        
        # Cria um documento PDF simples
        doc = fitz.open()
        page = doc.new_page()
        
        # Adiciona texto simulando um RG
        text = """
        REPÚBLICA FEDERATIVA DO BRASIL
        SECRETARIA DE SEGURANÇA PÚBLICA
        CARTEIRA DE IDENTIDADE
        
        Nome: <NOME_COMPLETO>
        CPF: <XXX.XXX.XXX-XX>
        RG: 12.345.678-9
        Data de Nascimento: 01/01/1990
        Filiação: <NOME_PAI> e <NOME_MAE>
        """
        
        page.insert_text((50, 100), text, fontsize=12)
        
        # Salva o PDF
        doc.save("/home/ec2-user/exemplo_rg.pdf")
        doc.close()
        
        print("PDF de exemplo criado: exemplo_rg.pdf")
        return True
        
    except Exception as e:
        print(f"Erro ao criar PDF de exemplo: {e}")
        return False

def main():
    print("=== TESTE DO PROCESSADOR DE DOCUMENTOS ===\n")
    
    # Testa validador de CPF
    test_cpf_validator()
    
    # Cria PDF de exemplo
    print("\n" + "="*50)
    create_sample_pdf()
    
    print("\n" + "="*50)
    print("Para testar com um PDF real, execute:")
    print("python document_processor.py caminho/para/seu/documento.pdf")
    print("\nPara instalar as dependências:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
