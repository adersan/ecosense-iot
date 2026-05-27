from pydantic import BaseModel, Field


class LeituraEntrada(BaseModel):
    sensor_id: str = Field(
        ...,
        example="ESP32_01",
        description="Identificação do microcontrolador ou sensor IoT"
    )

    temperatura: float = Field(
        ...,
        example=28.5,
        description="Temperatura em graus Celsius"
    )

    umidade: float = Field(
        ...,
        example=65.0,
        description="Umidade relativa do ar em porcentagem"
    )

    co2: float = Field(
        ...,
        example=750,
        description="Nível de CO2 simulado em ppm"
    )

    luminosidade: float = Field(
        ...,
        example=600,
        description="Luminosidade simulada do ambiente"
    )


class LeituraSaida(BaseModel):
    id: int
    sensor_id: str
    timestamp: str
    temperatura: float
    umidade: float
    co2: float
    luminosidade: float
    status: str