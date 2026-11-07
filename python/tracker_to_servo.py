import cv2
import numpy as np
import serial
import time

stream_url = "http://172.20.10.3:81/stream"
esp = serial.Serial("COM6", 115200, timeout=1)
time.sleep(2)

cap = cv2.VideoCapture(stream_url)

TARGET_SHAPE = "CIRCLE"   # CIRCLE / SQUARE / TRIANGLE
smooth_x = None

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

last_send = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (640, 480))

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(blur, 20, 80)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

        if smooth_x is None:
            smooth_x = current_x
        else:
            smooth_x = int(0.8 * smooth_x + 0.2 * current_x)

        # šaljemo X na ESP32 svakih 0.1 s
        if time.time() - last_send > 0.1:
            esp.write(f"{smooth_x},{y + h // 2}\n".encode())
            last_send = time.time()

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(frame, f"TRACKING {TARGET_SHAPE} X:{smooth_x}",
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.circle(frame, (smooth_x, y + h // 2), 6, (0,0,255), -1)

    else:
        cv2.putText(frame, f"{TARGET_SHAPE} NOT DETECTED",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

    cv2.imshow("Tracker to Servo", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
esp.close()
cv2.destroyAllWindows()