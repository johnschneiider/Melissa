import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import io
import base64
import json
from typing import Dict, List, Tuple
import os
import replicate
from django.conf import settings
from django.core.files.base import ContentFile

class VisagismoService:
    """Servicio para análisis de visagismo usando IA"""
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
    
    def analizar_rostro(self, imagen_path: str) -> Dict:
        """Analiza el rostro y extrae características faciales"""
        try:
            # Cargar imagen
            imagen = cv2.imread(imagen_path)
            imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
            
            # Detectar landmarks faciales
            resultados = self.face_mesh.process(imagen_rgb)
            
            if not resultados.multi_face_landmarks:
                return {"error": "No se detectó un rostro en la imagen"}
            
            landmarks = resultados.multi_face_landmarks[0]
            
            # Extraer características
            caracteristicas = self._extraer_caracteristicas(landmarks, imagen.shape)
            
            return caracteristicas
            
        except Exception as e:
            return {"error": f"Error en el análisis: {str(e)}"}
    
    def _extraer_caracteristicas(self, landmarks, imagen_shape) -> Dict:
        """Extrae características específicas del rostro"""
        altura, ancho = imagen_shape[:2]
        
        # Convertir landmarks a coordenadas de píxeles
        puntos = []
        for landmark in landmarks.landmark:
            x = int(landmark.x * ancho)
            y = int(landmark.y * altura)
            puntos.append((x, y))
        
        # Calcular medidas faciales
        medidas = self._calcular_medidas_faciales(puntos)
        
        # Determinar forma de cara
        forma_cara = self._determinar_forma_cara(medidas)
        
        return {
            "forma_cara": forma_cara,
            "medidas_faciales": medidas,
            "landmarks": puntos[:10]  # Solo primeros 10 puntos para ahorrar espacio
        }
    
    def _calcular_medidas_faciales(self, puntos: List[Tuple[int, int]]) -> Dict:
        """Calcula medidas faciales clave"""
        # Índices de landmarks importantes (MediaPipe Face Mesh)
        # Estos índices pueden variar según la versión de MediaPipe
        
        # Ancho de cara (puntos de las sienes)
        ancho_cara = self._calcular_distancia(puntos[10], puntos[234])  # Aproximado
        
        # Alto de cara (frente a mentón)
        alto_cara = self._calcular_distancia(puntos[10], puntos[152])  # Aproximado
        
        # Ancho de mandíbula
        ancho_mandibula = self._calcular_distancia(puntos[132], puntos[361])  # Aproximado
        
        # Relación ancho/alto
        relacion_ancho_alto = ancho_cara / alto_cara if alto_cara > 0 else 0
        
        return {
            "ancho_cara": ancho_cara,
            "alto_cara": alto_cara,
            "ancho_mandibula": ancho_mandibula,
            "relacion_ancho_alto": relacion_ancho_alto
        }
    
    def _calcular_distancia(self, punto1: Tuple[int, int], punto2: Tuple[int, int]) -> float:
        """Calcula la distancia euclidiana entre dos puntos"""
        return np.sqrt((punto2[0] - punto1[0])**2 + (punto2[1] - punto1[1])**2)
    
    def _determinar_forma_cara(self, medidas: Dict) -> str:
        """Determina la forma de la cara basada en las medidas"""
        relacion = medidas.get("relacion_ancho_alto", 0)
        
        if relacion > 0.85:
            return "redonda"
        elif relacion > 0.75:
            return "ovalada"
        elif relacion > 0.65:
            return "cuadrada"
        else:
            return "alargada"
    
    def generar_recomendaciones(self, caracteristicas: Dict) -> List[Dict]:
        """Genera recomendaciones de cortes basadas en las características"""
        forma_cara = caracteristicas.get("forma_cara", "ovalada")
        
        recomendaciones = {
            "redonda": [
                {
                    "nombre": "Corte Asimétrico",
                    "descripcion": "Corte que crea líneas asimétricas para alargar visualmente el rostro",
                    "categoria": "asimetrico",
                    "confianza": 0.85,
                    "prompt": "asymmetric bob haircut, layered, side swept bangs"
                },
                {
                    "nombre": "Bob Largo",
                    "descripcion": "Corte que llega hasta los hombros para crear líneas verticales",
                    "categoria": "medio",
                    "confianza": 0.80,
                    "prompt": "long bob haircut, shoulder length, straight hair"
                }
            ],
            "ovalada": [
                {
                    "nombre": "Corte Clásico",
                    "descripcion": "Corte que complementa la forma natural del rostro",
                    "categoria": "medio",
                    "confianza": 0.90,
                    "prompt": "classic layered haircut, natural waves, medium length"
                },
                {
                    "nombre": "Capas Suaves",
                    "descripcion": "Capas que añaden movimiento sin alterar la forma natural",
                    "categoria": "capas",
                    "confianza": 0.85,
                    "prompt": "soft layers, textured haircut, natural movement"
                }
            ],
            "cuadrada": [
                {
                    "nombre": "Corte Ondulado",
                    "descripcion": "Ondas suaves que suavizan los ángulos del rostro",
                    "categoria": "medio",
                    "confianza": 0.85,
                    "prompt": "wavy haircut, soft curls, shoulder length"
                },
                {
                    "nombre": "Bob Redondeado",
                    "descripcion": "Corte que redondea los ángulos de la mandíbula",
                    "categoria": "corto",
                    "confianza": 0.80,
                    "prompt": "rounded bob haircut, chin length, smooth edges"
                }
            ],
            "alargada": [
                {
                    "nombre": "Corte con Flequillo",
                    "descripcion": "Flequillo que acorta visualmente el rostro",
                    "categoria": "medio",
                    "confianza": 0.85,
                    "prompt": "bangs haircut, side swept fringe, medium length"
                },
                {
                    "nombre": "Corte en Capas Horizontales",
                    "descripcion": "Capas que añaden volumen horizontal",
                    "categoria": "capas",
                    "confianza": 0.80,
                    "prompt": "horizontal layers, voluminous haircut, long hair"
                }
            ]
        }
        
        return recomendaciones.get(forma_cara, recomendaciones["ovalada"])

class IAImageProcessor:
    """Procesador de imágenes para IA"""
    
    @staticmethod
    def procesar_imagen(imagen_path: str) -> str:
        """Procesa la imagen para mejorar el análisis"""
        try:
            imagen = Image.open(imagen_path)
            
            # Redimensionar si es muy grande
            max_size = (800, 800)
            imagen.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Mejorar contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(imagen)
            imagen = enhancer.enhance(1.2)
            
            # Guardar imagen procesada
            output_path = imagen_path.replace('.', '_procesada.')
            imagen.save(output_path, 'JPEG', quality=85)
            
            return output_path
            
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            return imagen_path

class ReplicateService:
    """Servicio para generar imágenes con Replicate"""
    
    def __init__(self):
        # Configurar API key de Replicate
        self.api_token = getattr(settings, 'REPLICATE_API_TOKEN', None)
        if self.api_token:
            os.environ['REPLICATE_API_TOKEN'] = self.api_token
    
    def generar_imagen_con_corte(self, imagen_path: str, prompt_corte: str) -> str:
        """Genera una imagen con el corte de cabello aplicado"""
        try:
            if not self.api_token:
                return None
            
            # Leer imagen como base64
            with open(imagen_path, 'rb') as f:
                imagen_bytes = f.read()
                imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            
            # Prompt para la generación
            prompt = f"A photo of the same person with {prompt_corte}, realistic, same pose, same background, high quality, professional photography"
            
            # Usar modelo de Replicate para generación de imágenes
            # Modelo: stable-diffusion-xl-base-1.0
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt,
                    "image": f"data:image/jpeg;base64,{imagen_base64}",
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "strength": 0.8  # Controla cuánto cambiar la imagen original
                }
            )
            
            if output and len(output) > 0:
                return output[0]  # URL de la imagen generada
            
            return None
            
        except Exception as e:
            print(f"Error generando imagen con Replicate: {e}")
            return None
    
    def generar_imagen_alternativa(self, prompt: str) -> str:
        """Genera una imagen alternativa sin usar la foto original"""
        try:
            if not self.api_token:
                return None
            
            # Usar modelo de Replicate para generación de imágenes
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5
                }
            )
            
            if output and len(output) > 0:
                return output[0]  # URL de la imagen generada
            
            return None
            
        except Exception as e:
            print(f"Error generando imagen alternativa: {e}")
            return None 