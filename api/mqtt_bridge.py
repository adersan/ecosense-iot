import json
import time
import requests
import paho.mqtt.client as mqtt


MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "ecosense/santiago/leituras"

API_URL = "http://127.0.0.1:8050/leituras"


def enviar_para_api(dados: dict):
    """
    Recebe dados vindos do MQTT e envia para a API FastAPI local.
    """
    try:
        resposta = requests.post(
            API_URL,
            json=dados,
            timeout=5
        )

        resposta.raise_for_status()

        print("✅ Enviado para API com sucesso:")
        print(resposta.json())

    except requests.exceptions.ConnectionError:
        print("❌ Erro: API local não está rodando.")
        print("Verifique se você iniciou:")
        print("uvicorn api.main:app --reload --port 8050")

    except requests.exceptions.HTTPError as erro:
        print("❌ Erro HTTP ao enviar para API:")
        print(erro)
        print("Resposta:", resposta.text)

    except Exception as erro:
        print("❌ Erro inesperado ao enviar para API:")
        print(erro)


def on_connect(client, userdata, flags, rc):
    """
    Executado quando a ponte conecta ao broker MQTT.
    """
    if rc == 0:
        print("✅ Conectado ao broker MQTT.")
        print(f"📡 Inscrito no tópico: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Falha ao conectar ao broker MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    """
    Executado quando chega uma mensagem MQTT.
    """
    print()
    print("=" * 80)
    print("📥 Mensagem MQTT recebida")
    print("Tópico:", msg.topic)

    try:
        payload = msg.payload.decode("utf-8")
        print("Payload bruto:", payload)

        dados = json.loads(payload)

        campos_obrigatorios = [
            "sensor_id",
            "temperatura",
            "umidade",
            "co2",
            "luminosidade"
        ]

        for campo in campos_obrigatorios:
            if campo not in dados:
                print(f"❌ Campo ausente no JSON: {campo}")
                return

        enviar_para_api(dados)

    except json.JSONDecodeError:
        print("❌ Erro: payload recebido não é um JSON válido.")

    except Exception as erro:
        print("❌ Erro ao processar mensagem MQTT:")
        print(erro)

    print("=" * 80)


def iniciar_bridge():
    """
    Inicia a ponte MQTT → API.
    """
    print("=" * 80)
    print("EcoSense IoT - Ponte MQTT para API")
    print("=" * 80)
    print(f"Broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Tópico MQTT: {MQTT_TOPIC}")
    print(f"API destino: {API_URL}")
    print("Pressione CTRL + C para encerrar.")
    print("=" * 80)

    client = mqtt.Client(client_id=f"ecosense-bridge-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


if __name__ == "__main__":
    try:
        iniciar_bridge()
    except KeyboardInterrupt:
        print()
        print("Ponte MQTT encerrada pelo usuário.")
        