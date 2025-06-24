# Guia de Migração: Tesseract → AWS Textract

## Resumo da Limpeza Realizada

Foram removidos com sucesso todos os pacotes relacionados ao tesseract e ferramentas de desenvolvimento:

### Pacotes Removidos:
- **Development Tools** (294 pacotes) - 451 MB liberados
- **cmake** e dependências - 31 MB liberados  
- **python3-devel** e ferramentas Python - 1.3 MB liberados

### Espaço Liberado Total: ~483 MB

## Implementação com AWS Textract

### 1. Vantagens do AWS Textract

✅ **Sem instalação local** - Serviço na nuvem
✅ **Alta precisão** - OCR otimizado pela AWS
✅ **Escalabilidade** - Processa milhares de documentos
✅ **Integração nativa** - Já está no ambiente AWS
✅ **Suporte a múltiplos formatos** - PDF, PNG, JPEG, TIFF

### 2. Configuração Necessária

#### Credenciais AWS
```bash
# Opção 1: Usar IAM Role (recomendado para EC2)
# A instância EC2 já deve ter uma role com permissões

# Opção 2: Configurar credenciais manualmente
aws configure
```

#### Permissões IAM Necessárias
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

### 3. Instalação de Dependências

```bash
# Instalar apenas as dependências necessárias
pip3 install boto3 PyMuPDF Pillow

# Verificar se já estão instaladas
pip3 list | grep -E "(boto3|PyMuPDF|Pillow)"
```

### 4. Migração do Código Existente

#### Antes (com tesseract):
```python
import pytesseract
from PIL import Image

def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang='por')
    return text
```

#### Depois (com Textract):
```python
import boto3

def extract_text(image_bytes):
    textract = boto3.client('textract')
    response = textract.detect_document_text(
        Document={'Bytes': image_bytes}
    )
    
    text_lines = []
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            text_lines.append(block['Text'])
    
    return '\n'.join(text_lines)
```

### 5. Exemplo de Integração Completa

O arquivo `textract_ocr_example.py` contém:

- ✅ Classe `TextractOCR` para substituir tesseract
- ✅ Classe `MockOCR` para testes sem AWS
- ✅ Classe `DocumentProcessorWithTextract` integrada
- ✅ Tratamento de erros e fallbacks
- ✅ Processamento de PDFs
- ✅ Extração de CPF e nome
- ✅ Validação básica de CPF

### 6. Custos do AWS Textract

**Preços (região us-east-1):**
- Primeiras 1.000 páginas/mês: **GRATUITAS**
- Páginas adicionais: ~$0.0015 por página
- Análise de formulários: ~$0.05 por página

### 7. Teste da Implementação

```bash
# Executar o exemplo
python3 textract_ocr_example.py

# Para testar com documento real:
# 1. Configure AWS credentials
# 2. Modifique o código para usar seu PDF
# 3. Execute: processor.process_document('seu_documento.pdf')
```

### 8. Modificações no Seu Projeto

Para integrar no seu processador de documentos existente:

1. **Substitua a importação do pytesseract:**
   ```python
   # from pytesseract import image_to_string
   from textract_ocr_example import get_ocr_engine
   ```

2. **Modifique a inicialização:**
   ```python
   def __init__(self):
       self.ocr = get_ocr_engine(use_textract=True)
   ```

3. **Atualize as chamadas de OCR:**
   ```python
   # Antes: text = pytesseract.image_to_string(image)
   # Depois: text = self.ocr.extract_text_from_image_bytes(image_bytes)
   ```

### 9. Benefícios da Migração

- 🚀 **Performance**: Textract é mais rápido que tesseract local
- 🎯 **Precisão**: Melhor reconhecimento de texto em português
- 🔧 **Manutenção**: Sem necessidade de instalar/manter tesseract
- 📈 **Escalabilidade**: Processa múltiplos documentos simultaneamente
- 💰 **Custo**: Tier gratuito para até 1.000 páginas/mês

### 10. Próximos Passos

1. ✅ Testar o exemplo com documentos reais
2. ✅ Configurar credenciais AWS adequadas
3. ✅ Integrar no seu código existente
4. ✅ Implementar tratamento de erros robusto
5. ✅ Considerar cache para reduzir custos
6. ✅ Monitorar uso e custos no AWS Console

## Suporte

Se encontrar problemas:
1. Verifique as credenciais AWS
2. Confirme as permissões IAM
3. Teste primeiro com MockOCR
4. Verifique logs de erro detalhados
