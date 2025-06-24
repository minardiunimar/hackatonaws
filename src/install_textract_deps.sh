#!/bin/bash

# Script para instalar dependências do AWS Textract
# Substitui a necessidade do tesseract

echo "=== Instalando dependências para AWS Textract ==="

# Verificar se pip3 está disponível
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instalando..."
    sudo dnf install -y python3-pip
fi

# Instalar dependências Python necessárias
echo "📦 Instalando dependências Python..."

# boto3 - SDK da AWS
if ! pip3 list | grep -q boto3; then
    echo "  Instalando boto3..."
    pip3 install --user boto3
else
    echo "  ✅ boto3 já instalado"
fi

# PyMuPDF - Para processamento de PDF
if ! pip3 list | grep -q PyMuPDF; then
    echo "  Instalando PyMuPDF..."
    pip3 install --user PyMuPDF
else
    echo "  ✅ PyMuPDF já instalado"
fi

# Pillow - Para processamento de imagens
if ! pip3 list | grep -q Pillow; then
    echo "  Instalando Pillow..."
    pip3 install --user Pillow
else
    echo "  ✅ Pillow já instalado"
fi

# Verificar instalação
echo ""
echo "🔍 Verificando instalação..."
python3 -c "
try:
    import boto3
    print('✅ boto3: OK')
except ImportError:
    print('❌ boto3: ERRO')

try:
    import fitz
    print('✅ PyMuPDF: OK')
except ImportError:
    print('❌ PyMuPDF: ERRO')

try:
    from PIL import Image
    print('✅ Pillow: OK')
except ImportError:
    print('❌ Pillow: ERRO')
"

echo ""
echo "🎉 Instalação concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Configure suas credenciais AWS:"
echo "   aws configure"
echo ""
echo "2. Ou use IAM Role (recomendado para EC2)"
echo ""
echo "3. Teste o exemplo:"
echo "   python3 textract_ocr_example.py"
echo ""
echo "4. Leia o guia completo:"
echo "   cat migration_guide.md"
