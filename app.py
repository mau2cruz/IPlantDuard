from flask import Flask, render_template, request, redirect, url_for
import os
from detector_backend import DetectorPlagas
from camera_backend import CameraManager
import cv2

# ----------------------------------------------------
# CONFIGURACIÓN DEL PROYECTO
# ----------------------------------------------------

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# ----------------------------------------------------
# CONFIGURAR AQUÍ TU API KEY (NO SE MODIFICA NUNCA)
# ----------------------------------------------------
API_KEY = "gy8cvgR2vrezqaC3IwdjlYsVDroJoag2LoCPGvYNEJVl7sOD8c"  # <-- NO CAMBIAR NADA EN LA LÓGICA
detector = DetectorPlagas(API_KEY)

camera_manager = CameraManager()


# ----------------------------------------------------
# PANTALLA PRINCIPAL
# ----------------------------------------------------
@app.route("/")
def inicio():
    return render_template("index.html")


# ----------------------------------------------------
# SUBIR IMAGEN DESDE ARCHIVO
# ----------------------------------------------------
@app.route("/analizar_archivo", methods=["POST"])
def analizar_archivo():
    archivo = request.files["archivo"]

    if archivo.filename == "":
        return redirect(url_for("inicio"))

    ruta_guardada = os.path.join(app.config["UPLOAD_FOLDER"], archivo.filename)
    archivo.save(ruta_guardada)

    # Analizar
    resultados = detector.analizar_imagen_desde_archivo(ruta_guardada)
    print("RESPUESTA PLANTID:", resultados)
    return render_template("resultado.html", datos=resultados)


# ----------------------------------------------------
# CAPTURAR DESDE CÁMARA DE PC
# ----------------------------------------------------
@app.route("/foto_pc")
def foto_pc():
    try:
        camera_manager.abrir_camara_pc()
        imagen = camera_manager.capturar_foto_pc()
        camera_manager.cerrar_camara_pc()

        ruta = "uploads/captura_pc.jpg"
        cv2.imwrite(ruta, imagen)

        resultados = detector.analizar_imagen_desde_archivo(ruta)
        print("RESPUESTA PLANTID:", resultados)
        return render_template("resultado.html", datos=resultados)

    except Exception as e:
        return render_template("resultado.html", datos={"error": str(e)})


# ----------------------------------------------------
# CAPTURAR DESDE CÁMARA DE CELULAR (IP)
# ----------------------------------------------------
@app.route("/foto_ip", methods=["POST"])
def foto_ip():
    ip = request.form["ip"]

    url = f"http://{ip}/shot.jpg"  # ejemplo: 192.168.0.15:8080

    imagen = camera_manager.capturar_foto_ip(url)

    if isinstance(imagen, dict) and "error" in imagen:
        return render_template("resultado.html", datos=imagen)

    ruta = "uploads/captura_ip.jpg"
    cv2.imwrite(ruta, imagen)

    resultados = detector.analizar_imagen_desde_archivo(ruta)
    print("RESPUESTA PLANTID:", resultados)
    return render_template("resultado.html", datos=resultados)


# ----------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ----------------------------------------------------
if __name__ == "__main__":
    # En Render (y otros cloud), el puerto viene en la variable de entorno 'PORT'
    # Si no existe (estamos en local), usamos 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
