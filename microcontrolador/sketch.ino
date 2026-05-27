#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// =======================================================
// CONFIGURAÇÕES DE WI-FI DO WOKWI
// =======================================================
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// =======================================================
// CONFIGURAÇÕES MQTT
// =======================================================
const char* mqttServer = "broker.hivemq.com";
const int mqttPort = 1883;
const char* mqttTopic = "ecosense/santiago/leituras";

// =======================================================
// IDENTIFICAÇÃO DOS SENSORES SIMULADOS
// =======================================================
const int TOTAL_SENSORES = 4;

const char* sensores[TOTAL_SENSORES] = {
  "SALA_AULA_01",
  "LABORATORIO_01",
  "SALA_TECNICA_01",
  "ALMOXARIFADO_01"
};

// =======================================================
// DHT22
// =======================================================
#define DHTPIN 15
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// =======================================================
// PINOS DO CIRCUITO
// =======================================================
#define PINO_CO2 34
#define PINO_LUMINOSIDADE 35

#define LED_VERDE_GERAL 26
#define LED_VERMELHO_GERAL 27
#define BUZZER 25

// LEDs individuais por ambiente
#define LED_SALA_AULA 18
#define LED_LABORATORIO 19
#define LED_SALA_TECNICA 21
#define LED_ALMOXARIFADO 22

// =======================================================
// LIMITES DE ALERTA
// =======================================================
const float LIMITE_TEMPERATURA = 30.0;
const float LIMITE_UMIDADE = 80.0;
const int LIMITE_CO2 = 1000;
const int LIMITE_LUMINOSIDADE_BAIXA = 200;

// =======================================================
// CONTROLE DE ENVIO E BUZZER
// =======================================================
// 5000 ms = 5 segundos
const unsigned long INTERVALO_ENVIO = 5000;

unsigned long ultimoEnvio = 0;
bool primeiraLeitura = true;

const bool BUZZER_ATIVO = true;
String ultimoStatusGeral = "NORMAL";

// =======================================================
// OBJETOS DE CONEXÃO
// =======================================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// =======================================================
// CONECTAR AO WI-FI
// =======================================================
void conectarWiFi() {
  Serial.println();
  Serial.println("Conectando ao Wi-Fi do Wokwi...");
  Serial.print("SSID: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int tentativas = 0;

  while (WiFi.status() != WL_CONNECTED && tentativas < 40) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi conectado com sucesso!");
    Serial.print("IP local: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Falha ao conectar ao Wi-Fi.");
    Serial.print("Status Wi-Fi: ");
    Serial.println(WiFi.status());
  }
}

// =======================================================
// CONECTAR AO BROKER MQTT
// =======================================================
void conectarMQTT() {
  mqttClient.setServer(mqttServer, mqttPort);

  while (!mqttClient.connected()) {
    Serial.println();
    Serial.println("Conectando ao broker MQTT...");

    String clientId = "EcoSenseESP32-";
    clientId += String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("Conectado ao broker MQTT!");
      Serial.print("Tópico de publicação: ");
      Serial.println(mqttTopic);
    } else {
      Serial.print("Falha MQTT. Estado: ");
      Serial.println(mqttClient.state());
      Serial.println("Tentando novamente em 3 segundos...");
      delay(3000);
    }
  }
}

// =======================================================
// DEFINIR STATUS
// =======================================================
String definirStatus(float temperatura, float umidade, int co2, int luminosidade) {
  if (temperatura > LIMITE_TEMPERATURA) {
    return "ALERTA";
  }

  if (umidade > LIMITE_UMIDADE) {
    return "ALERTA";
  }

  if (co2 > LIMITE_CO2) {
    return "ALERTA";
  }

  if (luminosidade < LIMITE_LUMINOSIDADE_BAIXA) {
    return "ALERTA";
  }

  return "NORMAL";
}

// =======================================================
// IDENTIFICAR MOTIVO DO ALERTA
// =======================================================
String identificarMotivoAlerta(float temperatura, float umidade, int co2, int luminosidade) {
  String motivo = "";

  if (temperatura > LIMITE_TEMPERATURA) {
    motivo += "TEMPERATURA_ALTA ";
  }

  if (umidade > LIMITE_UMIDADE) {
    motivo += "UMIDADE_ALTA ";
  }

  if (co2 > LIMITE_CO2) {
    motivo += "CO2_ALTO ";
  }

  if (luminosidade < LIMITE_LUMINOSIDADE_BAIXA) {
    motivo += "LUMINOSIDADE_BAIXA ";
  }

  if (motivo == "") {
    motivo = "SEM_ALERTA";
  }

  motivo.trim();
  return motivo;
}

// =======================================================
// ATUALIZAR STATUS GERAL
// =======================================================
void atualizarAtuadoresGerais(String statusGeral) {
  if (statusGeral == "ALERTA") {
    digitalWrite(LED_VERDE_GERAL, LOW);
    digitalWrite(LED_VERMELHO_GERAL, HIGH);

    // Bipe curto apenas quando muda de NORMAL para ALERTA
    if (BUZZER_ATIVO && ultimoStatusGeral != "ALERTA") {
      tone(BUZZER, 1000);
      delay(250);
      noTone(BUZZER);
    }

  } else {
    digitalWrite(LED_VERDE_GERAL, HIGH);
    digitalWrite(LED_VERMELHO_GERAL, LOW);
    noTone(BUZZER);
  }

  ultimoStatusGeral = statusGeral;
}

// =======================================================
// ATUALIZAR LED INDIVIDUAL POR SENSOR
// =======================================================
void atualizarLedSensor(int indiceSensor, String status) {
  int pinoLed = -1;

  if (indiceSensor == 0) {
    pinoLed = LED_SALA_AULA;
  } else if (indiceSensor == 1) {
    pinoLed = LED_LABORATORIO;
  } else if (indiceSensor == 2) {
    pinoLed = LED_SALA_TECNICA;
  } else if (indiceSensor == 3) {
    pinoLed = LED_ALMOXARIFADO;
  }

  if (pinoLed == -1) {
    return;
  }

  if (status == "ALERTA") {
    digitalWrite(pinoLed, HIGH);
  } else {
    digitalWrite(pinoLed, LOW);
  }
}

// =======================================================
// GARANTIR LIMITES DE VALORES
// =======================================================
void limitarValores(float &temperatura, float &umidade, int &co2, int &luminosidade) {
  if (temperatura < 0) {
    temperatura = 0;
  }

  if (temperatura > 60) {
    temperatura = 60;
  }

  if (umidade < 0) {
    umidade = 0;
  }

  if (umidade > 100) {
    umidade = 100;
  }

  if (co2 < 300) {
    co2 = 300;
  }

  if (co2 > 1500) {
    co2 = 1500;
  }

  if (luminosidade < 0) {
    luminosidade = 0;
  }

  if (luminosidade > 1000) {
    luminosidade = 1000;
  }
}

// =======================================================
// GERAR LEITURA POR SENSOR
// =======================================================
void gerarLeituraPorSensor(
  int indiceSensor,
  float &temperatura,
  float &umidade,
  int &co2,
  int &luminosidade
) {
  unsigned long tempoSegundos = millis() / 1000;

  // A cada 20 segundos muda a fase do ambiente.
  int fase = (tempoSegundos / 20) % 6;

  int variacaoTemp = random(-10, 11);
  int variacaoUmidade = random(-5, 6);
  int variacaoCO2 = random(-40, 41);
  int variacaoLuz = random(-50, 51);

  // SENSOR 0 - SALA DE AULA
  // Normalmente estável, mas pode ter CO2 alto em alguns ciclos.
  if (indiceSensor == 0) {
    temperatura = 26.0 + (variacaoTemp / 10.0);
    umidade = 62.0 + variacaoUmidade;
    luminosidade = 700 + variacaoLuz;

    if (fase == 3) {
      co2 = 1080 + variacaoCO2;
    } else {
      co2 = 760 + variacaoCO2;
    }
  }

  // SENSOR 1 - LABORATÓRIO
  // Pode apresentar temperatura alta.
  else if (indiceSensor == 1) {
    if (fase == 1) {
      temperatura = 33.0 + (variacaoTemp / 10.0);
    } else {
      temperatura = 27.0 + (variacaoTemp / 10.0);
    }

    umidade = 65.0 + variacaoUmidade;
    co2 = 820 + variacaoCO2;
    luminosidade = 650 + variacaoLuz;
  }

  // SENSOR 2 - SALA TÉCNICA
  // Simula ambiente com equipamentos, podendo aquecer mais.
  else if (indiceSensor == 2) {
    if (fase == 1 || fase == 2 || fase == 3) {
      temperatura = 34.0 + (variacaoTemp / 10.0);
    } else {
      temperatura = 29.0 + (variacaoTemp / 10.0);
    }

    umidade = 55.0 + variacaoUmidade;
    co2 = 780 + variacaoCO2;
    luminosidade = 500 + variacaoLuz;
  }

  // SENSOR 3 - ALMOXARIFADO
  // Pode apresentar umidade alta e baixa luminosidade.
  else if (indiceSensor == 3) {
    temperatura = 25.0 + (variacaoTemp / 10.0);
    co2 = 720 + variacaoCO2;

    if (fase == 4) {
      umidade = 87.0 + variacaoUmidade;
    } else {
      umidade = 68.0 + variacaoUmidade;
    }

    if (fase == 5) {
      luminosidade = 120 + variacaoLuz;
    } else {
      luminosidade = 480 + variacaoLuz;
    }
  }

  limitarValores(temperatura, umidade, co2, luminosidade);
}

// =======================================================
// PUBLICAR UMA LEITURA NO MQTT
// =======================================================
void publicarLeitura(
  const char* sensorIdAtual,
  float temperatura,
  float umidade,
  int co2,
  int luminosidade,
  String status,
  String motivoAlerta
) {
  if (!mqttClient.connected()) {
    conectarMQTT();
  }

  String json = "{";
  json += "\"sensor_id\":\"" + String(sensorIdAtual) + "\",";
  json += "\"temperatura\":" + String(temperatura, 2) + ",";
  json += "\"umidade\":" + String(umidade, 2) + ",";
  json += "\"co2\":" + String(co2) + ",";
  json += "\"luminosidade\":" + String(luminosidade);
  json += "}";

  Serial.println();
  Serial.println("Publicando leitura MQTT...");
  Serial.print("Sensor: ");
  Serial.println(sensorIdAtual);
  Serial.print("Tópico: ");
  Serial.println(mqttTopic);
  Serial.print("JSON: ");
  Serial.println(json);
  Serial.print("Status local: ");
  Serial.println(status);
  Serial.print("Motivo: ");
  Serial.println(motivoAlerta);

  bool publicado = mqttClient.publish(mqttTopic, json.c_str());

  if (publicado) {
    Serial.println("Mensagem MQTT publicada com sucesso.");
  } else {
    Serial.println("Falha ao publicar mensagem MQTT.");
  }
}

// =======================================================
// SETUP
// =======================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  randomSeed(analogRead(33));

  pinMode(PINO_CO2, INPUT);
  pinMode(PINO_LUMINOSIDADE, INPUT);

  pinMode(LED_VERDE_GERAL, OUTPUT);
  pinMode(LED_VERMELHO_GERAL, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  pinMode(LED_SALA_AULA, OUTPUT);
  pinMode(LED_LABORATORIO, OUTPUT);
  pinMode(LED_SALA_TECNICA, OUTPUT);
  pinMode(LED_ALMOXARIFADO, OUTPUT);

  digitalWrite(LED_VERDE_GERAL, LOW);
  digitalWrite(LED_VERMELHO_GERAL, LOW);

  digitalWrite(LED_SALA_AULA, LOW);
  digitalWrite(LED_LABORATORIO, LOW);
  digitalWrite(LED_SALA_TECNICA, LOW);
  digitalWrite(LED_ALMOXARIFADO, LOW);

  noTone(BUZZER);

  dht.begin();
  delay(2000);

  Serial.println("======================================");
  Serial.println("EcoSense IoT - ESP32 + MQTT");
  Serial.println("Modo: Rede com multiplos sensores simulados");
  Serial.println("LEDs individuais por ambiente ativados");
  Serial.println("Envio: primeiro ciclo imediato e depois a cada 5 segundos");
  Serial.println("======================================");

  conectarWiFi();
  conectarMQTT();
}

// =======================================================
// LOOP PRINCIPAL
// =======================================================
void loop() {
  mqttClient.loop();

  unsigned long agora = millis();

  if (primeiraLeitura || agora - ultimoEnvio >= INTERVALO_ENVIO) {
    ultimoEnvio = agora;
    primeiraLeitura = false;

    bool existeAlerta = false;

    Serial.println();
    Serial.println("========================================");
    Serial.println("INICIANDO CICLO DE LEITURAS MULTISSENSOR");
    Serial.println("========================================");

    for (int i = 0; i < TOTAL_SENSORES; i++) {
      float temperatura = 0;
      float umidade = 0;
      int co2 = 0;
      int luminosidade = 0;

      gerarLeituraPorSensor(
        i,
        temperatura,
        umidade,
        co2,
        luminosidade
      );

      String status = definirStatus(
        temperatura,
        umidade,
        co2,
        luminosidade
      );

      String motivoAlerta = identificarMotivoAlerta(
        temperatura,
        umidade,
        co2,
        luminosidade
      );

      atualizarLedSensor(i, status);

      if (status == "ALERTA") {
        existeAlerta = true;
      }

      Serial.println();
      Serial.println("--------- LEITURA MULTISSENSOR ---------");
      Serial.print("Sensor ID: ");
      Serial.println(sensores[i]);

      Serial.print("Temperatura: ");
      Serial.print(temperatura);
      Serial.println(" °C");

      Serial.print("Umidade: ");
      Serial.print(umidade);
      Serial.println(" %");

      Serial.print("CO2: ");
      Serial.print(co2);
      Serial.println(" ppm");

      Serial.print("Luminosidade: ");
      Serial.println(luminosidade);

      Serial.print("Status: ");
      Serial.println(status);

      Serial.print("Motivo: ");
      Serial.println(motivoAlerta);

      Serial.println("----------------------------------------");

      publicarLeitura(
        sensores[i],
        temperatura,
        umidade,
        co2,
        luminosidade,
        status,
        motivoAlerta
      );

      // Pequeno intervalo para não publicar as 4 mensagens totalmente coladas.
      delay(50);
    }

    if (existeAlerta) {
      atualizarAtuadoresGerais("ALERTA");
      Serial.println();
      Serial.println("STATUS GERAL DO AMBIENTE: ALERTA");
      Serial.println("LED vermelho geral acionado.");
      Serial.println("Um ou mais LEDs individuais indicam o ambiente em alerta.");
    } else {
      atualizarAtuadoresGerais("NORMAL");
      Serial.println();
      Serial.println("STATUS GERAL DO AMBIENTE: NORMAL");
      Serial.println("LED verde geral acionado.");
    }

    Serial.println("========================================");
    Serial.println("FIM DO CICLO DE LEITURAS");
    Serial.println("========================================");
  }
}