# 🏆 HackatonAWS - Processador de Documentos Pessoais

[![AWS](https://img.shields.io/badge/AWS-Textract-orange)](https://aws.amazon.com/textract/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)](https://opencv.org)

Esta aplicação foi desenvolvida para o **Hackaton AWS** e processa documentos pessoais em PDF, identifica automaticamente o tipo de documento (RG, CNH, Passaporte), extrai informações importantes e valida CPF usando algoritmos oficiais.

## 🚀 Funcionalidades

- **🔍 Identificação Automática**: Detecta automaticamente se é RG, CNH ou Passaporte
- **📝 Extração de Informações**: Extrai nome e CPF do documento usando OCR e AWS Textract
- **✅ Validação de CPF**: Verifica se o CPF é válido usando o algoritmo oficial brasileiro
- **📸 Extração de Foto**: Detecta e extrai fotos/rostos do documento usando Computer Vision
- **☁️ Integração AWS**: Suporte completo ao Amazon Textract para OCR avançado
- **🔧 Múltiplas Versões**: Implementações básica, robusta e com AWS Textract

## 📁 Estrutura do Projeto

```
hackatonaws/
├── src/                          # Código fonte principal
│   ├── document_processor.py     # Versão principal
│   ├── document_processor_textract.py  # Versão com AWS Textract
│   ├── document_processor_robust.py    # Versão robusta
│   └── requirements*.txt         # Dependências
├── tests/                        # Testes e validações
├── docs/                         # Documentação completa
└── README.md                     # Este arquivo
```

## ⚡ Instalação Rápida

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/hackatonaws.git
cd hackatonaws
```

### 2. Instale as dependências
```bash
# Versão básica (OCR local)
pip install -r src/requirements.txt

# Versão com AWS Textract
pip install -r src/requirements_textract.txt
```

### 3. Configure o Tesseract OCR (Linux)
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-por

# CentOS/RHEL
sudo yum install tesseract tesseract-langpack-por
```

### 4. Configure AWS (para versão Textract)
```bash
aws configure
# Insira suas credenciais AWS
```

## ☁️ Integração AWS

### Amazon Textract
- **OCR Avançado**: Extração de texto com alta precisão
- **Detecção de Formulários**: Identificação automática de campos
- **Análise de Layout**: Compreensão da estrutura do documento

### Benefícios da Versão AWS
- ✅ Maior precisão na extração de texto
- ✅ Melhor detecção de CPF e informações pessoais
- ✅ Processamento em nuvem escalável
- ✅ Suporte a documentos de baixa qualidade

```python
# Exemplo de uso com Textract
from src.document_processor_textract import DocumentProcessorTextract

processor = DocumentProcessorTextract()
resultado = processor.process_document("documento.pdf", "output/")
```

## 🔧 Uso

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
