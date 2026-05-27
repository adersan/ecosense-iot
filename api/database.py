import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path("data/ecosense.db")


def conectar():
    """
    Cria e retorna uma conexão com o banco SQLite.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    """
    Cria a tabela de leituras caso ela ainda não exista.
    """
    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperatura REAL NOT NULL,
            umidade REAL NOT NULL,
            co2 REAL NOT NULL,
            luminosidade REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conexao.commit()
    conexao.close()


def definir_status(
    temperatura: float,
    umidade: float,
    co2: float,
    luminosidade: float = 1000
) -> str:
    """
    Define se a leitura está em estado NORMAL ou ALERTA.
    """
    if temperatura > 30:
        return "ALERTA"

    if umidade > 80:
        return "ALERTA"

    if co2 > 1000:
        return "ALERTA"

    if luminosidade < 200:
        return "ALERTA"

    return "NORMAL"

def salvar_leitura(sensor_id: str, temperatura: float, umidade: float, co2: float, luminosidade: float):
    """
    Salva uma nova leitura no banco de dados.
    """
    criar_banco()

    status = definir_status(
        temperatura=temperatura,
        umidade=umidade,
        co2=co2,
        luminosidade=luminosidade
    )

    timestamp = datetime.now().isoformat(timespec="seconds")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO leituras (
            sensor_id,
            timestamp,
            temperatura,
            umidade,
            co2,
            luminosidade,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        sensor_id,
        timestamp,
        temperatura,
        umidade,
        co2,
        luminosidade,
        status
    ))

    conexao.commit()

    leitura_id = cursor.lastrowid

    conexao.close()

    return {
        "id": leitura_id,
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "temperatura": temperatura,
        "umidade": umidade,
        "co2": co2,
        "luminosidade": luminosidade,
        "status": status
    }


def listar_leituras(limite: int = 500):
    """
    Lista as leituras mais recentes.
    """
    criar_banco()

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            sensor_id,
            timestamp,
            temperatura,
            umidade,
            co2,
            luminosidade,
            status
        FROM leituras
        ORDER BY id DESC
        LIMIT ?
    """, (limite,))

    dados = [dict(linha) for linha in cursor.fetchall()]

    conexao.close()

    return dados


def buscar_ultima_leitura():
    """
    Retorna a leitura mais recente registrada no banco.
    """
    criar_banco()

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            id,
            sensor_id,
            timestamp,
            temperatura,
            umidade,
            co2,
            luminosidade,
            status
        FROM leituras
        ORDER BY id DESC
        LIMIT 1
    """)

    linha = cursor.fetchone()

    conexao.close()

    if linha is None:
        return None

    return dict(linha)


def obter_estatisticas():
    """
    Retorna estatísticas gerais para o dashboard.
    """
    criar_banco()

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM leituras")
    total_leituras = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM leituras WHERE status = 'ALERTA'")
    total_alertas = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT sensor_id) AS total FROM leituras")
    sensores_ativos = cursor.fetchone()["total"]

    cursor.execute("SELECT AVG(temperatura) AS media FROM leituras")
    media_temperatura = cursor.fetchone()["media"]

    cursor.execute("SELECT AVG(umidade) AS media FROM leituras")
    media_umidade = cursor.fetchone()["media"]

    cursor.execute("SELECT AVG(co2) AS media FROM leituras")
    media_co2 = cursor.fetchone()["media"]

    cursor.execute("SELECT AVG(luminosidade) AS media FROM leituras")
    media_luminosidade = cursor.fetchone()["media"]

    conexao.close()

    return {
        "total_leituras": total_leituras,
        "total_alertas": total_alertas,
        "sensores_ativos": sensores_ativos,
        "media_temperatura": round(media_temperatura or 0, 2),
        "media_umidade": round(media_umidade or 0, 2),
        "media_co2": round(media_co2 or 0, 2),
        "media_luminosidade": round(media_luminosidade or 0, 2)
    }


def limpar_leituras():
    """
    Apaga todas as leituras do banco.
    Útil apenas para testes.
    """
    criar_banco()

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM leituras")
    conexao.commit()

    conexao.close()

    return {
        "mensagem": "Todas as leituras foram apagadas com sucesso."
    }