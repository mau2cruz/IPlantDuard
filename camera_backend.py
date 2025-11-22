import cv2
import numpy as np


class CameraManager:
    """
    Administrador de cámaras separado de la interfaz.
    Permite capturar desde:
    - Cámara de laptop/PC (cv2.VideoCapture(0))
    - Cámara de celular vía IP (http://IP:PUERTO/video)
    """

    def __init__(self):
        self.cam = None

    # ----------------------------
    #   CÁMARA DE COMPUTADORA
    # ----------------------------
    def abrir_camara_pc(self):
        """Abre la cámara principal del equipo."""
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            raise Exception("No se pudo abrir la cámara de la computadora.")

    def capturar_foto_pc(self):
        """Captura una imagen de la webcam."""
        if self.cam is None:
            self.abrir_camara_pc()

        ret, frame = self.cam.read()
        if not ret:
            raise Exception("No se pudo leer la imagen de la cámara.")

        return frame  # numpy array

    def cerrar_camara_pc(self):
        """Cierra la cámara del PC."""
        if self.cam is not None:
            self.cam.release()
            self.cam = None

    # ----------------------------
    #   CÁMARA DE CELULAR (IP)
    # ----------------------------
    def capturar_foto_ip(self, url_stream):
        """
        Captura imagen desde la cámara del celular vía IP.
        Ejemplo URL: http://192.168.0.15:8080/shot.jpg

        NOTA IMPORTANTE:
        La página web podrá pedirle a AMP CODE
        mejorar esta parte sin tocar la lógica.
        """

        try:
            stream = cv2.VideoCapture(url_stream)

            if not stream.isOpened():
                raise Exception(f"No se pudo conectar al stream: {url_stream}")

            ret, frame = stream.read()
            stream.release()

            if not ret:
                raise Exception("No se pudo capturar la imagen desde IP.")

            return frame

        except Exception as e:
            return {
                "error": f"Error capturando desde cámara IP: {e}"
            }
