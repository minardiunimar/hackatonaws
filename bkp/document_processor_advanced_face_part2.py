    def extract_text_with_textract(self, pdf_path: str) -> Tuple[str, Dict]:
        """Extrai texto usando AWS Textract"""
        if not self.textract_client:
            self.initialize_textract()
        
        try:
            with open(pdf_path, 'rb') as document:
                document_bytes = document.read()
            
            # Análise de texto simples
            response = self.textract_client.detect_document_text(
                Document={'Bytes': document_bytes}
            )
            
            # Extrai texto
            text = ""
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text += block['Text'] + '\n'
            
            # Análise de formulários estruturados
            try:
                form_response = self.textract_client.analyze_document(
                    Document={'Bytes': document_bytes},
                    FeatureTypes=['FORMS']
                )
                
                # Extrai campos estruturados
                structured_data = self.extract_structured_data(form_response)
                
            except Exception as e:
                self.logger.warning(f"Erro na análise de formulários: {e}")
                structured_data = {}
            
            return text, structured_data
            
        except ClientError as e:
            self.logger.error(f"Erro do Textract: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao processar documento: {e}")
            raise
    
    def extract_structured_data(self, response: Dict) -> Dict[str, str]:
        """Extrai dados estruturados da resposta do Textract"""
        structured_data = {}
        
        # Mapeia blocos por ID
        blocks = {block['Id']: block for block in response['Blocks']}
        
        # Processa pares chave-valor
        for block in response['Blocks']:
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    # É uma chave
                    key_text = self.get_text_from_block(block, blocks)
                    
                    # Procura o valor correspondente
                    if 'Relationships' in block:
                        for relationship in block['Relationships']:
                            if relationship['Type'] == 'VALUE':
                                for value_id in relationship['Ids']:
                                    if value_id in blocks:
                                        value_block = blocks[value_id]
                                        value_text = self.get_text_from_block(value_block, blocks)
                                        
                                        # Limpa e armazena
                                        clean_key = re.sub(r'[:\s]+$', '', key_text.lower().strip())
                                        structured_data[clean_key] = value_text.strip()
        
        return structured_data
    
    def get_text_from_block(self, block: Dict, blocks: Dict) -> str:
        """Extrai texto de um bloco"""
        text = ""
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        if child_id in blocks:
                            child_block = blocks[child_id]
                            if child_block['BlockType'] == 'WORD':
                                text += child_block['Text'] + ' '
        return text.strip()
    
    def resize_image_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Redimensiona imagem se for muito grande"""
        if image is None or image.size == 0:
            return image
            
        height, width = image.shape[:2]
        max_dimension = max(height, width)
        
        if max_dimension > self.max_image_size:
            scale = self.max_image_size / max_dimension
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            self.logger.info(f"Imagem redimensionada de {width}x{height} para {new_width}x{new_height}")
            return resized
        
        return image
    
    def extract_images_from_pdf(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai imagens embutidas do PDF"""
        images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 5)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.width * pix.height > 4000000:
                            self.logger.warning(f"Imagem muito grande ignorada: {pix.width}x{pix.height}")
                            pix = None
                            continue
                        
                        if pix.n - pix.alpha < 4:
                            img_data = pix.tobytes("png")
                            nparr = np.frombuffer(img_data, np.uint8)
                            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            
                            if cv_img is not None and cv_img.shape[0] > 50 and cv_img.shape[1] > 50:
                                cv_img = self.resize_image_if_needed(cv_img)
                                images.append(cv_img)
                        
                        pix = None
                        
                        if len(images) >= 10:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair imagem {img_index} da página {page_num}: {e}")
                        continue
                
                gc.collect()
                
                if len(images) >= 10:
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagens do PDF: {e}")
        finally:
            if doc:
                doc.close()
        
        return images
    
    def extract_full_page_images(self, pdf_path: str) -> List[np.ndarray]:
        """
        Extrai imagens completas das páginas do documento
        Usado como fallback quando não encontra rostos
        """
        page_images = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            self.logger.info(f"Extraindo imagens completas de {min(len(doc), 3)} páginas")
            
            for page_num in range(min(len(doc), 3)):  # Máximo 3 páginas
                page = doc.load_page(page_num)
                
                # Renderiza com resolução moderada
                mat = fitz.Matrix(1.2, 1.2)  # Resolução menor para economizar memória
                pix = page.get_pixmap(matrix=mat)
                
                if pix.width * pix.height > 8000000:  # Máximo 8MP para páginas completas
                    self.logger.warning(f"Página {page_num} muito grande, reduzindo resolução")
                    mat = fitz.Matrix(0.8, 0.8)  # Resolução ainda menor
                    pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if cv_img is not None:
                    # Redimensiona se necessário
                    cv_img = self.resize_image_if_needed(cv_img)
                    
                    # Aplica crop inteligente para remover bordas excessivas
                    cropped_page = self.smart_crop_page(cv_img)
                    if cropped_page is not None:
                        page_images.append(cropped_page)
                    else:
                        page_images.append(cv_img)
                
                pix = None
                cv_img = None
                gc.collect()
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair páginas completas: {e}")
        finally:
            if doc:
                doc.close()
        
        return page_images
    
    def smart_crop_page(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Aplica crop inteligente na página para remover bordas desnecessárias
        """
        try:
            # Converte para escala de cinza
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Aplica threshold para encontrar conteúdo
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
            
            # Encontra contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Encontra o maior contorno (conteúdo principal)
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Adiciona margem de 5%
                margin_x = int(w * 0.05)
                margin_y = int(h * 0.05)
                
                x = max(0, x - margin_x)
                y = max(0, y - margin_y)
                w = min(image.shape[1] - x, w + 2 * margin_x)
                h = min(image.shape[0] - y, h + 2 * margin_y)
                
                # Crop a região
                cropped = image[y:y+h, x:x+w]
                
                # Redimensiona para tamanho padrão mantendo proporção
                target_height = 600
                aspect_ratio = w / h
                target_width = int(target_height * aspect_ratio)
                
                if target_width > 800:  # Limita largura máxima
                    target_width = 800
                    target_height = int(target_width / aspect_ratio)
                
                resized = cv2.resize(cropped, (target_width, target_height), interpolation=cv2.INTER_AREA)
                return resized
            
        except Exception as e:
            self.logger.warning(f"Erro no crop inteligente: {e}")
        
        return None
    
    def detect_faces_advanced(self, images: List[np.ndarray]) -> List[Tuple[np.ndarray, str, float]]:
        """
        Detecta faces usando métodos avançados
        Returns: Lista de (face_image, detection_method, confidence_score)
        """
        all_faces = []
        
        for img_idx, img in enumerate(images):
            if img is None or img.size == 0:
                continue
            
            self.logger.info(f"Analisando imagem {img_idx + 1}/{len(images)} para detecção de faces")
            
            # Cria versões melhoradas da imagem
            enhanced_images = self.face_detector.enhance_image_for_detection(img)
            
            for enh_idx, enhanced_img in enumerate(enhanced_images):
                # Detecta faces com múltiplos métodos
                faces = self.face_detector.detect_faces_multiple_methods(enhanced_img)
                
                for face_data in faces:
                    x, y, w, h, method = face_data
                    
                    # Calcula score de confiança baseado no tamanho e método
                    face_area = w * h
                    confidence = face_area / (enhanced_img.shape[0] * enhanced_img.shape[1])
                    
                    # Bonus para métodos mais confiáveis
                    if method == 'frontal_default':
                        confidence *= 1.2
                    elif method == 'frontal_alt':
                        confidence *= 1.1
                    
                    # Bonus para imagem original (não melhorada)
                    if enh_idx == 0:
                        confidence *= 1.1
                    
                    # Extrai e processa a face
                    try:
                        face_region = self.crop_face_3x4(enhanced_img, x, y, w, h)
                        if face_region is not None:
                            detection_info = f"{method}_enh{enh_idx}"
                            all_faces.append((face_region, detection_info, confidence))
                    except Exception as e:
                        self.logger.warning(f"Erro ao extrair face: {e}")
                        continue
        
        # Ordena por confiança (maior primeiro)
        all_faces.sort(key=lambda x: x[2], reverse=True)
        
        self.logger.info(f"Total de faces detectadas: {len(all_faces)}")
        return all_faces
    
    def crop_face_3x4(self, image: np.ndarray, x: int, y: int, w: int, h: int) -> Optional[np.ndarray]:
        """Corta a imagem para formato 3x4 focando no rosto"""
        try:
            img_height, img_width = image.shape[:2]
            aspect_ratio = 3.0 / 4.0
            
            # Margens otimizadas
            top_margin = int(h * 0.3)
            bottom_margin = int(h * 0.2)
            side_margin = int(w * 0.1)
            
            # Calcular nova área expandida
            expanded_x = max(0, x - side_margin)
            expanded_y = max(0, y - top_margin)
            expanded_w = min(img_width - expanded_x, w + 2 * side_margin)
            expanded_h = min(img_height - expanded_y, h + top_margin + bottom_margin)
            
            # Ajustar para proporção 3x4
            current_ratio = expanded_w / expanded_h
            
            if current_ratio > aspect_ratio:
                new_width = int(expanded_h * aspect_ratio)
                width_diff = expanded_w - new_width
                expanded_x += width_diff // 2
                expanded_w = new_width
            else:
                new_height = int(expanded_w / aspect_ratio)
                height_diff = expanded_h - new_height
                expanded_y += height_diff // 2
                expanded_h = new_height
            
            # Garantir limites
            expanded_x = max(0, expanded_x)
            expanded_y = max(0, expanded_y)
            expanded_w = min(img_width - expanded_x, expanded_w)
            expanded_h = min(img_height - expanded_y, expanded_h)
            
            # Extrair região
            cropped_face = image[expanded_y:expanded_y + expanded_h, 
                               expanded_x:expanded_x + expanded_w]
            
            # Redimensionar para tamanho padrão
            if cropped_face.size > 0:
                resized_face = cv2.resize(cropped_face, (200, 267), interpolation=cv2.INTER_AREA)
                return resized_face
            
        except Exception as e:
            self.logger.error(f"Erro ao cortar face 3x4: {e}")
        
        return None
