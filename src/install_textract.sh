#!/bin/bash

echo "=== Instalação do Processador de Documentos com AWS Textract ==="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não está instalado"
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "Instalando pip..."
    sudo yum install -y python3-pip
fi

# Instalar dependências Python
echo "Instalando dependências Python..."
pip3 install -r requirements_textract.txt

# Verificar se AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "AWS CLI não encontrado. Instalando..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Verificar configuração AWS
echo "Verificando configuração AWS..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "AVISO: Credenciais AWS não configuradas ou inválidas"
    echo "Execute 'aws configure' para configurar suas credenciais"
    echo "Ou configure as variáveis de ambiente:"
    echo "  export AWS_ACCESS_KEY_ID=sua_access_key"
    echo "  export AWS_SECRET_ACCESS_KEY=sua_secret_key"
    echo "  export AWS_DEFAULT_REGION=us-east-1"
else
    echo "Credenciais AWS configuradas com sucesso!"
fi

# Tornar o script executável
chmod +x document_processor_textract.py

echo ""
echo "=== Instalação Concluída ==="
echo ""
echo "Para usar o processador:"
echo "  ./document_processor_textract.py documento.pdf"
echo ""
echo "Para especificar diretório de saída:"
echo "  ./document_processor_textract.py documento.pdf -o /caminho/saida"
echo ""
echo "Para usar região AWS específica:"
echo "  ./document_processor_textract.py documento.pdf -r us-west-2"
echo ""
echo "Para modo debug:"
echo "  ./document_processor_textract.py documento.pdf --debug"
