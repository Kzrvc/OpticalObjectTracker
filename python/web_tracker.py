import cv2
import numpy as np
import serial
import time
from flask import Flask, Response, render_template_string, redirect

stream_url = "http://172.20.10.3:81/stream"
esp = serial.Serial("COM6", 115200, timeout=1)
time.sleep(2)

cap = cv2.VideoCapture(stream_url)

app = Flask(__name__)

TARGET_SHAPE = "CIRCLE"

smooth_x = None
smooth_y = None

last_send = 0
last_status = "NOT DETECTED"


html_page = """
<!DOCTYPE html>
<html>
<head>
    <title>Optical Object Tracker</title>
    <style>
        body {
            font-family: Arial;
            text-align: center;
            background: #111;
            color: white;
        }
        button {
            font-size: 25px;
            padding: 15px 30px;
            margin: 10px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
        }
        .active {
            background: limegreen;
            color: white;
        }
        .normal {
            background: #444;
            color: white;
        }
        img {
            border: 4px solid white;
            border-radius: 10px;
            width: 80%;
            max-width: 800px;
        }
    </style>
</head>
<body>
    <h1>Optical Object Tracker</h1>

    <h2>Trenutno prati: {{ target }}</h2>
    <h3>Status: {{ status }}</h3>

    <a href="/set/CIRCLE">
        <button class="{{ 'active' if target == 'CIRCLE' else 'normal' }}">KUGLA / KRUG</button>
    </a>

    <a href="/set/SQUARE">
        <button class="{{ 'active' if target == 'SQUARE' else 'normal' }}">KOCKA / KVADRAT</button>
    </a>

    <a href="/set/TRIANGLE">
        <button class="{{ 'active' if target == 'TRIANGLE' else 'normal' }}">TROKUT</button>
    </a>

    <br><br>

    <img src="/video_feed">
</body>
</html>
"""


def detect_shape(contour):
    area = cv2.contourArea(contour)

    if area < 600:
        return "UNKNOWN"

    perimeter = cv2.arcLength(contour, True)

    if perimeter == 0:
        return "UNKNOWN"

    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    vertices = len(approx)

    if vertices == 3:
        return "TRIANGLE"

    if vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        ratio = w / float(h)

        if 0.65 <= ratio <= 1.35:
            return "SQUARE"

    circularity = 4 * np.pi * area / (perimeter * perimeter)

    if circularity > 0.55:
        return "CIRCLE"

    return "UNKNOWN"


def generate_frames():
    global smooth_x, smooth_y, last_send, last_status

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blur, 20, 80)

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        best_contour = None
        best_area = 0

        for contour in contours:
            shape = detect_shape(contour)

            if shape != TARGET_SHAPE:
                continue

            area = cv2.contourArea(contour)

            if area > best_area:
                best_area = area
                best_contour = contour

        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)

            current_x = x + w // 2
            current_y = y + h // 2

            if smooth_x is None or smooth_y is None:
                smooth_x = current_x
                smooth_y = current_y
            else:
                smooth_x = int(0.8 * smooth_x + 0.2 * current_x)
                smooth_y = int(0.8 * smooth_y + 0.2 * current_y)

            if time.time() - last_send > 0.1:
                esp.write(f"{smooth_x},{smooth_y}\n".encode())
                last_send = time.time()

            last_status = f"DETECTED X:{smooth_x} Y:{smooth_y}"

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.putText(
                frame,
                f"TRACKING {TARGET_SHAPE} X:{smooth_x} Y:{smooth_y}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.circle(frame, (smooth_x, smooth_y), 6, (0, 0, 255), -1)

        else:
            smooth_x = None
            smooth_y = None
            last_status = "NOT DETECTED"

            cv2.putText(
                frame,
                f"{TARGET_SHAPE} NOT DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2
            )

        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/")
def index():
    return render_template_string(
        html_page,
        target=TARGET_SHAPE,
        status=last_status
    )


@app.route("/set/<shape>")
def set_shape(shape):
    global TARGET_SHAPE, smooth_x, smooth_y

    if shape in ["CIRCLE", "SQUARE", "TRIANGLE"]:
        TARGET_SHAPE = shape
        smooth_x = None
        smooth_y = None

    return redirect("/")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)