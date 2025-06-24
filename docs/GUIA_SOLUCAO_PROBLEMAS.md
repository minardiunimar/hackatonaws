# Guia de Solução de Problemas - Processador de Documentos

## Erro: "Não foi possível extrair texto do PDF"

### Possíveis Causas e Soluções

#### 1. PDF Corrompido ou Inválido
**Sintomas:**
- Erro ao abrir o PDF
- Arquivo não pode ser lido

**Solução:**
```bash
# Verifique se o arquivo existe e tem tamanho válido
ls -la documento.pdf

# Use o diagnóstico
python3 diagnose_pdf.py documento.pdf
```

#### 2. PDF Baseado em Imagens (Sem Texto Extraível)
**Sintomas:**
- PDF abre normalmente
- Contém imagens mas pouco ou nenhum texto

**Solução:**
```bash
# Use o processador robusto que inclui OCR
python3 document_processor_robust.py documento.pdf

# Ou use o processador simplificado
python3 document_processor_simple.py documento.pdf
```

#### 3. PDF Criptografado/Protegido
**Sintomas:**
- Erro de permissão ao abrir
- PDF requer senha

**Solução:**
- Remova a proteção do PDF usando ferramentas como `qpdf`
- Ou obtenha a versão não protegida do documento

#### 4. Problemas de Encoding/Caracteres
**Sintomas:**
- Texto extraído com caracteres estranhos
- Acentos não aparecem corretamente

**Solução:**
- Use o processador robusto que trata melhor encoding
- Verifique se o PDF foi gerado corretamente

## Versões Disponíveis do Processador

### 1. document_processor.py (Original)
- Versão básica
- Pode falhar com PDFs complexos

### 2. document_processor_robust.py (Recomendado)
- Múltiplas estratégias de extração
- Inclui OCR para PDFs baseados em imagens
- Melhor tratamento de erros
- Logging detalhado

### 3. document_processor_simple.py (Sem OCR)
- Não requer Tesseract
- Funciona apenas com PDFs com texto extraível
- Mais rápido e leve

## Como Escolher a Versão Certa

### Use o Processador Robusto quando:
- PDF contém principalmente imagens
- Documento foi escaneado
- Texto não é extraível diretamente
- Precisa de máxima compatibilidade

### Use o Processador Simples quando:
- PDF tem texto extraível
- Quer processamento mais rápido
- Não quer instalar OCR
- Documento é digital (não escaneado)

## Comandos de Diagnóstico

### 1. Verificar Dependências
```bash
python3 diagnose_pdf.py documento.pdf
```

### 2. Testar Processamento
```bash
# Teste básico
python3 test_robust_processor.py

# Teste com arquivo específico
python3 document_processor_simple.py documento.pdf -v
```

### 3. Verificar Instalação
```bash
# Verificar se todas as bibliotecas estão instaladas
python3 -c "import fitz, cv2, numpy, PIL; print('Todas as dependências OK')"
```

## Soluções por Tipo de Erro

### Erro: "ModuleNotFoundError"
```bash
# Instalar dependências
pip3 install -r requirements.txt
```

### Erro: "tesseract is not installed"
```bash
# Use o processador simples (sem OCR)
python3 document_processor_simple.py documento.pdf

# Ou instale o Tesseract
sudo dnf install tesseract
```

### Erro: "PDF não encontrado"
```bash
# Verifique o caminho
ls -la /caminho/para/documento.pdf

# Use caminho absoluto
python3 document_processor_simple.py /home/ec2-user/documento.pdf
```

### Erro: "Nenhum texto encontrado"
```bash
# Use OCR (processador robusto)
python3 document_processor_robust.py documento.pdf

# Ou verifique se o PDF tem texto
python3 diagnose_pdf.py documento.pdf
```

## Melhorias de Performance

### Para PDFs Grandes
- Use o processador simples se possível
- Processe uma página por vez
- Aumente a memória disponível

### Para Múltiplos Documentos
```bash
# Processe em lote
for pdf in *.pdf; do
    echo "Processando $pdf"
    python3 document_processor_simple.py "$pdf" -o output/
done
```

## Logs e Debug

### Ativar Modo Verboso
```bash
python3 document_processor_simple.py documento.pdf -v
```

### Verificar Logs
- Logs aparecem no stderr
- Use `2>&1` para capturar em arquivo:
```bash
python3 document_processor_simple.py documento.pdf -v > resultado.txt 2>&1
```

## Limitações Conhecidas

### Processador Simples
- Não funciona com PDFs escaneados
- Requer texto extraível no PDF
- Limitado a documentos digitais

### Processador Robusto
- Mais lento devido ao OCR
- Requer mais memória
- Dependente do Tesseract

## Contato e Suporte

Se o problema persistir:
1. Execute o diagnóstico completo
2. Verifique os logs detalhados
3. Teste com diferentes versões do processador
4. Verifique se o PDF é válido em outros visualizadores

## Exemplos de Uso Bem-Sucedido

### Documento Digital (RG/CNH)
```bash
python3 document_processor_simple.py documento_digital.pdf
```

### Documento Escaneado
```bash
python3 document_processor_robust.py documento_escaneado.pdf
```

### Processamento em Lote
```bash
find . -name "*.pdf" -exec python3 document_processor_simple.py {} \;
```
