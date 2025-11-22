import cv2
import numpy as np

class QualityChecker:
    """
    Verificador de calidad de imagen.
    Detecta: desenfoque, oscuridad, encuadre deficiente.
    """
    
    def __init__(self, blur_threshold=100, darkness_threshold=50, focus_threshold=0.3):
        self.blur_threshold = blur_threshold
        self.darkness_threshold = darkness_threshold
        self.focus_threshold = focus_threshold
    
    def check_image(self, image_path):
        """
        Verifica la calidad general de la imagen.
        Retorna dict con: is_poor (bool), warnings (list), scores (dict)
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {
                    "is_poor": True,
                    "warnings": ["No se pudo leer la imagen"],
                    "scores": {}
                }
            
            blur_score = self.detect_blur(img)
            darkness_score = self.detect_darkness(img)
            focus_score = self.detect_focus(img)
            
            warnings = []
            is_poor = False
            
            # Verificar desenfoque
            if blur_score < self.blur_threshold:
                warnings.append("⚠️ Imagen desenfocada: la foto podría estar movida o desenfocada.")
                is_poor = True
            
            # Verificar oscuridad
            if darkness_score < self.darkness_threshold:
                warnings.append("⚠️ Imagen muy oscura: mejora la iluminación.")
                is_poor = True
            
            # Verificar foco
            if focus_score < self.focus_threshold:
                warnings.append("⚠️ Foco deficiente: asegúrate de que la planta esté claramente visible.")
                is_poor = True
            
            return {
                "is_poor": is_poor,
                "warnings": warnings,
                "scores": {
                    "blur": blur_score,
                    "darkness": darkness_score,
                    "focus": focus_score
                }
            }
        
        except Exception as e:
            return {
                "is_poor": True,
                "warnings": [f"Error verificando imagen: {str(e)}"],
                "scores": {}
            }
    
    def detect_blur(self, img):
        """
        Detecta desenfoque usando Laplaciano.
        Valores altos = imagen nítida, valores bajos = desenfoque.
        """
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return laplacian_var
    
    def detect_darkness(self, img):
        """
        Detecta si la imagen está muy oscura.
        Retorna brillo promedio (0-255).
        """
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        brightness = np.mean(gray)
        return brightness
    
    def detect_focus(self, img):
        """
        Detecta si hay objeto bien enfocado usando contornos.
        Retorna proporción de píxeles con cambio significativo.
        """
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Aplicar Sobel para detectar bordes
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # Proporción de píxeles con bordes claros
        threshold = np.mean(magnitude) + np.std(magnitude)
        edge_pixels = np.sum(magnitude > threshold)
        total_pixels = magnitude.size
        
        return edge_pixels / total_pixels
