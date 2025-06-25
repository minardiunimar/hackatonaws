#!/usr/bin/env python3
"""
Frontend Web Real para Processador de Documentos Pessoais
Integração completa com processamento real de PDFs
"""

import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging

# Adicionar o diretório atual ao path para importar o processador
sys.path.append('/opt/document-processor')

try:
    from document_processor import DocumentProcessor
except ImportError as e:
    logging.error(f"Erro ao importar DocumentProcessor: {e}")
    DocumentProcessor = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuração de diretórios
UPLOAD_FOLDER = '/opt/document-processor/uploads'
OUTPUT_FOLDER = '/opt/document-processor/output'
ALLOWED_EXTENSIONS = {'pdf'}

# Criar diretórios se não existirem
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_result(result):
    """Sanitiza o resultado removendo informações sensíveis para exibição"""
    if not result or not isinstance(result, dict):
        return result
    
    sanitized = result.copy()
    
    # Substitui informações pessoais por placeholders para demonstração
    if 'nome' in sanitized and sanitized['nome'] and sanitized['nome'] != 'Não encontrado':
        sanitized['nome_original'] = sanitized['nome']  # Manter original para logs
        sanitized['nome'] = '<NOME_COMPLETO>'
    
    if 'cpf' in sanitized and sanitized['cpf'] and sanitized['cpf'] != 'Não encontrado':
        sanitized['cpf_original'] = sanitized['cpf']  # Manter original para logs
        sanitized['cpf'] = '<XXX.XXX.XXX-XX>'
    
    return sanitized

@app.route('/')
def index():
    """Página principal"""
    return render_template('index_real.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para upload e processamento real de arquivo"""
    try:
        # Verificar se o processador está disponível
        if DocumentProcessor is None:
            return jsonify({'error': 'Processador de documentos não disponível. Verifique as dependências.'}), 500
        
        # Verificar se foi enviado um arquivo
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Apenas arquivos PDF são permitidos'}), 400
        
        # Gerar nome único para o arquivo
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
        
        # Salvar arquivo
        file.save(file_path)
        logger.info(f"Arquivo salvo: {file_path}")
        
        # Processar documento REAL
        processor = DocumentProcessor()
        output_dir = os.path.join(OUTPUT_FOLDER, unique_id)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Iniciando processamento real do documento: {filename}")
        result = processor.process_document(file_path, output_dir)
        logger.info(f"Resultado do processamento: {result}")
        
        # Sanitizar resultado para exibição
        display_result = sanitize_result(result)
        
        # Adicionar informações extras
        display_result['upload_id'] = unique_id
        display_result['filename'] = filename
        display_result['timestamp'] = datetime.now().isoformat()
        display_result['processing_type'] = 'real'
        
        # Verificar se há foto extraída
        if result.get('foto_extraida') and os.path.exists(result['foto_extraida']):
            # Copiar foto para diretório de output com nome padronizado
            photo_filename = f"foto_{unique_id}.jpg"
            photo_path = os.path.join(output_dir, photo_filename)
            
            if result['foto_extraida'] != photo_path:
                import shutil
                try:
                    shutil.copy2(result['foto_extraida'], photo_path)
                    display_result['foto_url'] = f"/download_photo/{unique_id}/{photo_filename}"
                    logger.info(f"Foto copiada para: {photo_path}")
                except Exception as e:
                    logger.error(f"Erro ao copiar foto: {e}")
            else:
                display_result['foto_url'] = f"/download_photo/{unique_id}/{photo_filename}"
        
        # Limpar arquivo original após processamento
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo original: {e}")
        
        logger.info(f"Processamento real concluído para {filename}")
        return jsonify(display_result)
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'Arquivo muito grande. Tamanho máximo: 16MB'}), 413
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return jsonify({'error': f'Erro no processamento: {str(e)}'}), 500

@app.route('/download_photo/<upload_id>/<filename>')
def download_photo(upload_id, filename):
    """Endpoint para download de fotos extraídas"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, upload_id, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=False)
        else:
            return jsonify({'error': 'Foto não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro no download da foto: {str(e)}")
        return jsonify({'error': 'Erro no download da foto'}), 500

@app.route('/health')
def health_check():
    """Endpoint de health check para AWS"""
    processor_status = "available" if DocumentProcessor is not None else "unavailable"
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'processor_status': processor_status
    })

@app.route('/test_processor')
def test_processor():
    """Endpoint para testar o processador"""
    try:
        if DocumentProcessor is None:
            return jsonify({'error': 'DocumentProcessor não disponível'})
        
        # Testar importação e inicialização
        processor = DocumentProcessor()
        return jsonify({
            'status': 'success',
            'message': 'Processador inicializado com sucesso',
            'processor_class': str(type(processor))
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro ao testar processador: {str(e)}'
        })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Arquivo muito grande. Tamanho máximo: 16MB'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Configuração para desenvolvimento
    app.run(debug=False, host='0.0.0.0', port=5000)
