import requests
import pandas as pd


API_BASE_URL = "http://127.0.0.1:8050"


def buscar_leituras(limite: int = 500) -> pd.DataFrame:
    """
    Busca as leituras registradas na API e retorna um DataFrame Pandas.
    """
    try:
        resposta = requests.get(
            f"{API_BASE_URL}/leituras",
            params={"limite": limite},
            timeout=5
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if not dados:
            return pd.DataFrame()

        df = pd.DataFrame(dados)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        colunas_numericas = [
            "temperatura",
            "umidade",
            "co2",
            "luminosidade"
        ]

        for coluna in colunas_numericas:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

        return df

    except requests.exceptions.ConnectionError:
        return pd.DataFrame()

    except requests.exceptions.Timeout:
        return pd.DataFrame()

    except requests.exceptions.RequestException:
        return pd.DataFrame()

    except Exception:
        return pd.DataFrame()


def buscar_estatisticas() -> dict:
    """
    Busca estatísticas gerais da API.
    """
    try:
        resposta = requests.get(
            f"{API_BASE_URL}/estatisticas",
            timeout=5
        )

        resposta.raise_for_status()

        return resposta.json()

    except Exception:
        return {
            "total_leituras": 0,
            "total_alertas": 0,
            "sensores_ativos": 0,
            "media_temperatura": 0,
            "media_umidade": 0,
            "media_co2": 0,
            "media_luminosidade": 0
        }


def buscar_ultima_leitura() -> dict | None:
    """
    Busca a última leitura registrada.
    """
    try:
        resposta = requests.get(
            f"{API_BASE_URL}/leituras/ultima",
            timeout=5
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if isinstance(dados, dict) and dados.get("leitura") is None:
            return None

        return dados

    except Exception:
        return None


def limpar_leituras() -> bool:
    """
    Solicita à API a remoção de todas as leituras.
    Usado apenas em ambiente de testes.
    """
    try:
        resposta = requests.delete(
            f"{API_BASE_URL}/leituras",
            timeout=5
        )

        resposta.raise_for_status()

        return True

    except Exception:
        return False