import cv2
import time

stream_url = "http://172.20.10.3:81/stream"

cap = cv2.VideoCapture(stream_url)

time.sleep(2)

if not cap.isOpened():
    print("GRESKA: Stream se ne moze otvoriti.")
    print("Provjeri URL:", stream_url)
    exit()

print("Stream otvoren.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Nema frame-a, pokusavam dalje...")
        continue

    cv2.imshow("ESP32-CAM Stream", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()