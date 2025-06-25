    def detect_best_photo_or_fallback(self, images: List[np.ndarray], pdf_path: str) -> Tuple[Optional[np.ndarray], str]:
        """
        Detecta a melhor foto com rosto ou usa fallback para imagem completa
        Returns: (image, extraction_type)
        """
        extraction_type = "none"
        
        # Primeiro: tenta detectar rostos com métodos avançados
        print("🔍 Iniciando detecção avançada de rostos...")
        faces_detected = self.detect_faces_advanced(images)
        
        if faces_detected:
            best_face, method, confidence = faces_detected[0]
            print(f"✅ Melhor rosto detectado com {method} (confiança: {confidence:.3f})")
            return best_face, f"face_detected_{method}"
        
        print("⚠️  Nenhum rosto detectado em imagens embutidas")
        
        # Segundo: tenta detectar rostos em páginas renderizadas
        print("🔍 Procurando rostos em páginas renderizadas...")
        try:
            rendered_images = self.extract_faces_from_rendered_pages(pdf_path)
            if rendered_images:
                rendered_faces = self.detect_faces_advanced(rendered_images)
                if rendered_faces:
                    best_face, method, confidence = rendered_faces[0]
                    print(f"✅ Rosto encontrado em página renderizada com {method} (confiança: {confidence:.3f})")
                    return best_face, f"face_rendered_{method}"
            
            # Limpa memória
            rendered_images = None
            gc.collect()
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar páginas renderizadas: {e}")
        
        print("⚠️  Nenhum rosto detectado em páginas renderizadas")
        
        # Terceiro: fallback para imagem completa do documento
        print("📄 Extraindo imagem completa do documento como fallback...")
        try:
            page_images = self.extract_full_page_images(pdf_path)
            if page_images:
                # Seleciona a primeira página (geralmente a principal)
                best_page = page_images[0]
                print(f"✅ Imagem completa extraída: {best_page.shape[1]}x{best_page.shape[0]} pixels")
                return best_page, "full_document"
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair imagem completa: {e}")
        
        print("❌ Não foi possível extrair nenhuma imagem")
        return None, "none"
    
    def extract_faces_from_rendered_pages(self, pdf_path: str) -> List[np.ndarray]:
        """Extrai faces das páginas renderizadas"""
        faces = []
        doc = None
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(min(len(doc), 3)):
                page = doc.load_page(page_num)
                
                mat = fitz.Matrix(self.max_render_resolution, self.max_render_resolution)
                pix = page.get_pixmap(matrix=mat)
                
                if pix.width * pix.height > 6000000:
                    self.logger.warning(f"Página {page_num} muito grande, pulando")
                    pix = None
                    continue
                
                img_data = pix.tobytes("png")
                nparr = np.frombuffer(img_data, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if cv_img is not None:
                    cv_img = self.resize_image_if_needed(cv_img)
                    faces.append(cv_img)
                
                pix = None
                cv_img = None
                gc.collect()
                
                if len(faces) >= 3:
                    break
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair faces das páginas renderizadas: {e}")
        finally:
            if doc:
                doc.close()
        
        return faces
    
    def save_photo(self, photo: np.ndarray, output_path: str) -> bool:
        """Salva a foto extraída"""
        try:
            cv2.imwrite(output_path, photo)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar foto: {e}")
            return False
    
    def identify_document_type(self, text: str) -> Optional[str]:
        """Identifica o tipo de documento baseado no texto"""
        text = text.lower()
        
        scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            scores[doc_type] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return None
    
    def extract_information_from_text(self, text: str) -> Dict[str, str]:
        """Extrai informações do texto usando regex"""
        info = {}
        
        for field, patterns in self.info_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if field == 'cpf':
                        cpf = re.sub(r'[^\d]', '', matches[0])
                        if len(cpf) == 11:
                            formatted_cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
                            info[field] = formatted_cpf
                            break
                    else:
                        info[field] = matches[0].strip()
                        break
        
        return info
    
    def process_document(self, pdf_path: str, output_dir: str = "./") -> Dict[str, Any]:
        """Processa um documento PDF completo com detecção avançada"""
        try:
            self.logger.info(f"Processando documento: {pdf_path}")
            
            # Extrai texto com Textract
            print("📝 Extraindo texto com AWS Textract...")
            text, structured_data = self.extract_text_with_textract(pdf_path)
            
            if structured_data:
                print("📋 Analisando formulários estruturados...")
            
            # Identifica tipo de documento
            doc_type = self.identify_document_type(text)
            print(f"📄 Tipo de documento identificado: {doc_type}")
            
            # Extrai informações do texto
            extracted_info = self.extract_information_from_text(text)
            
            # Combina informações estruturadas
            if structured_data:
                field_mapping = {
                    'nome': ['nome', 'name'],
                    'cpf': ['cpf'],
                    'rg': ['rg', 'registro geral', 'identidade']
                }
                
                for our_key, possible_keys in field_mapping.items():
                    if not extracted_info.get(our_key):
                        for key in possible_keys:
                            if key in structured_data:
                                value = structured_data[key]
                                if our_key == 'cpf' and value:
                                    clean_cpf = re.sub(r'[^\d]', '', value)
                                    if len(clean_cpf) == 11 and CPFValidator.validate_cpf(clean_cpf):
                                        formatted_cpf = f"{clean_cpf[:3]}.{clean_cpf[3:6]}.{clean_cpf[6:9]}-{clean_cpf[9:]}"
                                        extracted_info[our_key] = formatted_cpf
                                elif value:
                                    extracted_info[our_key] = value
                                break
            
            print(f"ℹ️  Informações extraídas: {extracted_info}")
            
            # Valida CPF
            cpf_valid = False
            if extracted_info.get('cpf'):
                cpf_valid = CPFValidator.validate_cpf(extracted_info['cpf'])
            print(f"✅ CPF válido: {cpf_valid}")
            
            # Extrai fotos com detecção avançada e fallback
            print("🖼️  Iniciando extração de imagens...")
            photo_path = None
            extraction_method = "none"
            
            try:
                # Extrai imagens embutidas
                embedded_images = self.extract_images_from_pdf(pdf_path)
                
                # Detecta melhor foto ou usa fallback
                best_image, extraction_method = self.detect_best_photo_or_fallback(embedded_images, pdf_path)
                
                # Limpa memória
                embedded_images = None
                gc.collect()
                
                if best_image is not None:
                    photo_filename = f"foto_extraida_{os.path.basename(pdf_path)}.jpg"
                    photo_path = os.path.join(output_dir, photo_filename)
                    
                    if self.save_photo(best_image, photo_path):
                        if extraction_method.startswith('face_'):
                            print(f"📸 Foto 3x4 com rosto salva: {photo_path}")
                        else:
                            print(f"📄 Imagem completa do documento salva: {photo_path}")
                    else:
                        photo_path = None
                else:
                    print("❌ Nenhuma imagem pôde ser extraída")
                    
            except Exception as photo_error:
                self.logger.error(f"Erro no processamento de imagens: {photo_error}")
                print("⚠️  Erro ao processar imagens, continuando sem foto...")
            
            # Força limpeza final
            gc.collect()
            
            # Monta resultado
            result = {
                'tipo_documento': doc_type,
                'nome': extracted_info.get('nome', ''),
                'cpf': extracted_info.get('cpf', ''),
                'rg': extracted_info.get('rg', ''),
                'cpf_valido': cpf_valid,
                'foto_extraida': photo_path,
                'extraction_method': extraction_method,
                'sucesso': True,
                'campos_estruturados': structured_data
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro ao processar documento: {e}")
            return {
                'tipo_documento': None,
                'nome': '',
                'cpf': '',
                'rg': '',
                'cpf_valido': False,
                'foto_extraida': None,
                'extraction_method': 'error',
                'sucesso': False,
                'erro': str(e)
            }

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Processador Avançado de Documentos')
    parser.add_argument('pdf_path', help='Caminho para o arquivo PDF')
    parser.add_argument('-o', '--output', default='./', help='Diretório de saída')
    parser.add_argument('-r', '--region', default='us-east-1', help='Região AWS')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    processor = DocumentProcessor(region=args.region)
    result = processor.process_document(args.pdf_path, args.output)
    
    print("\n" + "="*60)
    print("🎯 RESULTADO DO PROCESSAMENTO AVANÇADO")
    print("="*60)
    print(f"📄 Tipo de Documento: {result['tipo_documento']}")
    print(f"👤 Nome: {result['nome']}")
    print(f"🆔 CPF: {result['cpf']}")
    print(f"🆔 RG: {result['rg']}")
    print(f"✅ CPF Válido: {'Sim' if result['cpf_valido'] else 'Não'}")
    print(f"📸 Imagem Extraída: {result['foto_extraida'] or 'Não encontrada'}")
    print(f"🔍 Método de Extração: {result.get('extraction_method', 'N/A')}")
    print(f"📋 Campos Estruturados: {len(result.get('campos_estruturados', {}))}")
    print("="*60)

if __name__ == "__main__":
    main()
