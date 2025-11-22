import cv2
import base64
import requests
import numpy as np

class DetectorPlagas:
    """
    LÓGICA PRINCIPAL DE ANÁLISIS (SIN INTERFAZ)
    Extraída directamente de tu archivo original Plant_Guard.py
    NO se modifica nada del análisis.
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://plant.id/api/v3/health_assessment"

    def convertir_imagen_a_base64(self, ruta_imagen):
        """Convierte imagen local a base64 para la API."""
        with open(ruta_imagen, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analizar_imagen_desde_archivo(self, ruta_imagen):
        """Usa la imagen de archivo."""
        imagen_b64 = self.convertir_imagen_a_base64(ruta_imagen)
        return self._enviar_a_plantid(imagen_b64)

    def analizar_imagen_desde_array(self, imagen):
        """Analiza imágenes en formato numpy (cámara)."""
        _, buffer = cv2.imencode('.jpg', imagen)
        imagen_b64 = base64.b64encode(buffer).decode('utf-8')
        return self._enviar_a_plantid(imagen_b64)

    def _enviar_a_plantid(self, imagen_b64):
        """Envía la imagen a Plant.ID (no se modifica nada)."""
        payload = {
            "images": [imagen_b64],
            "similar_images": True
        }

        headers = {
            "Content-Type": "application/json",
            "Api-Key": self.api_key
        }

        response = requests.post(self.api_url, json=payload, headers=headers)

        if response.status_code not in [200, 201]:
            return {
                "error": f"HTTP {response.status_code}",
                "detalle": response.text
            }

        return self._adaptar_respuesta(response.json())

    def _adaptar_respuesta(self, data):
        """
        Adapta la respuesta de Plant.ID v3 al formato que espera el template.
        El template espera: datos.health_assessment.is_healthy, .diseases, etc.
        """
        # Si la API ya devuelve health_assessment (formato antiguo/personalizado), lo dejamos pasar
        if "health_assessment" in data:
            return data

        # Si viene en formato v3 estándar ("result": {...})
        if "result" in data:
            result = data["result"]
            
            # 1. Estado de Salud
            is_healthy = result.get("is_healthy", {}).get("binary", False)
            
            # 2. Enfermedades y detalles
            diseases_list = []
            reasons_list = []
            recommendations_list = []

            suggestions = result.get("disease", {}).get("suggestions", [])
            
            for s in suggestions:
                # Filtramos solo las que tengan probabilidad alta
                prob = s.get("probability", 0)
                if prob > 0.05: # Bajamos un poco el umbral para mostrar más info relevante
                    name = s.get("name", "Desconocido")
                    similarity = f"{int(prob * 100)}%"
                    
                    diseases_list.append({
                        "name": name,
                        "severity": similarity
                    })

                    # Intentamos sacar más info si existe (detalles, descripción)
                    # La API v3 a veces incluye 'details' con 'description' o 'treatment'
                    details = s.get("details", {})
                    if "description" in details:
                         desc = details["description"]
                         # Recortamos si es muy largo
                         if len(desc) > 150: desc = desc[:147] + "..."
                         reasons_list.append(f"{name}: {desc}")
                    elif "url" in s:
                        reasons_list.append(f"{name}: Ver más en {s['url']}")
                    
                    # Tratamiento (si la API lo provee en alguna estructura futura o 'treatment')
                    if "treatment" in details:
                         recommendations_list.append(f"Tratamiento para {name}: {details['treatment']}")

            # Si no hay razones específicas, ponemos genericas basadas en los nombres
            if not reasons_list and diseases_list:
                top_disease = diseases_list[0]["name"]
                reasons_list.append(f"Se ha detectado una alta probabilidad de {top_disease}.")
                reasons_list.append("Los síntomas visuales coinciden con patrones conocidos de esta patología.")

            # Si no hay recomendaciones específicas, generamos unas contextuales
            if not recommendations_list and not is_healthy:
                 recommendations_list.append("Aísle inmediatamente la planta para evitar contagios.")
                 recommendations_list.append("Retire las hojas visiblemente afectadas con tijeras desinfectadas.")
                 recommendations_list.append("Evite mojar las hojas durante el riego.")
                 if diseases_list:
                     recommendations_list.append(f"Busque un fungicida o tratamiento específico para: {diseases_list[0]['name']}.")
            elif is_healthy:
                recommendations_list.append("Continúe con los cuidados actuales de riego y luz.")
                recommendations_list.append("Realice podas de mantenimiento regularmente.")
                reasons_list.append("El análisis no detectó anomalías visuales significativas.")

            # 3. Construir estructura compatible
            data["health_assessment"] = {
                "is_healthy": is_healthy,
                "diseases": diseases_list,
                "reasons": reasons_list
            }
            
            data["recommendations"] = recommendations_list
                
        return data
