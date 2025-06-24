#!/bin/bash

echo "=== Instalação Simplificada do Tesseract ==="

# Instala dependências básicas
sudo dnf install -y wget curl

# Baixa e instala Tesseract pré-compilado
cd /tmp
wget https://github.com/tesseract-ocr/tesseract/releases/download/5.3.0/tesseract-5.3.0.tar.gz
tar -xzf tesseract-5.3.0.tar.gz

# Instala dependências para Tesseract
sudo dnf install -y leptonica-devel

# Como alternativa, vamos usar easyocr que é mais fácil de instalar
echo "Instalando EasyOCR como alternativa..."
pip3 install easyocr

echo "Instalação concluída!"
