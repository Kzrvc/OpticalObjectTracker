#include <ESP32Servo.h>

// Prima "x,y\n" preko serijske veze (kadar 640x480) i pomiče dva servo motora.
Servo servoX;
Servo servoY;

int servoXPin = 18;
int servoYPin = 19;

int angleX = 90;
int angleY = 90;

void setup() {
  Serial.begin(115200);

  servoX.attach(servoXPin);
  servoY.attach(servoYPin);

  servoX.write(90);
  servoY.write(90);

  Serial.println("ESP32 2-servo ready");
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');

    int commaIndex = data.indexOf(',');
    if (commaIndex > 0) {
      int x = data.substring(0, commaIndex).toInt();
      int y = data.substring(commaIndex + 1).toInt();

      if (x >= 0 && x <= 640 && y >= 0 && y <= 480) {
        angleX = map(x, 0, 640, 150, 30);  // X smjer je obrnut
        angleY = map(y, 0, 480, 30, 150);

        angleX = constrain(angleX, 30, 150);
        angleY = constrain(angleY, 30, 150);
        servoX.write(angleX);
        servoY.write(angleY);

        Serial.print("X=");
        Serial.print(x);
        Serial.print(" Y=");
        Serial.print(y);
        Serial.print(" AngleX=");
        Serial.print(angleX);
        Serial.print(" AngleY=");
        Serial.println(angleY);
      }
    }
  }
}
