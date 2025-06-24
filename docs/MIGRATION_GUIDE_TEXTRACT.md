# Guia de Migração: Tesseract → AWS Textract

Este guia explica como migrar do processador de documentos baseado em Tesseract para a versão que usa AWS Textract.

## Principais Diferenças

### Versão Original (Tesseract)
- ✅ Processamento local
- ✅ Sem custos de API
- ❌ Menor precisão OCR
- ❌ Requer instalação do Tesseract
- ❌ Limitado para documentos complexos

### Nova Versão (AWS Textract)
- ✅ Maior precisão OCR
- ✅ Detecção de formulários estruturados
- ✅ Análise de layout avançada
- ✅ Sem dependências locais de OCR
- ❌ Requer credenciais AWS
- ❌ Custos por uso da API

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
    print(f"CPF Válido: {resultado['cpf_valido']}")
    print(f"Campos Estruturados: {resultado['campos_estruturados']}")
else:
    print(f"Erro: {resultado['erro']}")
```

## Novas Funcionalidades

### 1. Detecção de Formulários Estruturados
A nova versão pode identificar pares chave-valor em formulários:

```python
# Exemplo de campos estruturados detectados
{
    'nome': 'João da Silva',
    'cpf': '123.456.789-00',
    'data nascimento': '01/01/1990'
}
```

### 2. Maior Precisão na Extração
- Melhor reconhecimento de texto em documentos de baixa qualidade
- Detecção mais precisa de campos específicos
- Menos erros de OCR

### 3. Análise de Layout
- Compreensão da estrutura do documento
- Identificação automática de seções
- Melhor extração de informações contextuais

## Comparação de Resultados

### Estrutura do Resultado - Versão Original
```python
{
    "tipo_documento": "RG|CNH|PASSAPORTE|None",
    "nome": "Nome extraído",
    "cpf": "CPF extraído",
    "cpf_valido": True/False,
    "foto_extraida": "caminho/foto.jpg",
    "sucesso": True/False
}
```

### Estrutura do Resultado - Nova Versão
```python
{
    "tipo_documento": "RG|CNH|PASSAPORTE|None",
    "nome": "Nome extraído",
    "cpf": "CPF extraído",
    "rg": "RG extraído",  # NOVO
    "cpf_valido": True/False,
    "foto_extraida": "caminho/foto.jpg",
    "texto_completo": "Texto completo extraído",  # NOVO
    "campos_estruturados": {...},  # NOVO
    "sucesso": True/False
}
```

## Custos AWS Textract

### Preços (região us-east-1)
- **DetectDocumentText**: $0.0015 por página
- **AnalyzeDocument**: $0.05 por página

### Estimativa de Custos
- 100 documentos/mês: ~$5.15
- 1.000 documentos/mês: ~$51.50
- 10.000 documentos/mês: ~$515.00

*Preços podem variar por região. Consulte a calculadora AWS para estimativas precisas.*

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

## Migração Gradual

### Estratégia Recomendada

1. **Fase 1**: Instalar e testar nova versão
2. **Fase 2**: Executar ambas versões em paralelo
3. **Fase 3**: Comparar resultados e ajustar
4. **Fase 4**: Migrar completamente para Textract

### Script de Comparação
```python
# Comparar resultados das duas versões
from document_processor import DocumentProcessor  # Versão original
from document_processor_textract import DocumentProcessorTextract  # Nova versão

def compare_processors(pdf_path):
    # Processar com versão original
    processor_old = DocumentProcessor()
    result_old = processor_old.process_document(pdf_path)
    
    # Processar com Textract
    processor_new = DocumentProcessorTextract()
    result_new = processor_new.process_document(pdf_path)
    
    # Comparar resultados
    print("=== COMPARAÇÃO ===")
    print(f"Tesseract - Nome: {result_old.get('nome')}")
    print(f"Textract  - Nome: {result_new.get('nome')}")
    print(f"Tesseract - CPF: {result_old.get('cpf')}")
    print(f"Textract  - CPF: {result_new.get('cpf')}")
```

## Backup e Rollback

### Manter Versão Original
```bash
# Renomear versão original
mv document_processor.py document_processor_tesseract.py

# Manter ambas versões disponíveis
ls -la document_processor*
```

### Rollback Rápido
Se necessário voltar à versão original:
```bash
# Usar versão Tesseract
python document_processor_tesseract.py documento.pdf
```

## Suporte e Monitoramento

### Logs Detalhados
```bash
# Executar com debug para logs detalhados
./document_processor_textract.py documento.pdf --debug
```

### Monitoramento AWS
- CloudWatch para métricas de uso
- AWS Cost Explorer para custos
- CloudTrail para auditoria de chamadas

## Próximos Passos

1. Execute o teste: `./test_textract_processor.py`
2. Configure suas credenciais AWS
3. Teste com documentos reais
4. Compare resultados com versão original
5. Implemente em produção gradualmente

Para dúvidas ou problemas, consulte a documentação oficial do AWS Textract ou abra uma issue no repositório do projeto.
