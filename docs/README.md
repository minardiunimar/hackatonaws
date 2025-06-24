# Processador de Documentos Pessoais

Esta aplicação processa documentos pessoais em PDF, identifica o tipo de documento (RG, CNH, Passaporte), extrai informações importantes e valida CPF.

## Funcionalidades

- **Identificação de Documento**: Detecta automaticamente se é RG, CNH ou Passaporte
- **Extração de Informações**: Extrai nome e CPF do documento
- **Validação de CPF**: Verifica se o CPF é válido usando o algoritmo oficial
- **Extração de Foto**: Detecta e extrai fotos/rostos do documento

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Para sistemas Linux, instale o Tesseract OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# CentOS/RHEL
sudo yum install tesseract
```

## Uso

### Linha de Comando

```bash
python document_processor.py caminho/para/documento.pdf
```

Com diretório de saída personalizado:
```bash
python document_processor.py documento.pdf -o /caminho/saida
```

### Exemplo de Uso Programático

```python
from document_processor import DocumentProcessor

processor = DocumentProcessor()
resultado = processor.process_document("documento.pdf", "saida/")

print(f"Tipo: {resultado['tipo_documento']}")
print(f"Nome: {resultado['nome']}")
print(f"CPF: {resultado['cpf']}")
print(f"CPF Válido: {resultado['cpf_valido']}")
print(f"Foto: {resultado['foto_extraida']}")
```

## Estrutura do Resultado

A aplicação retorna um dicionário com as seguintes informações:

```python
{
    "tipo_documento": "RG|CNH|PASSAPORTE|None",
    "nome": "Nome extraído do documento",
    "cpf": "CPF extraído (com formatação)",
    "cpf_valido": True/False,
    "foto_extraida": "caminho/para/foto.jpg ou None",
    "sucesso": True/False
}
```

## Validação de CPF

A aplicação inclui um validador de CPF que:
- Remove formatação (pontos e hífens)
- Verifica se tem 11 dígitos
- Valida usando o algoritmo oficial dos dígitos verificadores
- Rejeita CPFs com todos os dígitos iguais

### Exemplo de Validação

```python
from document_processor import CPFValidator

# CPF válido
print(CPFValidator.validate_cpf("111.444.777-35"))  # True

# CPF inválido
print(CPFValidator.validate_cpf("111.111.111-11"))  # False
```

## Tipos de Documento Suportados

### RG (Registro Geral)
- Identifica por palavras-chave: "registro geral", "carteira de identidade"
- Extrai nome e CPF

### CNH (Carteira Nacional de Habilitação)
- Identifica por: "carteira nacional de habilitação", "categoria"
- Extrai nome e CPF

### Passaporte
- Identifica por: "passaporte", "ministério das relações exteriores"
- Extrai nome e CPF (quando disponível)

## Limitações

- Funciona melhor com documentos digitalizados em boa qualidade
- A extração de texto depende da qualidade do PDF
- A detecção de faces requer que a foto esteja bem definida
- Alguns documentos podem ter layouts não padronizados

## Teste

Execute o script de teste para verificar a instalação:

```bash
python test_document_processor.py
```

## Dependências

- **PyMuPDF**: Manipulação de arquivos PDF
- **OpenCV**: Processamento de imagens e detecção de faces
- **Pillow**: Manipulação de imagens
- **pytesseract**: OCR (Optical Character Recognition)
- **numpy**: Operações numéricas

## Segurança e Privacidade

- A aplicação processa documentos localmente
- Não envia dados para serviços externos
- Substitua informações pessoais por placeholders em ambientes de produção
- Use com cuidado em documentos reais contendo dados sensíveis

## Exemplo de Saída

```
Processando documento: documento.pdf
Tipo de documento identificado: RG
Informações extraídas: {'nome': '<NOME_COMPLETO>', 'cpf': '<XXX.XXX.XXX-XX>'}
CPF válido: True
Foto salva em: ./foto_extraida_documento.pdf.jpg

==================================================
RESULTADO DO PROCESSAMENTO
==================================================
Tipo de Documento: RG
Nome: <NOME_COMPLETO>
CPF: <XXX.XXX.XXX-XX>
CPF Válido: Sim
Foto Extraída: ./foto_extraida_documento.pdf.jpg
==================================================
```
