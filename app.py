from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
from datetime import datetime
from detector_backend import DetectorPlagas
from camera_backend import CameraManager
from quality_checker import QualityChecker
import cv2

# ----------------------------------------------------
# CONFIGURACIÓN DEL PROYECTO
# ----------------------------------------------------

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["DIAGNOSTICS_FOLDER"] = "diagnostics"
app.secret_key = "iplantguard_secret_key_2025"

if not os.path.exists("uploads"):
    os.makedirs("uploads")
if not os.path.exists(app.config["DIAGNOSTICS_FOLDER"]):
    os.makedirs(app.config["DIAGNOSTICS_FOLDER"])

# Base de datos local JSON para diagnósticos
DIAGNOSTICS_DB = os.path.join(app.config["DIAGNOSTICS_FOLDER"], "diagnostics.json")
CHAT_FAQ = os.path.join(app.config["DIAGNOSTICS_FOLDER"], "faq.json")
DISEASE_LIBRARY = os.path.join(app.config["DIAGNOSTICS_FOLDER"], "disease_library.json")
USER_SETTINGS = os.path.join(app.config["DIAGNOSTICS_FOLDER"], "user_settings.json")

# Funciones auxiliares para base de datos
def load_json_file(filepath):
    """Carga archivo JSON, retorna vacío si no existe."""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json_file(filepath, data):
    """Guarda datos en JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_diagnostic_record(image_name, analysis_result):
    """Agrega un diagnóstico al historial."""
    diagnostics = load_json_file(DIAGNOSTICS_DB)
    if "records" not in diagnostics:
        diagnostics["records"] = []
    
    record = {
        "id": len(diagnostics["records"]) + 1,
        "timestamp": datetime.now().isoformat(),
        "image": image_name,
        "result": analysis_result,
        "plant_type": analysis_result.get("plant_type", "Desconocida"),
        "is_healthy": analysis_result.get("health_assessment", {}).get("is_healthy", False)
    }
    diagnostics["records"].append(record)
    save_json_file(DIAGNOSTICS_DB, diagnostics)
    return record

# Inicializar datos si no existen
if not os.path.exists(CHAT_FAQ):
    default_faq = {
        "questions": [
            {"id": 1, "question": "¿Con qué frecuencia debo regar mis plantas?", "answer": "Depende del tipo de planta y el clima. La mayoría necesita riego cuando el suelo está seco al tacto. Generalmente es cada 2-3 días en verano y menos frecuente en invierno."},
            {"id": 2, "question": "¿Cuáles son los signos de una planta enferma?", "answer": "Hojas amarillas, manchas oscuras, marchitamiento, crecimiento lento y presencia de insectos son señales de alerta."},
            {"id": 3, "question": "¿Cómo puedo mejorar la iluminación de mis plantas?", "answer": "Coloca tus plantas cerca de ventanas con luz natural. Si esto no es posible, considera luces de cultivo LED."},
            {"id": 4, "question": "¿Qué nutrientes necesitan las plantas?", "answer": "Las plantas necesitan nitrógeno (N), fósforo (P) y potasio (K), junto con micronutrientes como hierro, magnesio y zinc."},
            {"id": 5, "question": "¿Cómo sé si estoy regando demasiado?", "answer": "El exceso de agua causa pudrición de raíces, hojas amarillas y olor a humedad. Asegúrate de que las macetas tengan buen drenaje."}
        ]
    }
    save_json_file(CHAT_FAQ, default_faq)

if not os.path.exists(DISEASE_LIBRARY):
    default_library = {
        "diseases": [
            {"id": 1, "name": "Mildiu", "symptoms": "Manchas blancas polvorientas en hojas y tallos", "prevention": "Mantén buena ventilación, evita mojadura foliar"},
            {"id": 2, "name": "Oidio", "symptoms": "Polvo blanco en superficies de hojas, distorsión del crecimiento", "prevention": "Mejora circulación de aire, reduce humedad"},
            {"id": 3, "name": "Roya", "symptoms": "Pústulas naranjas o marrones en envés de hojas", "prevention": "Mantén plantas secas, retira hojas infectadas"},
            {"id": 4, "name": "Antracnosis", "symptoms": "Manchas oscuras con bordes acuosos en hojas y tallos", "prevention": "Mejora drenaje, evita encharcamientos"},
            {"id": 5, "name": "Botrytis", "symptoms": "Moho gris en flores y frutas, especialmente en climas húmedos", "prevention": "Aumenta ventilación, reduce humedad"}
        ]
    }
    save_json_file(DISEASE_LIBRARY, default_library)

if not os.path.exists(USER_SETTINGS):
    default_settings = {
        "language": "es",
        "theme": "light",
        "notifications": True,
        "auto_save": True
    }
    save_json_file(USER_SETTINGS, default_settings)

# ----------------------------------------------------
# CONFIGURAR AQUÍ TU API KEY (NO SE MODIFICA NUNCA)
# ----------------------------------------------------
API_KEY = "gy8cvgR2vrezqaC3IwdjlYsVDroJoag2LoCPGvYNEJVl7sOD8c"  # <-- NO CAMBIAR NADA EN LA LÓGICA
detector = DetectorPlagas(API_KEY)
camera_manager = CameraManager()
quality_checker = QualityChecker()


# ----------------------------------------------------
# PANTALLA PRINCIPAL
# ----------------------------------------------------
@app.route("/")
def inicio():
    return render_template("index.html")

# ----------------------------------------------------
# DASHBOARD DE ESTADÍSTICAS
# ----------------------------------------------------
@app.route("/dashboard")
def dashboard():
    diagnostics = load_json_file(DIAGNOSTICS_DB).get("records", [])
    
    total_diagnostics = len(diagnostics)
    healthy_count = sum(1 for d in diagnostics if d.get("is_healthy", False))
    infected_count = total_diagnostics - healthy_count
    
    # Plantas más analizadas
    plant_types = {}
    for d in diagnostics:
        plant = d.get("plant_type", "Desconocida")
        plant_types[plant] = plant_types.get(plant, 0) + 1
    
    stats = {
        "total": total_diagnostics,
        "healthy": healthy_count,
        "infected": infected_count,
        "plant_types": sorted(plant_types.items(), key=lambda x: x[1], reverse=True)[:5],
        "recent": diagnostics[-5:][::-1] if diagnostics else []
    }
    
    return render_template("dashboard.html", stats=stats)

# ----------------------------------------------------
# HISTORIAL DE DIAGNÓSTICOS
# ----------------------------------------------------
@app.route("/historial")
def historial():
    diagnostics = load_json_file(DIAGNOSTICS_DB).get("records", [])
    # Mostrar más recientes primero
    diagnostics = sorted(diagnostics, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return render_template("historial.html", diagnostics=diagnostics)

# ----------------------------------------------------
# BIBLIOTECA DE ENFERMEDADES
# ----------------------------------------------------
@app.route("/biblioteca")
def biblioteca():
    library = load_json_file(DISEASE_LIBRARY).get("diseases", [])
    return render_template("biblioteca.html", diseases=library)

# ----------------------------------------------------
# PERFIL DE USUARIO
# ----------------------------------------------------
@app.route("/perfil")
def perfil():
    settings = load_json_file(USER_SETTINGS)
    return render_template("perfil.html", settings=settings)

@app.route("/guardar_preferencias", methods=["POST"])
def guardar_preferencias():
    settings = load_json_file(USER_SETTINGS)
    data = request.json
    settings.update(data)
    save_json_file(USER_SETTINGS, settings)
    return jsonify({"success": True})

# ----------------------------------------------------
# CHATBOT DE PREGUNTAS
# ----------------------------------------------------
@app.route("/chatbot")
def chatbot():
    faq = load_json_file(CHAT_FAQ)
    return render_template("chatbot.html", faq=faq.get("questions", []))

# ----------------------------------------------------
# MODO DEMO
# ----------------------------------------------------
@app.route("/demo")
def demo():
    # Buscar imágenes en uploads para usar como demo
    demo_images = []
    if os.path.exists(app.config["UPLOAD_FOLDER"]):
        for img in os.listdir(app.config["UPLOAD_FOLDER"])[:5]:
            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                demo_images.append(img)
    
    return render_template("demo.html", demo_images=demo_images)

@app.route("/analizar_demo/<imagen>")
def analizar_demo(imagen):
    """Analiza una imagen de demostración."""
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], imagen)
    
    if os.path.exists(ruta):
        resultados = detector.analizar_imagen_desde_archivo(ruta)
        add_diagnostic_record(imagen, resultados)
        return render_template("resultado.html", datos=resultados)
    else:
        return render_template("resultado.html", datos={"error": "Imagen de demo no encontrada"})


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

    # Verificar calidad de imagen
    quality_check = quality_checker.check_image(ruta_guardada)
    
    if quality_check["is_poor"]:
        return render_template("editor.html", 
                             imagen_path=ruta_guardada, 
                             advertencias=quality_check["warnings"])

    # Analizar
    resultados = detector.analizar_imagen_desde_archivo(ruta_guardada)
    # Agregar recomendaciones automáticas
    resultados = agregar_recomendaciones_contextuales(resultados)
    add_diagnostic_record(archivo.filename, resultados)
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

        # Verificar calidad
        quality_check = quality_checker.check_image(ruta)
        if quality_check["is_poor"]:
            return render_template("editor.html", 
                                 imagen_path=ruta, 
                                 advertencias=quality_check["warnings"])

        resultados = detector.analizar_imagen_desde_archivo(ruta)
        resultados = agregar_recomendaciones_contextuales(resultados)
        add_diagnostic_record("captura_pc.jpg", resultados)
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

    # Verificar calidad
    quality_check = quality_checker.check_image(ruta)
    if quality_check["is_poor"]:
        return render_template("editor.html", 
                             imagen_path=ruta, 
                             advertencias=quality_check["warnings"])

    resultados = detector.analizar_imagen_desde_archivo(ruta)
    resultados = agregar_recomendaciones_contextuales(resultados)
    add_diagnostic_record("captura_ip.jpg", resultados)
    print("RESPUESTA PLANTID:", resultados)
    return render_template("resultado.html", datos=resultados)

# ====================================================
# FUNCIÓN AUXILIAR: RECOMENDACIONES CONTEXTUALES
# ====================================================
def agregar_recomendaciones_contextuales(resultado):
    """Agrega recomendaciones estáticas basadas en el resultado (SIN alterar API)."""
    if "error" in resultado:
        return resultado
    
    is_healthy = resultado.get("health_assessment", {}).get("is_healthy", False)
    diseases = resultado.get("health_assessment", {}).get("diseases", [])
    
    recs = resultado.get("recommendations", [])
    
    # Agregar recomendaciones contextuales sin afectar diagnóstico
    if not is_healthy and diseases:
        disease_name = diseases[0]["name"] if diseases else "enfermedad"
        recs.insert(0, f"📚 Consulta la Biblioteca de Enfermedades para aprender más sobre {disease_name}.")
    
    recs.append("💡 Utiliza el Chatbot para resolver dudas generales de cuidado.")
    
    resultado["recommendations"] = recs
    return resultado

# ====================================================
# EDITOR DE IMÁGENES (procesar imagen antes de análisis)
# ====================================================
@app.route("/procesar_imagen", methods=["POST"])
def procesar_imagen():
    """Procesa imagen con editor: recorte, rotación, brillo."""
    data = request.json
    imagen_path = data.get("imagen_path")
    acciones = data.get("acciones", {})
    
    if not os.path.exists(imagen_path):
        return jsonify({"error": "Imagen no encontrada"}), 404
    
    from PIL import Image, ImageEnhance
    
    img = Image.open(imagen_path)
    
    # Recorte
    if "crop" in acciones:
        crop_data = acciones["crop"]
        img = img.crop((crop_data["x1"], crop_data["y1"], crop_data["x2"], crop_data["y2"]))
    
    # Rotación
    if "rotate" in acciones:
        img = img.rotate(acciones["rotate"], expand=True)
    
    # Brillo
    if "brightness" in acciones:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(acciones["brightness"])
    
    img.save(imagen_path)
    
    # Reanálizar
    resultados = detector.analizar_imagen_desde_archivo(imagen_path)
    resultados = agregar_recomendaciones_contextuales(resultados)
    add_diagnostic_record(os.path.basename(imagen_path), resultados)
    
    return jsonify({"success": True, "resultado": resultados})


# ----------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ----------------------------------------------------
if __name__ == "__main__":
    # En Render (y otros cloud), el puerto viene en la variable de entorno 'PORT'
    # Si no existe (estamos en local), usamos 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
