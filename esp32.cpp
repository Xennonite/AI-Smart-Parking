#include <WiFi.h>
#include <ArduinoJson.h>
#include <WebServer.h>
#include <ESP32Servo.h>
#include <LiquidCrystal_I2C.h>
#include <ESPmDNS.h>

Servo myServo;
LiquidCrystal_I2C lcd(0x27, 16, 2);

int irPin = 18;
int servoPin = 13;

unsigned long servoOpenTime = 0;
bool servoIsOpen = false;

const char* ssid = "YOURSSID";
const char* password = "YOURPASSWORD";
const char* hostname = "esp32";

WebServer server(80);

void convertToChars(int inputArray[], char outputArray[], int length) {
  for (int i = 0; i < length; i++) {
    outputArray[i] = (inputArray[i] == 1) ? 'X' : '_';
  }
}

void handleServo() {
  int irValue = digitalRead(irPin);

  if (irValue == LOW) {
    if (!servoIsOpen) {
      myServo.write(90);
      servoOpenTime = millis();
      servoIsOpen = true;
    }
  }

  if (servoIsOpen && millis() - servoOpenTime >= 1500) {
    if (digitalRead(irPin) == HIGH) {
      myServo.write(0);
      servoIsOpen = false;
    } else {
      servoOpenTime = millis();
    }
  }
}

void lcdChange(int inputArray[], int length) {
  char s[length];
  convertToChars(inputArray, s, length);

  char r1[17];
  char r2[17];
  sprintf(r1, "1:%c 2:%c 3:%c 4:%c", s[0], s[1], s[2], s[3]);
  sprintf(r2, "5:%c 6:%c 7:%c 8:%c", s[4], s[5], s[6], s[7]);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(r1);
  lcd.setCursor(0, 1);
  lcd.print(r2);
}

void handleStatus() {
  String body = server.arg("plain");

  StaticJsonDocument<200> doc;
  deserializeJson(doc, body);

  if (doc.containsKey("clear") && doc["clear"] == 1) {
    lcd.clear();
  }

  if (doc.containsKey("slots")) {
    JsonArray slots = doc["slots"].as<JsonArray>();
    int length = slots.size();
    int slotsArr[length];
    for (int i = 0; i < length; i++) {
      slotsArr[i] = slots[i];
    }
    lcdChange(slotsArr, length);
  }

  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void setup() {
  Serial.begin(115200);

  lcd.init();
  lcd.backlight();
  lcd.print("Connecting...");

  pinMode(irPin, INPUT);
  myServo.attach(servoPin);
  myServo.write(0);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  Serial.println("Connected to WiFi!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin(hostname)) {
    Serial.println("mDNS started");
  }

  lcd.clear();

  server.on("/status", HTTP_POST, handleStatus);
  server.begin();
}

void loop() {
  server.handleClient();
  handleServo();
}
