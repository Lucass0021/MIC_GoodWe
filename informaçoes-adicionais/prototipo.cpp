#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- Wi-Fi (Wokwi)
#define WIFI_SSID     "Wokwi-GUEST"
#define WIFI_PASSWORD ""

// ---------- Firebase (Realtime Database REST)
const char* FIREBASE_HOST = "https://mic-9d88e-default-rtdb.firebaseio.com";
const char* FIREBASE_AUTH = ""; // Se usar auth: "eyJhbGciOi..." (opcional, adicione se regras exigirem)

// ---------- Device ID (MAC Address)
String deviceId = "";

// ---------- Pinos / Simulação (LDR ~ Hall)
#define LDR_PIN 34
const float GAMMA = 0.7;
const float RL10  = 33.0;

// ---------- Elétrica (simulação)
const float TENSAO_REDE = 127.8;    // V
float energia_kwh = 0.0;            // energia acumulada
const float DELTA_T_S = 1.0;        // intervalo base (s)

// ---------- Estado
WiFiClientSecure secureClient;
int valorAnterior = -1;
float corrente = 0, potencia = 0;

void conectawifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando ao WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi OK: " + WiFi.localIP().toString());
  
  // Obtém Device ID (MAC Address limpo)
  deviceId = WiFi.macAddress();
  deviceId.replace(":", ""); // Remove ":" para ID limpo
  Serial.print("Device ID (MAC): ");
  Serial.println(deviceId);
}

void sendDeviceCall() {
  if (WiFi.status() != WL_CONNECTED || deviceId == "") return;

  secureClient.setInsecure(); // Wokwi: ignora certificado

  HTTPClient https;
  String url = String(FIREBASE_HOST) + "/device_calls/" + deviceId + ".json";
  if (FIREBASE_AUTH && strlen(FIREBASE_AUTH) > 0) url += "?auth=" + String(FIREBASE_AUTH);

  if (!https.begin(secureClient, url)) {
    Serial.println("Falha ao iniciar HTTPS (Device Call)");
    return;
  }

  https.addHeader("Content-Type", "application/json");

  // JSON para o chamado
  StaticJsonDocument<128> doc;
  doc["timestamp"] = millis();
  doc["status"] = "pending_registration";
  String payload;
  serializeJson(doc, payload);

  Serial.print("Enviando Device Call para: ");
  Serial.println(url);
  Serial.println("Payload: " + payload);

  int code = https.PUT((uint8_t*)payload.c_str(), payload.length());
  Serial.printf("Device Call -> %d\n", code);
  if (code > 0) {
    Serial.println("Resposta: " + https.getString());
  } else {
    Serial.println("Erro na requisição Device Call.");
  }
  https.end();
}

// PUT em /tomadas/{deviceId}.json (estado atual)
bool putEstadoAtual(const String& jsonPayload) {
  if (WiFi.status() != WL_CONNECTED || deviceId == "") return false;

  secureClient.setInsecure(); // Wokwi: ignora certificado

  HTTPClient https;
  String url = String(FIREBASE_HOST) + "/tomadas/" + deviceId + ".json";
  if (FIREBASE_AUTH && strlen(FIREBASE_AUTH) > 0) url += "?auth=" + String(FIREBASE_AUTH);

  if (!https.begin(secureClient, url)) {
    Serial.println("Falha ao iniciar HTTPS (PUT)");
    return false;
  }

  https.addHeader("Content-Type", "application/json");
  int code = https.PUT((uint8_t*)jsonPayload.c_str(), jsonPayload.length());
  Serial.printf("PUT %s -> %d\n", url.c_str(), code);
  if (code > 0) Serial.println("Resp: " + https.getString());
  https.end();
  return (code == HTTP_CODE_OK);
}

// POST em /tomadas/{deviceId}/historico.json (log)
bool postHistorico(const String& jsonPayload) {
  if (WiFi.status() != WL_CONNECTED || deviceId == "") return false;

  secureClient.setInsecure();

  HTTPClient https;
  String url = String(FIREBASE_HOST) + "/tomadas/" + deviceId + "/historico.json";
  if (FIREBASE_AUTH && strlen(FIREBASE_AUTH) > 0) url += "?auth=" + String(FIREBASE_AUTH);

  if (!https.begin(secureClient, url)) {
    Serial.println("Falha ao iniciar HTTPS (POST)");
    return false;
  }

  https.addHeader("Content-Type", "application/json");
  int code = https.POST((uint8_t*)jsonPayload.c_str(), jsonPayload.length());
  Serial.printf("POST %s -> %d\n", url.c_str(), code);
  if (code > 0) Serial.println("Resp: " + https.getString());
  https.end();
  return (code == HTTP_CODE_OK || code == HTTP_CODE_CREATED);
}

// ---- Simulação do “Hall” via LDR
void simulaSensorHall(float& i_corrente, float& i_potencia) {
  int analogValue = analogRead(LDR_PIN);
  float voltage    = analogValue / 4096.0 * 3.3;
  float resistance = 2000.0 * voltage / (1.0 - voltage / 3.3);
  float lux        = pow(RL10 * 1e3 * pow(10, GAMMA) / resistance, (1.0 / GAMMA));

  // mapeamento fictício: 100 lux ≈ 1 A (limitado a 0-10A para realismo)
  i_corrente = lux / 100.0;
  if (i_corrente < 0) i_corrente = 0;
  if (i_corrente > 10) i_corrente = 10; // Limite realista

  i_potencia = i_corrente * TENSAO_REDE;
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("ESP32 + Wokwi + Firebase RTDB (REST) - Modificado para Device Calls");

  pinMode(LDR_PIN, INPUT);

  conectawifi(); // Conecta WiFi e obtém deviceId

  // Envia chamado inicial após conexão
  sendDeviceCall();
}

unsigned long lastSend = 0;

void loop() {
  // Verifica e reconecta WiFi se necessário
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado, reconectando...");
    conectawifi();
    sendDeviceCall(); // Reenvia chamado após reconexão
    delay(2000);
    return;
  }

  // Leitura/simulação
  simulaSensorHall(corrente, potencia);

  // Energia acumulada (kWh): P (W) * tempo (h) / 1000
  // Nota: Simplificado para intervalo de 1s (DELTA_T_S = 1.0)
  energia_kwh += (potencia / 1000.0) * (DELTA_T_S / 3600.0); // kW * h

  float frequencia = 60.0;
  float pf = 1.0;

  // Monta JSON com ArduinoJson
  StaticJsonDocument<256> doc;
  doc["Voltage"]   = TENSAO_REDE;
  doc["Current"]   = corrente;
  doc["Power"]     = potencia;
  doc["Energy"]    = energia_kwh;
  doc["Frequency"] = frequencia;
  doc["PF"]        = pf;
  doc["ts"]        = (uint32_t)(millis() / 1000);

  String payload;
  serializeJson(doc, payload);

  // Envia a cada 5s
  if (millis() - lastSend > 5000) {
    Serial.println("Enviando JSON: " + payload);

    bool okPut = putEstadoAtual(payload);
    bool okPost = postHistorico(payload); // Comente se não quiser histórico

    Serial.println(okPut ? "Estado atual atualizado." : "Falha no PUT.");
    Serial.println(okPost ? "Registro salvo no historico." : "Falha no POST historico.");
    Serial.println();

    lastSend = millis();
  }

  delay(1000);
}
