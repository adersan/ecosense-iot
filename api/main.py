from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import LeituraEntrada
from api.database import (
    criar_banco,
    salvar_leitura,
    listar_leituras,
    buscar_ultima_leitura,
    obter_estatisticas,
    limpar_leituras
)


app = FastAPI(
    title="EcoSense IoT API",
    description="API para recebimento, armazenamento e consulta de dados ambientais enviados por microcontroladores IoT.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def iniciar_api():
    """
    Executado automaticamente quando a API inicia.
    """
    criar_banco()


@app.get("/")
def home():
    """
    Rota inicial da API.
    """
    return {
        "projeto": "EcoSense IoT",
        "descricao": "API de monitoramento ambiental com microcontrolador, Python e dashboard em tempo real.",
        "status": "online",
        "documentacao": "/docs"
    }


@app.post("/leituras")
def receber_leitura(leitura: LeituraEntrada):
    """
    Recebe uma leitura enviada pelo ESP32 ou por outro dispositivo IoT.
    """
    nova_leitura = salvar_leitura(
        sensor_id=leitura.sensor_id,
        temperatura=leitura.temperatura,
        umidade=leitura.umidade,
        co2=leitura.co2,
        luminosidade=leitura.luminosidade
    )

    return {
        "mensagem": "Leitura recebida com sucesso.",
        "leitura": nova_leitura
    }


@app.get("/leituras")
def obter_leituras(limite: int = 500):
    """
    Retorna as leituras mais recentes armazenadas no banco.
    """
    if limite <= 0:
        raise HTTPException(
            status_code=400,
            detail="O limite deve ser maior que zero."
        )

    dados = listar_leituras(limite=limite)

    return dados


@app.get("/leituras/ultima")
def obter_ultima_leitura():
    """
    Retorna a última leitura registrada.
    """
    leitura = buscar_ultima_leitura()

    if leitura is None:
        return {
            "mensagem": "Nenhuma leitura encontrada.",
            "leitura": None
        }

    return leitura


@app.get("/estatisticas")
def estatisticas():
    """
    Retorna estatísticas gerais das leituras.
    """
    return obter_estatisticas()


@app.delete("/leituras")
def deletar_leituras():
    """
    Apaga todas as leituras.
    Usar apenas em ambiente de teste.
    """
    return limpar_leituras()
