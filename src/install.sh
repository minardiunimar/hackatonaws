#!/bin/bash

echo "=== INSTALAÇÃO DO PROCESSADOR DE DOCUMENTOS ==="

# Verifica se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não encontrado. Instalando..."
    sudo yum update -y
    sudo yum install python3 python3-pip -y
fi

# Instala Tesseract OCR
echo "Instalando Tesseract OCR..."
sudo yum install tesseract -y

# Instala dependências Python
echo "Instalando dependências Python..."
pip3 install --user -r requirements.txt

echo ""
echo "=== INSTALAÇÃO CONCLUÍDA ==="
echo ""
echo "Para testar a instalação, execute:"
echo "python3 test_document_processor.py"
echo ""
echo "Para processar um documento, execute:"
echo "python3 document_processor.py caminho/para/documento.pdf"
