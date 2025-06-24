# Processador de Documentos Pessoais com AWS Textract

Esta aplicação processa documentos pessoais em PDF usando AWS Textract, identifica o tipo de documento (RG, CNH, Passaporte), extrai informações importantes e valida CPF com maior precisão que a versão baseada em Tesseract.

## Principais Vantagens sobre a Versão Original

- ✅ **Maior precisão OCR**: AWS Textract oferece reconhecimento de texto superior
- ✅ **Detecção de formulários estruturados**: Identifica automaticamente pares chave-valor
- ✅ **Análise de layout avançada**: Compreende a estrutura do documento
- ✅ **Sem dependências locais de OCR**: Não requer instalação do Tesseract
- ✅ **Processamento em nuvem**: Aproveita a infraestrutura AWS

## Funcionalidades

- **Identificação de Documento**: Detecta automaticamente se é RG, CNH ou Passaporte
- **Extração de Informações**: Extrai nome, CPF e RG do documento
- **Validação de CPF**: Verifica se o CPF é válido usando o algoritmo oficial
- **Extração de Foto**: Detecta e extrai fotos/rostos do documento
- **Análise de Formulários**: Identifica campos estruturados automaticamente

## Pré-requisitos

### 1. Conta AWS
- Conta AWS ativa
- Permissões para usar Amazon Textract
- Credenciais configuradas (Access Key + Secret Key)

### 2. Configuração de Credenciais
Escolha uma das opções:

**Opção A: AWS CLI**
```bash
aws configure
```

**Opção B: Variáveis de Ambiente**
```bash
export AWS_ACCESS_KEY_ID=sua_access_key
export AWS_SECRET_ACCESS_KEY=sua_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Opção C: IAM Role (para EC2)**
- Anexe uma IAM Role à instância EC2 com permissões Textract

### 3. Permissões IAM Necessárias
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText",
                "textract:AnalyzeDocument"
            ],
            "Resource": "*"
        }
    ]
}
```

## Instalação

### 1. Instalar Dependências
```bash
# Executar script de instalação
./install_textract.sh

# Ou instalar manualmente
pip3 install -r requirements_textract.txt
```

### 2. Verificar Instalação
```bash
./test_textract_processor.py
```

## Uso

### Linha de Comando

**Uso Básico:**
```bash
./document_processor_textract.py documento.pdf
```

**Com Diretório de Saída:**
```bash
./document_processor_textract.py documento.pdf -o /caminho/saida
```

**Região AWS Específica:**
```bash
./document_processor_textract.py documento.pdf -r us-west-2
```

**Modo Debug:**
```bash
./document_processor_textract.py documento.pdf --debug
```

### Uso Programático

```python
from document_processor_textract import DocumentProcessorTextract

# Inicializar processador
processor = DocumentProcessorTextract(region_name='us-east-1')

# Processar documento
resultado = processor.process_document("documento.pdf", "saida/")

# Verificar resultado
if resultado['sucesso']:
    print(f"Tipo: {resultado['tipo_documento']}")
    print(f"Nome: {resultado['nome']}")
    print(f"CPF: {resultado['cpf']}")
    print(f"RG: {resultado['rg']}")
    print(f"CPF Válido: {resultado['cpf_valido']}")
    print(f"Campos Estruturados: {resultado['campos_estruturados']}")
else:
    print(f"Erro: {resultado['erro']}")
```

## Estrutura do Resultado

A aplicação retorna um dicionário com as seguintes informações:

```python
{
    "tipo_documento": "RG|CNH|PASSAPORTE|None",
    "nome": "Nome extraído do documento",
    "cpf": "CPF extraído (com formatação)",
    "rg": "RG extraído",
    "cpf_valido": True/False,
    "foto_extraida": "caminho/para/foto.jpg ou None",
    "texto_completo": "Texto completo extraído pelo Textract",
    "campos_estruturados": {
        "chave1": "valor1",
        "chave2": "valor2"
    },
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
from document_processor_textract import CPFValidator

# CPF válido
print(CPFValidator.validate_cpf("111.444.777-35"))  # True

# CPF inválido
print(CPFValidator.validate_cpf("111.111.111-11"))  # False
```

## Tipos de Documento Suportados

### RG (Registro Geral)
- Identifica por palavras-chave: "registro geral", "carteira de identidade"
- Extrai nome, CPF e RG

### CNH (Carteira Nacional de Habilitação)
- Identifica por: "carteira nacional de habilitação", "categoria"
- Extrai nome, CPF e número de registro

### Passaporte
- Identifica por: "passaporte", "ministério das relações exteriores"
- Extrai nome e CPF (quando disponível)

## Custos AWS Textract

### Preços (região us-east-1)
- **DetectDocumentText**: $0.0015 por página
- **AnalyzeDocument**: $0.05 por página

### Estimativa de Custos
- 100 documentos/mês: ~$5.15
- 1.000 documentos/mês: ~$51.50
- 10.000 documentos/mês: ~$515.00

*Preços podem variar por região. Consulte a calculadora AWS para estimativas precisas.*

## Limitações

- Textract tem limite de 10MB por documento
- Funciona melhor com documentos digitalizados em boa qualidade
- A detecção de faces requer que a foto esteja bem definida
- Alguns documentos podem ter layouts não padronizados

## Teste

Execute o script de teste para verificar a instalação:

```bash
python test_textract_processor.py
```

## Dependências

- **boto3**: SDK da AWS para Python
- **PyMuPDF**: Manipulação de arquivos PDF
- **OpenCV**: Processamento de imagens e detecção de faces
- **Pillow**: Manipulação de imagens
- **numpy**: Operações numéricas

## Segurança e Privacidade

- A aplicação envia documentos para AWS Textract (processamento em nuvem)
- Certifique-se de que isso está em conformidade com suas políticas de privacidade
- Substitua informações pessoais por placeholders em ambientes de produção
- Use com cuidado em documentos reais contendo dados sensíveis

## Exemplo de Saída

```
Processando documento: documento.pdf
Extraindo texto com AWS Textract...
Analisando formulários estruturados...
Tipo de documento identificado: RG
Informações extraídas: {'nome': 'Maria Silva Santos', 'cpf': '111.444.777-35', 'rg': '12.345.678-9'}
CPF válido: True

============================================================
RESULTADO DO PROCESSAMENTO COM AWS TEXTRACT
============================================================
Tipo de Documento: RG
Nome: Maria Silva Santos
CPF: 111.444.777-35
RG: 12.345.678-9
CPF Válido: Sim
Foto Extraída: Não encontrada

Campos Estruturados Detectados:
  nome:: MARIA SILVA SANTOS
  cpf:: 111.444.777-35
  data de nascimento:: 15/03/1985
============================================================
```

## Troubleshooting

### Erro: "Credenciais AWS não encontradas"
```bash
# Verificar configuração
aws sts get-caller-identity

# Reconfigurar se necessário
aws configure
```

### Erro: "Access Denied"
- Verificar permissões IAM
- Confirmar se a região está correta
- Verificar se o serviço Textract está disponível na região

### Erro: "Document too large"
- Textract tem limite de 10MB por documento
- Reduzir resolução do PDF se necessário
- Dividir documentos grandes em páginas menores

### Baixa Qualidade de Extração
- Aumentar DPI na conversão PDF→imagem (padrão: 200 DPI)
- Verificar qualidade do documento original
- Considerar pré-processamento da imagem

## Próximos Passos

1. Execute o teste: `./test_textract_processor.py`
2. Configure suas credenciais AWS
3. Teste com documentos reais
4. Compare resultados com versão original
5. Implemente em produção

Para dúvidas ou problemas, consulte a documentação oficial do AWS Textract ou abra uma issue no repositório do projeto.
