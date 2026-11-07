import serial
import time

esp = serial.Serial("COM6", 115200, timeout=1)

time.sleep(2)

while True:

    positions = [50, 320, 600, 320]

    for x in positions:

        esp.write(f"{x},240\n".encode())

        print("Poslano:", x)

        time.sleep(1)