import random
import time
import requests
from datetime import datetime


API_URL = "http://127.0.0.1:8050/leituras"

SENSORES = [
    "ESP32_01",
    "ESP32_02",
    "ESP32_03"
]


def gerar_valor_com_variacao(valor_base: float, variacao: float, minimo: float, maximo: float) -> float:
    """
    Gera um valor com pequena variação em torno de uma base.
    Isso deixa os dados mais realistas para o dashboard.
    """
    valor = valor_base + random.uniform(-variacao, variacao)
    valor = max(minimo, min(valor, maximo))
    return round(valor, 2)


def gerar_leitura_normal(sensor_id: str) -> dict:
    """
    Gera uma leitura considerada normal.
    """
    temperatura = gerar_valor_com_variacao(
        valor_base=random.uniform(24, 29),
        variacao=1.2,
        minimo=20,
        maximo=30
    )

    umidade = gerar_valor_com_variacao(
        valor_base=random.uniform(45, 72),
        variacao=5,
        minimo=35,
        maximo=80
    )

    co2 = gerar_valor_com_variacao(
        valor_base=random.uniform(450, 850),
        variacao=80,
        minimo=300,
        maximo=1000
    )

    luminosidade = gerar_valor_com_variacao(
        valor_base=random.uniform(350, 850),
        variacao=120,
        minimo=50,
        maximo=1000
    )

    return {
        "sensor_id": sensor_id,
        "temperatura": temperatura,
        "umidade": umidade,
        "co2": co2,
        "luminosidade": luminosidade
    }


def gerar_leitura_alerta(sensor_id: str) -> dict:
    """
    Gera uma leitura em alerta.
    O alerta pode ser causado por temperatura, umidade ou CO2.
    """
    tipo_alerta = random.choice([
        "temperatura",
        "umidade",
        "co2",
        "multiplo"
    ])

    temperatura = round(random.uniform(24, 29), 2)
    umidade = round(random.uniform(45, 75), 2)
    co2 = round(random.uniform(450, 900), 2)
    luminosidade = round(random.uniform(250, 900), 2)

    if tipo_alerta == "temperatura":
        temperatura = round(random.uniform(31, 39), 2)

    elif tipo_alerta == "umidade":
        umidade = round(random.uniform(81, 95), 2)

    elif tipo_alerta == "co2":
        co2 = round(random.uniform(1001, 1400), 2)

    elif tipo_alerta == "multiplo":
        temperatura = round(random.uniform(31, 39), 2)
        umidade = round(random.uniform(81, 95), 2)
        co2 = round(random.uniform(1001, 1400), 2)

    return {
        "sensor_id": sensor_id,
        "temperatura": temperatura,
        "umidade": umidade,
        "co2": co2,
        "luminosidade": luminosidade
    }


def gerar_leitura() -> dict:
    """
    Gera uma leitura aleatória.
    A maior parte será normal, mas algumas serão alertas.
    """
    sensor_id = random.choice(SENSORES)

    chance_alerta = random.randint(1, 100)

    if chance_alerta <= 25:
        return gerar_leitura_alerta(sensor_id)

    return gerar_leitura_normal(sensor_id)


def enviar_leitura(dados: dict) -> bool:
    """
    Envia uma leitura para a API FastAPI.
    """
    try:
        resposta = requests.post(
            API_URL,
            json=dados,
            timeout=5
        )

        resposta.raise_for_status()

        retorno = resposta.json()

        leitura = retorno.get("leitura", {})
        status = leitura.get("status", "DESCONHECIDO")

        agora = datetime.now().strftime("%H:%M:%S")

        print(
            f"[{agora}] Enviado para API | "
            f"Sensor: {dados['sensor_id']} | "
            f"Temp: {dados['temperatura']} °C | "
            f"Umidade: {dados['umidade']} % | "
            f"CO2: {dados['co2']} ppm | "
            f"Luz: {dados['luminosidade']} | "
            f"Status: {status}"
        )

        return True

    except requests.exceptions.ConnectionError:
        print(
            "Erro: não foi possível conectar à API. "
            "Verifique se ela está rodando em http://127.0.0.1:8050"
        )
        return False

    except requests.exceptions.Timeout:
        print("Erro: tempo limite excedido ao tentar enviar dados para a API.")
        return False

    except requests.exceptions.HTTPError as erro:
        print(f"Erro HTTP ao enviar dados: {erro}")
        return False

    except Exception as erro:
        print(f"Erro inesperado ao enviar dados: {erro}")
        return False


def iniciar_simulador(intervalo_segundos: int = 3):
    """
    Inicia o simulador em loop.
    """
    print("=" * 80)
    print("EcoSense IoT - Simulador de Sensores")
    print("=" * 80)
    print(f"API destino: {API_URL}")
    print(f"Intervalo de envio: {intervalo_segundos} segundos")
    print("Pressione CTRL + C para encerrar.")
    print("=" * 80)

    while True:
        dados = gerar_leitura()
        enviar_leitura(dados)
        time.sleep(intervalo_segundos)


if __name__ == "__main__":
    try:
        iniciar_simulador(intervalo_segundos=3)
    except KeyboardInterrupt:
        print()
        print("Simulador encerrado pelo usuário.")