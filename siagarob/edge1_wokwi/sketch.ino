/*
  SiagaRob - Edge 1: Pos Air (Kolam Retensi Tanjung Mas)
  Board   : ESP32 DevKit v4 (Wokwi)
  Sensors : HC-SR04
  Output  : LED status pada GPIO 2

  Kontrak MQTT mengikuti PRD SiagaRob.
  PENTING: samakan PROJECT_ID dengan Edge 2, ai_server.py, dan dashboard/index.html.
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <math.h>

// -------------------- Identitas proyek --------------------
const char* PROJECT_ID = "siagarob_1739233";
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;

// -------------------- Pin Edge 1 --------------------
constexpr uint8_t TRIG_PIN = 5;
constexpr uint8_t ECHO_PIN = 18;
constexpr uint8_t LED_PIN = 2;

// Sensor dipasang 200 cm dari dasar acuan, sesuai PRD.
constexpr float SENSOR_HEIGHT_CM = 200.0f;
constexpr uint8_t MEDIAN_READINGS = 5;
constexpr uint8_t MIN_VALID_READINGS = 3;
constexpr uint32_t ECHO_TIMEOUT_US = 30000UL;
constexpr uint32_t PUBLISH_INTERVAL_MS = 2000UL; // 2 detik nyata = 1 menit simulasi
constexpr uint32_t RECONNECT_INTERVAL_MS = 3000UL;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

String topicPrefix;
String telemetryTopic;
String statusTopic;
String mqttClientId;

uint32_t lastPublishMs = 0;
uint32_t lastWifiAttemptMs = 0;
uint32_t lastMqttAttemptMs = 0;
uint32_t ledTurnOffAtMs = 0;
uint32_t sequenceNumber = 0;

float lastValidLevelCm = 0.0f;
float lastObservedLevelCm = 0.0f;
float lastRateCmMin = 0.0f;
bool hasValidLevel = false;
bool hasObservedLevel = false;
bool statusLedOn = false;

// Menyimpan enam sampel agar laju dihitung dari sampel sekarang
// dikurangi sampel lima interval sebelumnya, lalu dibagi lima.
float levelHistory[6] = {0, 0, 0, 0, 0, 0};
uint8_t levelHistoryCount = 0;

void resetRateHistory() {
  levelHistoryCount = 0;
  lastRateCmMin = 0.0f;
}

void addValidLevelToHistory(float levelCm) {
  if (levelHistoryCount < 6) {
    levelHistory[levelHistoryCount++] = levelCm;
  } else {
    for (uint8_t i = 0; i < 5; i++) {
      levelHistory[i] = levelHistory[i + 1];
    }
    levelHistory[5] = levelCm;
  }

  if (levelHistoryCount >= 6) {
    lastRateCmMin = (levelHistory[5] - levelHistory[0]) / 5.0f;
  } else {
    lastRateCmMin = 0.0f;
  }
}

// Ambil lima pembacaan jarak dan gunakan median dari pembacaan yang valid.
// Pembacaan di luar 2-400 cm atau timeout tidak digunakan.
bool readMedianDistanceCm(float &medianDistanceCm) {
  float validReadings[MEDIAN_READINGS];
  uint8_t validCount = 0;

  for (uint8_t i = 0; i < MEDIAN_READINGS; i++) {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
    if (duration > 0) {
      float distanceCm = (duration * 0.0343f) / 2.0f;
      if (distanceCm >= 2.0f && distanceCm <= 400.0f) {
        validReadings[validCount++] = distanceCm;
      }
    }
    delay(25);
  }

  if (validCount < MIN_VALID_READINGS) {
    return false;
  }

  // Insertion sort, cukup untuk maksimal lima nilai.
  for (uint8_t i = 1; i < validCount; i++) {
    float key = validReadings[i];
    int8_t j = static_cast<int8_t>(i) - 1;
    while (j >= 0 && validReadings[j] > key) {
      validReadings[j + 1] = validReadings[j];
      j--;
    }
    validReadings[j + 1] = key;
  }

  if (validCount % 2 == 1) {
    medianDistanceCm = validReadings[validCount / 2];
  } else {
    medianDistanceCm = (validReadings[validCount / 2 - 1] +
                        validReadings[validCount / 2]) / 2.0f;
  }
  return true;
}

void connectMqttIfNeeded() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) {
    return;
  }

  uint32_t now = millis();
  if (now - lastMqttAttemptMs < RECONNECT_INTERVAL_MS) {
    return;
  }
  lastMqttAttemptMs = now;

  Serial.print("Menghubungkan ke MQTT: ");
  Serial.println(MQTT_HOST);

  // Last Will: broker menerbitkan "offline" retained jika koneksi terputus.
  bool connected = mqtt.connect(
    mqttClientId.c_str(),
    statusTopic.c_str(),
    1,
    true,
    "offline"
  );

  if (connected) {
    mqtt.publish(statusTopic.c_str(), "online", true);
    Serial.println("MQTT tersambung; status online dipublikasikan.");
  } else {
    Serial.print("MQTT gagal, state=");
    Serial.println(mqtt.state());
  }
}

void maintainConnections() {
  uint32_t now = millis();

  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiAttemptMs >= RECONNECT_INTERVAL_MS) {
      lastWifiAttemptMs = now;
      Serial.println("Wi-Fi terputus; mencoba menyambungkan ulang...");
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
    }
    return;
  }

  connectMqttIfNeeded();
  if (mqtt.connected()) {
    mqtt.loop();
  }
}

void pulseStatusLed() {
  uint32_t now = millis();
  if (statusLedOn && static_cast<int32_t>(now - ledTurnOffAtMs) >= 0) {
    digitalWrite(LED_PIN, LOW);
    statusLedOn = false;
  }
}

void sampleAndPublishTelemetry() {
  float distanceCm = 0.0f;
  bool sensorOk = readMedianDistanceCm(distanceCm);

  if (sensorOk) {
    float candidateLevelCm = SENSOR_HEIGHT_CM - distanceCm;

    // Tolak satu sampel jika melonjak >50 cm dari pengamatan sebelumnya.
    // Nilai level valid terakhir tetap dipakai pada payload sampel ini.
    if (hasObservedLevel && fabsf(candidateLevelCm - lastObservedLevelCm) > 50.0f) {
      sensorOk = false;
      lastObservedLevelCm = candidateLevelCm;
      resetRateHistory();
      Serial.println("Peringatan: lonjakan level >50 cm; sampel ditandai tidak valid.");
    } else {
      lastObservedLevelCm = candidateLevelCm;
      hasObservedLevel = true;
      lastValidLevelCm = candidateLevelCm;
      hasValidLevel = true;
      addValidLevelToHistory(candidateLevelCm);
    }
  }

  float levelToPublish = hasValidLevel ? lastValidLevelCm : 0.0f;
  float rateToPublish = lastRateCmMin;

  StaticJsonDocument<256> doc;
  doc["device_id"] = "edge1";
  doc["seq"] = ++sequenceNumber;
  doc["level_cm"] = levelToPublish;
  doc["rate_cm_min"] = rateToPublish;
  doc["sensor_ok"] = sensorOk;
  doc["uptime_ms"] = millis();

  char payload[256];
  size_t payloadLength = serializeJson(doc, payload, sizeof(payload));

  if (payloadLength == 0 || !mqtt.publish(telemetryTopic.c_str(), payload)) {
    Serial.println("Telemetri gagal dikirim.");
    return;
  }

  Serial.print("Telemetri Edge 1: ");
  Serial.println(payload);

  digitalWrite(LED_PIN, HIGH);
  statusLedOn = true;
  ledTurnOffAtMs = millis() + 120UL;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  topicPrefix = String("siagarob/") + PROJECT_ID;
  telemetryTopic = topicPrefix + "/edge/edge1/telemetry";
  statusTopic = topicPrefix + "/edge/edge1/status";
  mqttClientId = String("siagarob-edge1-") + PROJECT_ID;

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
  lastWifiAttemptMs = millis();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(5);

  Serial.println("SiagaRob Edge 1 dimulai.");
  Serial.print("Topic telemetri: ");
  Serial.println(telemetryTopic);
}

void loop() {
  maintainConnections();
  pulseStatusLed();

  uint32_t now = millis();
  if (mqtt.connected() && now - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    lastPublishMs = now;
    sampleAndPublishTelemetry();
  }

  delay(5);
}
