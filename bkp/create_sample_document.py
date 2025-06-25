#!/usr/bin/env python3
"""
Criar um documento de exemplo para testar o Textract
"""

from PIL import Image, ImageDraw, ImageFont
import io

def create_sample_document():
    """Criar uma imagem de documento de exemplo"""
    
    # Criar imagem branca
    width, height = 600, 400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Tentar usar fonte padrão
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # Texto do documento de exemplo
    lines = [
        "REPÚBLICA FEDERATIVA DO BRASIL",
        "REGISTRO GERAL",
        "",
        "NOME: JOÃO DA SILVA SANTOS",
        "CPF: 123.456.789-00",
        "RG: 12.345.678-9",
        "DATA NASCIMENTO: 15/03/1985",
        "",
        "DOCUMENTO DE EXEMPLO PARA TESTE"
    ]
    
    # Desenhar texto
    y_position = 50
    for line in lines:
        if line:  # Pular linhas vazias
            draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    # Salvar como PNG
    image.save('/home/ec2-user/sample_document.png')
    print("✅ Documento de exemplo criado: sample_document.png")
    
    # Retornar bytes da imagem para teste
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    return img_bytes.getvalue()

if __name__ == "__main__":
    create_sample_document()
