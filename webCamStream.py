from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import imutils
import time
import cv2

# Inicializar frame de salida y generamos un lock, ya que outputFrame
# va a ser accedido por distintos procesos.
outputFrame = None
lock = threading.Lock()

app = Flask(__name__)

# Iniciamos el stream de video
vs = cv2.VideoCapture(0)
time.sleep(2.0)

@app.route("/")
def index():
    return render_template("index.html")

def get_frames():
    global vs, outputFrame, lock

    while True:
        ret, frame = vs.read()
        frame = imutils.resize(frame, width = 400)
        with lock:
            outputFrame = frame.copy()

def generate():
    global outputFrame, lock

    while True:
        with lock:
            if outputFrame is None:
                continue

            (flag, encondedImage) = cv2.imencode(".jpg", outputFrame)

            if not flag:
                continue

            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encondedImage) + b'\r\n')


@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

# Entrada al script
if __name__ == '__main__':

    # Iniciamos thread para leer frames desde la webcam
    t = threading.Thread(target = get_frames)
    t.daemon = True
    t.start()

    # Iniciamos app web para transmitir frames
    app.run(port = 8080)

vs.release()