// Animación suave al cargar la página
document.addEventListener("DOMContentLoaded", () => {
    const tarjetas = document.querySelectorAll(".tarjeta");
    tarjetas.forEach(t => {
        t.style.opacity = 0;
        setTimeout(() => {
            t.style.transition = "0.8s ease";
            t.style.opacity = 1;
        }, 150);
    });
});

// Validación para IP de cámara de celular
function validarIP(ip) {
    const patron = /^[0-9]{1,3}(\.[0-9]{1,3}){3}\:[0-9]+$/;
    return patron.test(ip);
}

const formularioIP = document.querySelector("form[action='/foto_ip']");
if (formularioIP) {
    formularioIP.addEventListener("submit", e => {
        const input = formularioIP.querySelector("input[name='ip']");
        if (!validarIP(input.value)) {
            e.preventDefault();
            alert("Formato de IP inválido. Ejemplo válido: 192.168.0.23:8080");
        }
    });
}

// ------------------------------------------------------
// FEEDBACK VISUAL: MOSTRAR QUE LA FOTO YA SE TOMÓ
// ------------------------------------------------------
const inputsArchivo = document.querySelectorAll("input[type='file']");

inputsArchivo.forEach(input => {
    input.addEventListener("change", function() {
        if (this.files && this.files.length > 0) {
            const fileName = this.files[0].name;
            const label = this.parentElement;
            
            // Efecto visual de "Éxito"
            label.style.backgroundColor = "#2ecc71"; // Se pone verde
            label.style.color = "white";             // Texto blanco
            label.style.borderColor = "#27ae60";     // Borde verde oscuro
            label.style.transition = "0.3s ease";
            label.style.transform = "scale(1.02)";   // Un pequeño "pop"

            // Cambiar el texto del botón para confirmar
            // Buscamos el texto dentro del label (ignorando el <input>)
            let textNode = Array.from(label.childNodes).find(node => node.nodeType === 3 && node.textContent.trim().length > 0);
            
            if (textNode) {
                // Acortar nombre si es muy largo
                const nombreCorto = fileName.length > 15 ? fileName.substring(0, 12) + "..." : fileName;
                textNode.textContent = `✅ ¡Foto Capturada! (${nombreCorto})`;
            }
        }
    });
});

// ------------------------------------------------------
// LÓGICA DE CÁMARA WEB (JS)
// ------------------------------------------------------
const modalCamara = document.getElementById("modal-camara");
const videoWebcam = document.getElementById("video-webcam");
const canvasWebcam = document.getElementById("canvas-webcam");
const formWebcam = document.getElementById("form-webcam");
let streamActual = null;

function iniciarWebcam() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                streamActual = stream;
                videoWebcam.srcObject = stream;
                modalCamara.style.display = "flex";
            })
            .catch(err => {
                alert("No se pudo acceder a la cámara: " + err.message);
            });
    } else {
        alert("Tu navegador no soporta acceso a cámara web.");
    }
}

function cerrarWebcam() {
    if (streamActual) {
        streamActual.getTracks().forEach(track => track.stop());
        streamActual = null;
    }
    modalCamara.style.display = "none";
}

function capturarWebcam() {
    if (!streamActual) return;

    // Ajustar tamaño del canvas al video
    canvasWebcam.width = videoWebcam.videoWidth;
    canvasWebcam.height = videoWebcam.videoHeight;
    
    // Dibujar frame actual
    const ctx = canvasWebcam.getContext("2d");
    ctx.drawImage(videoWebcam, 0, 0, canvasWebcam.width, canvasWebcam.height);

    // Convertir a Blob y enviar
    canvasWebcam.toBlob(blob => {
        // Crear un archivo simulado
        const file = new File([blob], "captura_webcam.jpg", { type: "image/jpeg" });
        
        // Asignarlo al input file del formulario oculto
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        document.getElementById("input-webcam-file").files = dataTransfer.files;

        // Enviar formulario
        cerrarWebcam();
        formWebcam.submit();
    }, "image/jpeg");
}

// ====================================================
// NUEVAS FUNCIONALIDADES - CHATBOT FAQ
// ====================================================
function toggleAnswer(element) {
    const answer = element.nextElementSibling;
    const icon = element.querySelector('.faq-icon');
    
    // Si está abierto, cerrar
    if (answer.style.display !== 'none') {
        answer.style.display = 'none';
        icon.textContent = '➕';
    } else {
        // Cerrar otros abiertos
        document.querySelectorAll('.faq-answer').forEach(a => {
            a.style.display = 'none';
        });
        document.querySelectorAll('.faq-icon').forEach(i => {
            i.textContent = '➕';
        });
        
        // Abrir este
        answer.style.display = 'block';
        icon.textContent = '➖';
    }
}

// ====================================================
// TEMA OSCURO
// ====================================================
function setTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        localStorage.setItem('iplantguard-theme', 'dark');
    } else {
        document.body.classList.remove('dark-theme');
        localStorage.setItem('iplantguard-theme', 'light');
    }
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('iplantguard-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

// Aplicar tema guardado al cargar
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('iplantguard-theme');
    if (savedTheme) {
        setTheme(savedTheme);
    }
});

// ====================================================
// UTILIDADES
// ====================================================
function mostrarExito(mensaje) {
    const div = document.createElement('div');
    div.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #2ecc71;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    div.textContent = mensaje;
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}

function mostrarError(mensaje) {
    const div = document.createElement('div');
    div.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #e74c3c;
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    div.textContent = mensaje;
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}
