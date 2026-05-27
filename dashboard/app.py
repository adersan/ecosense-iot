import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from services import (
    buscar_leituras,
    buscar_estatisticas,
    buscar_ultima_leitura,
    limpar_leituras,
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="EcoSense IoT",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANTES DO SISTEMA
# ============================================================

LIMITE_TEMPERATURA_ALTA = 30.0
LIMITE_UMIDADE_ALTA = 80.0
LIMITE_CO2_ALTO = 1000.0
LIMITE_LUMINOSIDADE_BAIXA = 200.0

COR_NORMAL = "#111827"
COR_ALERTA = "#dc2626"
COR_BAIXO = "#2563eb"
COR_NEUTRO = "#64748b"


# ============================================================
# FUNÇÕES DE FORMATAÇÃO
# ============================================================

def formatar_numero(valor, casas=2):
    try:
        return f"{float(valor):.{casas}f}"
    except (TypeError, ValueError):
        return "0.00"


def formatar_data(valor):
    try:
        data = pd.to_datetime(valor, errors="coerce")
        if pd.isna(data):
            return "Sem data"
        return data.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Sem data"


def tempo_sem_atualizar(timestamp):
    try:
        data = pd.to_datetime(timestamp, errors="coerce")
        if pd.isna(data):
            return "sem informação"

        agora = pd.Timestamp.now()
        segundos = int((agora - data).total_seconds())

        if segundos < 0:
            segundos = 0

        if segundos < 60:
            return f"{segundos} segundo(s)"

        minutos = segundos // 60
        resto_segundos = segundos % 60

        if minutos < 60:
            return f"{minutos} minuto(s) e {resto_segundos} segundo(s)"

        horas = minutos // 60
        resto_minutos = minutos % 60

        return f"{horas} hora(s) e {resto_minutos} minuto(s)"
    except Exception:
        return "sem informação"


def preparar_dataframe(dados) -> pd.DataFrame:
    if dados is None:
        return pd.DataFrame()

    if isinstance(dados, pd.DataFrame):
        df = dados.copy()
    else:
        try:
            df = pd.DataFrame(dados)
        except Exception:
            return pd.DataFrame()

    if df.empty:
        return df

    colunas_esperadas = [
        "sensor_id",
        "timestamp",
        "temperatura",
        "umidade",
        "co2",
        "luminosidade",
        "status",
    ]

    for coluna in colunas_esperadas:
        if coluna not in df.columns:
            if coluna == "status":
                df[coluna] = "NORMAL"
            else:
                df[coluna] = None

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    for coluna in ["temperatura", "umidade", "co2", "luminosidade"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=["timestamp", "sensor_id"])
    df = df.sort_values("timestamp")

    return df


# ============================================================
# REGRAS DE STATUS
# ============================================================

def estado_valor(tipo: str, valor):
    """
    Retorna classe, rótulo, ícone e cor do valor.
    - Acima do limite: vermelho
    - Normal: preto
    - Abaixo do limite: azul
    """
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return {
            "classe": "valor-neutro",
            "rotulo": "Sem dado",
            "icone": "○",
            "cor": COR_NEUTRO,
            "problema": False,
        }

    if tipo == "temperatura" and numero > LIMITE_TEMPERATURA_ALTA:
        return {
            "classe": "valor-alerta",
            "rotulo": "Acima do limite",
            "icone": "⚠️",
            "cor": COR_ALERTA,
            "problema": True,
        }

    if tipo == "umidade" and numero > LIMITE_UMIDADE_ALTA:
        return {
            "classe": "valor-alerta",
            "rotulo": "Acima do limite",
            "icone": "⚠️",
            "cor": COR_ALERTA,
            "problema": True,
        }

    if tipo == "co2" and numero > LIMITE_CO2_ALTO:
        return {
            "classe": "valor-alerta",
            "rotulo": "Acima do limite",
            "icone": "⚠️",
            "cor": COR_ALERTA,
            "problema": True,
        }

    if tipo == "luminosidade" and numero < LIMITE_LUMINOSIDADE_BAIXA:
        return {
            "classe": "valor-baixo",
            "rotulo": "Abaixo do limite",
            "icone": "⬇️",
            "cor": COR_BAIXO,
            "problema": True,
        }

    return {
        "classe": "valor-normal",
        "rotulo": "Normal",
        "icone": "✅",
        "cor": COR_NORMAL,
        "problema": False,
    }


def motivos_alerta(linha) -> list:
    motivos = []

    if estado_valor("temperatura", linha.get("temperatura"))["problema"]:
        motivos.append("Temperatura alta")

    if estado_valor("umidade", linha.get("umidade"))["problema"]:
        motivos.append("Umidade alta")

    if estado_valor("co2", linha.get("co2"))["problema"]:
        motivos.append("CO₂ alto")

    if estado_valor("luminosidade", linha.get("luminosidade"))["problema"]:
        motivos.append("Luminosidade baixa")

    return motivos


def status_visual_linha(linha) -> str:
    return "ALERTA" if motivos_alerta(linha) else "NORMAL"


def formatar_status(status: str) -> str:
    if status == "ALERTA":
        return "🚨 ALERTA"
    if status == "NORMAL":
        return "✅ NORMAL"
    return "○ SEM DADOS"


def classe_status(status: str) -> str:
    if status == "ALERTA":
        return "status-alerta"
    if status == "NORMAL":
        return "status-normal"
    return "status-neutro"


def status_geral(df: pd.DataFrame) -> str:
    if df.empty:
        return "SEM DADOS"

    ultimas = ultima_leitura_por_sensor(df)

    for _, linha in ultimas.iterrows():
        if status_visual_linha(linha) == "ALERTA":
            return "ALERTA"

    return "NORMAL"


# ============================================================
# FILTROS E AGRUPAMENTOS
# ============================================================

def sensores_existentes(df: pd.DataFrame) -> list:
    if df.empty or "sensor_id" not in df.columns:
        return []
    return sorted(df["sensor_id"].dropna().unique().tolist())


def sensores_ativos(df: pd.DataFrame, minutos: int) -> list:
    if df.empty or "timestamp" not in df.columns:
        return []

    limite = pd.Timestamp.now() - pd.Timedelta(minutes=minutos)
    recentes = df[df["timestamp"] >= limite]

    if recentes.empty:
        return []

    return sorted(recentes["sensor_id"].dropna().unique().tolist())


def filtrar_sensor(df: pd.DataFrame, sensor: str) -> pd.DataFrame:
    if df.empty:
        return df

    if sensor == "Todos":
        return df.copy()

    return df[df["sensor_id"] == sensor].copy()


def ultima_leitura_por_sensor(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    return (
        df.sort_values("timestamp")
        .groupby("sensor_id", as_index=False)
        .tail(1)
        .sort_values("sensor_id")
    )


def ultima_leitura(df: pd.DataFrame):
    if df.empty:
        return None
    return df.sort_values("timestamp").iloc[-1]


def adicionar_status_visual(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df_aux = df.copy()
    df_aux["status_visual"] = df_aux.apply(status_visual_linha, axis=1)
    df_aux["motivo_alerta"] = df_aux.apply(
        lambda linha: ", ".join(motivos_alerta(linha)) if motivos_alerta(linha) else "Sem alerta",
        axis=1,
    )
    return df_aux


def filtrar_status(df: pd.DataFrame, status: str) -> pd.DataFrame:
    if df.empty or status == "Todos":
        return df

    df_aux = adicionar_status_visual(df)
    return df_aux[df_aux["status_visual"] == status].copy()


def obter_alertas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    df_aux = adicionar_status_visual(df)
    return df_aux[df_aux["status_visual"] == "ALERTA"].copy()


def taxa_alerta(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    df_aux = adicionar_status_visual(df)
    total = len(df_aux)

    if total == 0:
        return 0.0

    return (len(df_aux[df_aux["status_visual"] == "ALERTA"]) / total) * 100


# ============================================================
# HTML
# ============================================================

def card_valor(titulo: str, valor: str, estado: dict, subtitulo: str = "") -> str:
    subtitulo_html = ""
    if subtitulo:
        subtitulo_html = f'<div class="metric-card-subtitle">{subtitulo}</div>'

    return (
        f'<div class="metric-card-custom">'
        f'<div class="metric-card-title">{titulo}</div>'
        f'<div class="{estado["classe"]}">{valor}</div>'
        f'<div class="metric-card-state" style="color:{estado["cor"]};">'
        f'{estado["icone"]} {estado["rotulo"]}'
        f'</div>'
        f'{subtitulo_html}'
        f'</div>'
    )


def card_sensor(sensor: str, linha, ativo: bool) -> str:
    status = status_visual_linha(linha)
    motivos = motivos_alerta(linha)
    motivos_txt = ", ".join(motivos) if motivos else "Sem alerta"
    tempo = tempo_sem_atualizar(linha.get("timestamp"))

    classe_ativo = "sensor-online" if ativo else "sensor-offline"
    texto_ativo = "ONLINE" if ativo else "SEM ATUALIZAÇÃO"

    return (
        f'<div class="card-sensor">'
        f'<div class="sensor-card-top">'
        f'<div>'
        f'<div class="card-sensor-title">📍 {sensor}</div>'
        f'<div class="small-muted">Última leitura: {formatar_data(linha.get("timestamp"))}</div>'
        f'</div>'
        f'<div class="{classe_ativo}">{texto_ativo}</div>'
        f'</div>'
        f'<div class="{classe_status(status)}">{formatar_status(status)}</div>'
        f'<div class="small-muted">🕒 Sem nova leitura há: <strong>{tempo}</strong></div>'
        f'<div class="small-muted">Motivo: <strong>{motivos_txt}</strong></div>'
        f'</div>'
    )


def relogio_atualizacao(linha, sensor_selecionado: str):
    if linha is None:
        st.markdown(
            '<div class="clock-box-warning">🕒 Nenhuma leitura encontrada.</div>',
            unsafe_allow_html=True,
        )
        return

    tempo = tempo_sem_atualizar(linha.get("timestamp"))
    data = formatar_data(linha.get("timestamp"))

    titulo = "Última atualização geral"
    if sensor_selecionado != "Todos":
        titulo = f"Última atualização de {sensor_selecionado}"

    st.markdown(
        (
            f'<div class="clock-box">'
            f'<div class="clock-title">🕒 {titulo}</div>'
            f'<div class="clock-main">Há {tempo}</div>'
            f'<div class="clock-subtitle">Última leitura registrada em {data}</div>'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# GRÁFICOS E TABELAS
# ============================================================

def grafico_linha(df: pd.DataFrame, y: str, titulo: str, eixo_y: str):
    if df.empty or len(df) < 2:
        return None

    fig = px.line(
        df,
        x="timestamp",
        y=y,
        color="sensor_id",
        markers=True,
        title=titulo,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_traces(line=dict(width=3), marker=dict(size=7))
    fig.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title=eixo_y,
        legend_title="Sensor",
        margin=dict(l=20, r=20, t=55, b=20),
        height=380,
        template="plotly_white",
        transition_duration=0,
        uirevision="ecosense",
    )

    return fig


def grafico_barra_ultima(df: pd.DataFrame, variavel: str, titulo: str, eixo_y: str):
    if df.empty:
        return None

    fig = px.bar(
        df,
        x="sensor_id",
        y=variavel,
        color="status_visual",
        text_auto=True,
        title=titulo,
        color_discrete_map={
            "NORMAL": "#111827",
            "ALERTA": "#dc2626",
            "SEM DADOS": "#64748b",
        },
    )

    fig.update_layout(
        xaxis_title="Sensor",
        yaxis_title=eixo_y,
        legend_title="Status",
        margin=dict(l=20, r=20, t=55, b=20),
        height=360,
        template="plotly_white",
        transition_duration=0,
        uirevision="ecosense",
    )

    return fig


def exibir_grafico(fig, mensagem="Não há dados suficientes para montar o gráfico."):
    if fig is None:
        st.info(mensagem)
    else:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )


def estilizar_dataframe(df: pd.DataFrame):
    def aplicar(valor, coluna):
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return ""

        if coluna == "temperatura" and numero > LIMITE_TEMPERATURA_ALTA:
            return "color: #dc2626; font-weight: 900;"

        if coluna == "umidade" and numero > LIMITE_UMIDADE_ALTA:
            return "color: #dc2626; font-weight: 900;"

        if coluna == "co2" and numero > LIMITE_CO2_ALTO:
            return "color: #dc2626; font-weight: 900;"

        if coluna == "luminosidade" and numero < LIMITE_LUMINOSIDADE_BAIXA:
            return "color: #2563eb; font-weight: 900;"

        return "color: #111827;"

    colunas = [
        coluna for coluna in ["temperatura", "umidade", "co2", "luminosidade"]
        if coluna in df.columns
    ]

    styler = df.style

    for coluna in colunas:
        styler = styler.map(
            lambda valor, col=coluna: aplicar(valor, col),
            subset=[coluna],
        )

    return styler


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.6rem !important;
            padding-bottom: 2rem !important;
        }

        header[data-testid="stHeader"] {
            height: 0rem;
            background: transparent;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        }

        section[data-testid="stSidebar"] > div {
            background: transparent;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
            color: #f8fafc !important;
        }

        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stSlider label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stCheckbox label {
            color: #f8fafc !important;
            font-weight: 700;
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] span,
        section[data-testid="stSidebar"] div[data-baseweb="select"] input {
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
            color: #111827 !important;
            fill: #111827 !important;
        }

        div[data-baseweb="popover"] div,
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] span {
            color: #111827 !important;
            background-color: #ffffff !important;
        }

        .hero-box {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, #ecfdf5 0%, #eff6ff 100%);
            border: 1px solid #dbeafe;
            margin-bottom: 0.8rem;
        }

        .titulo-principal {
            font-size: 2.1rem;
            font-weight: 950;
            color: #0f172a;
            margin-bottom: 0;
            line-height: 1.05;
        }

        .subtitulo {
            font-size: 1rem;
            color: #475569;
            margin-top: 0.15rem;
            margin-bottom: 0.8rem;
        }

        .card-status,
        .card-sensor,
        .metric-card-custom,
        .clock-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        }

        .card-status {
            padding: 1rem 1.1rem;
            border-radius: 1rem;
            margin-bottom: 0.8rem;
        }

        .card-sensor {
            padding: 1rem 1.1rem;
            border-radius: 1rem;
            margin-bottom: 0.9rem;
        }

        .sensor-card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.8rem;
            margin-bottom: 0.5rem;
        }

        .card-sensor-title {
            font-size: 1.1rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .sensor-online {
            background: #dcfce7;
            color: #166534;
            font-size: 0.75rem;
            font-weight: 900;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            border: 1px solid #86efac;
        }

        .sensor-offline {
            background: #fef3c7;
            color: #92400e;
            font-size: 0.75rem;
            font-weight: 900;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            border: 1px solid #fcd34d;
        }

        .status-normal {
            color: #111827;
            font-weight: 950;
            font-size: 1.35rem;
        }

        .status-alerta {
            color: #dc2626;
            font-weight: 950;
            font-size: 1.35rem;
        }

        .status-neutro {
            color: #64748b;
            font-weight: 950;
            font-size: 1.35rem;
        }

        .metric-card-custom {
            padding: 0.8rem 0.95rem;
            border-radius: 0.95rem;
            margin-bottom: 0.5rem;
            min-height: 112px;
        }

        .metric-card-title {
            font-size: 0.85rem;
            color: #475569;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .metric-card-subtitle {
            font-size: 0.78rem;
            color: #64748b;
            margin-top: 0.25rem;
        }

        .metric-card-state {
            font-size: 0.82rem;
            font-weight: 850;
            margin-top: 0.2rem;
        }

        .valor-normal {
            color: #111827;
            font-size: 1.55rem;
            font-weight: 950;
        }

        .valor-alerta {
            color: #dc2626;
            font-size: 1.55rem;
            font-weight: 950;
        }

        .valor-baixo {
            color: #2563eb;
            font-size: 1.55rem;
            font-weight: 950;
        }

        .info-box {
            padding: 0.8rem 1rem;
            border-radius: 0.8rem;
            background-color: #eff6ff;
            border-left: 5px solid #2563eb;
            color: #1e3a8a;
            margin-bottom: 0.8rem;
        }

        .alert-box {
            padding: 0.8rem 1rem;
            border-radius: 0.8rem;
            background-color: #fef2f2;
            border-left: 5px solid #dc2626;
            color: #7f1d1d;
            margin-bottom: 0.8rem;
        }

        .success-box {
            padding: 0.8rem 1rem;
            border-radius: 0.8rem;
            background-color: #f0fdf4;
            border-left: 5px solid #16a34a;
            color: #14532d;
            margin-bottom: 0.8rem;
        }

        .clock-box {
            padding: 0.9rem 1rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
            border: 1px solid #bfdbfe;
            margin-bottom: 0.8rem;
        }

        .clock-box-warning {
            padding: 0.9rem 1rem;
            border-radius: 1rem;
            background: #fff7ed;
            border: 1px solid #fdba74;
            color: #9a3412;
            font-weight: 800;
            margin-bottom: 0.8rem;
        }

        .clock-title {
            font-size: 0.85rem;
            color: #475569;
            font-weight: 800;
        }

        .clock-main {
            font-size: 1.35rem;
            color: #0f172a;
            font-weight: 950;
        }

        .clock-subtitle,
        .small-muted {
            color: #64748b;
            font-size: 0.88rem;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 0.75rem 0.9rem;
            border-radius: 0.9rem;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 800;
            color: #475569;
        }

        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 950;
        }

        hr {
            margin-top: 0.8rem !important;
            margin-bottom: 0.8rem !important;
        }

        h2, h3 {
            margin-top: 0.4rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    (
        '<div class="hero-box">'
        '<h1 class="titulo-principal">🌱 EcoSense IoT</h1>'
        '<p class="subtitulo">'
        'Monitoramento ambiental inteligente com ESP32, MQTT, FastAPI, Pandas, SQLite e dashboard em tempo real.'
        '</p>'
        '</div>'
    ),
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR — CONTROLES ANTES DO AUTOREFRESH
# ============================================================

st.sidebar.title("🌱 EcoSense IoT")
st.sidebar.caption("Painel de controle")

pagina = st.sidebar.radio(
    "Menu",
    options=[
        "🏠 Visão Geral",
        "📡 Sensores Ativos",
        "🚨 Alertas",
        "📈 Histórico",
        "🛠️ Diagnóstico",
    ],
)

st.sidebar.markdown("---")

janela_atividade = st.sidebar.slider(
    "Sensor ativo se enviou nos últimos",
    min_value=1,
    max_value=30,
    value=2,
    step=1,
)

atualizacao_automatica = st.sidebar.checkbox(
    "Atualização automática",
    value=True,
)

intervalo_atualizacao = st.sidebar.selectbox(
    "Atualizar a cada",
    options=[3, 5, 10, 15],
    index=1,
    help="Intervalos muito baixos podem deixar os gráficos cinzas durante o carregamento.",
)

if atualizacao_automatica:
    st_autorefresh(
        interval=intervalo_atualizacao * 1000,
        key="dashboard_ecosense_autorefresh",
    )


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

dados_api = buscar_leituras(limite=1500)
df = preparar_dataframe(dados_api)

try:
    estatisticas = buscar_estatisticas()
except Exception:
    estatisticas = {}

try:
    ultima_leitura_api = buscar_ultima_leitura()
except Exception:
    ultima_leitura_api = None


todos_sensores = sensores_existentes(df)
lista_sensores_ativos = sensores_ativos(df, janela_atividade)
lista_sensores_inativos = [
    sensor for sensor in todos_sensores
    if sensor not in lista_sensores_ativos
]

st.sidebar.markdown("---")

if todos_sensores:
    sensor_selecionado = st.sidebar.selectbox(
        "Ambiente / Sensor",
        options=["Todos"] + todos_sensores,
        help="Escolha um ambiente para mostrar somente os dados dele.",
    )
else:
    sensor_selecionado = "Todos"
    st.sidebar.warning("Nenhum sensor encontrado.")

status_selecionado = st.sidebar.selectbox(
    "Status",
    options=["Todos", "NORMAL", "ALERTA"],
)

st.sidebar.markdown("---")

st.sidebar.subheader("📡 Sensores ativos")

if lista_sensores_ativos:
    for sensor in lista_sensores_ativos:
        st.sidebar.success(sensor)
else:
    st.sidebar.info("Nenhum sensor ativo agora.")

if lista_sensores_inativos:
    with st.sidebar.expander("Sensores sem atualização"):
        for sensor in lista_sensores_inativos:
            st.caption(sensor)

st.sidebar.markdown("---")

habilitar_limpeza = st.sidebar.checkbox("Habilitar limpeza dos dados")

if habilitar_limpeza:
    if st.sidebar.button("🗑️ Apagar todas as leituras"):
        sucesso = limpar_leituras()

        if sucesso:
            st.sidebar.success("Leituras apagadas com sucesso.")
            st.rerun()
        else:
            st.sidebar.error("Erro ao apagar leituras.")


# ============================================================
# VALIDAÇÃO DE DADOS
# ============================================================

if df.empty:
    st.markdown(
        (
            '<div class="alert-box">'
            '<strong>Nenhuma leitura encontrada.</strong><br>'
            'O dashboard está aguardando dados da API. Verifique se a API, a ponte MQTT e o Wokwi estão rodando.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.code(
        """
Terminal 1 - API:
uvicorn api.main:app --reload --port 8050

Terminal 2 - Ponte MQTT:
python api/mqtt_bridge.py

Terminal 3 - Dashboard:
streamlit run dashboard/app.py

Wokwi:
Abrir o projeto ESP32 e clicar em Play.
        """,
        language="powershell",
    )

    st.stop()


# ============================================================
# FILTROS
# ============================================================

df_base = filtrar_sensor(df, sensor_selecionado)
df_base = filtrar_status(df_base, status_selecionado)

if df_base.empty:
    st.markdown(
        (
            '<div class="clock-box-warning">'
            '🕒 Nenhum dado encontrado para o filtro selecionado. '
            'A tela foi mantida ativa, mas não há registros compatíveis no momento.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )
    st.stop()


ultima_contexto = ultima_leitura(df_base)
relogio_atualizacao(ultima_contexto, sensor_selecionado)

df_grafico = df_base.tail(250)
df_ultimas = ultima_leitura_por_sensor(df_base)
df_ultimas = adicionar_status_visual(df_ultimas)

status_contexto = status_geral(df_base)
df_alertas = obter_alertas(df_base)
taxa_contexto = taxa_alerta(df_base)


# ============================================================
# PÁGINA: VISÃO GERAL
# ============================================================

if pagina == "🏠 Visão Geral":
    st.subheader("🏠 Visão geral")

    st.markdown(
        (
            f'<div class="card-status">'
            f'<div>Status geral do contexto selecionado</div>'
            f'<div class="{classe_status(status_contexto)}">{formatar_status(status_contexto)}</div>'
            f'<div class="small-muted">Filtro atual: <strong>{sensor_selecionado}</strong></div>'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    sensores_contexto = sensores_existentes(df_base)

    col1.metric("Sensores no Filtro", len(sensores_contexto))
    col2.metric("Leituras no Filtro", len(df_base))
    col3.metric("Alertas no Filtro", len(df_alertas))
    col4.metric("Taxa de Alerta", f"{taxa_contexto:.1f}%")

    st.markdown("### Última leitura do contexto")

    col5, col6, col7, col8 = st.columns(4)

    temp = ultima_contexto.get("temperatura")
    umi = ultima_contexto.get("umidade")
    co2 = ultima_contexto.get("co2")
    luz = ultima_contexto.get("luminosidade")

    col5.markdown(
        card_valor(
            "Temperatura",
            f"{formatar_numero(temp)} °C",
            estado_valor("temperatura", temp),
            f"Limite: {LIMITE_TEMPERATURA_ALTA} °C",
        ),
        unsafe_allow_html=True,
    )

    col6.markdown(
        card_valor(
            "Umidade",
            f"{formatar_numero(umi)} %",
            estado_valor("umidade", umi),
            f"Limite: {LIMITE_UMIDADE_ALTA}%",
        ),
        unsafe_allow_html=True,
    )

    col7.markdown(
        card_valor(
            "CO₂",
            f"{formatar_numero(co2, 0)} ppm",
            estado_valor("co2", co2),
            f"Limite: {LIMITE_CO2_ALTO} ppm",
        ),
        unsafe_allow_html=True,
    )

    col8.markdown(
        card_valor(
            "Luminosidade",
            f"{formatar_numero(luz, 0)}",
            estado_valor("luminosidade", luz),
            f"Abaixo de {LIMITE_LUMINOSIDADE_BAIXA}: azul",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("📡 Última leitura por sensor")

    st.dataframe(
        estilizar_dataframe(df_ultimas.sort_values("sensor_id")),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("📈 Gráficos recentes")

    aba_temp, aba_umi, aba_co2, aba_luz = st.tabs(
        ["🌡️ Temperatura", "💧 Umidade", "🏭 CO₂", "💡 Luminosidade"]
    )

    with aba_temp:
        exibir_grafico(
            grafico_linha(df_grafico, "temperatura", "Temperatura ao longo do tempo", "Temperatura (°C)")
        )

    with aba_umi:
        exibir_grafico(
            grafico_linha(df_grafico, "umidade", "Umidade ao longo do tempo", "Umidade (%)")
        )

    with aba_co2:
        exibir_grafico(
            grafico_linha(df_grafico, "co2", "CO₂ ao longo do tempo", "CO₂ (ppm)")
        )

    with aba_luz:
        exibir_grafico(
            grafico_linha(df_grafico, "luminosidade", "Luminosidade ao longo do tempo", "Luminosidade")
        )


# ============================================================
# PÁGINA: SENSORES ATIVOS
# ============================================================

elif pagina == "📡 Sensores Ativos":
    st.subheader("📡 Sensores ativos e ambientes")

    st.markdown(
        (
            f'<div class="info-box">'
            f'Sensores ativos são aqueles que enviaram dados nos últimos '
            f'<strong>{janela_atividade} minuto(s)</strong>. '
            f'Quando um sensor para de enviar, o último dado permanece visível com relógio de atualização.'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    col_s1.metric("Sensores Encontrados", len(todos_sensores))
    col_s2.metric("Sensores Ativos", len(lista_sensores_ativos))
    col_s3.metric("Sensores Inativos", len(lista_sensores_inativos))
    col_s4.metric("Alertas no Filtro", len(df_alertas))

    st.markdown("---")
    st.markdown("### Situação atual por ambiente")

    for _, linha in df_ultimas.iterrows():
        sensor = linha.get("sensor_id")
        ativo = sensor in lista_sensores_ativos

        st.markdown(
            card_sensor(sensor, linha, ativo),
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        temp = linha.get("temperatura")
        umi = linha.get("umidade")
        co2 = linha.get("co2")
        luz = linha.get("luminosidade")

        c1.markdown(
            card_valor(
                "Temperatura",
                f"{formatar_numero(temp)} °C",
                estado_valor("temperatura", temp),
                f"Alerta acima de {LIMITE_TEMPERATURA_ALTA} °C",
            ),
            unsafe_allow_html=True,
        )

        c2.markdown(
            card_valor(
                "Umidade",
                f"{formatar_numero(umi)} %",
                estado_valor("umidade", umi),
                f"Alerta acima de {LIMITE_UMIDADE_ALTA}%",
            ),
            unsafe_allow_html=True,
        )

        c3.markdown(
            card_valor(
                "CO₂",
                f"{formatar_numero(co2, 0)} ppm",
                estado_valor("co2", co2),
                f"Alerta acima de {LIMITE_CO2_ALTO} ppm",
            ),
            unsafe_allow_html=True,
        )

        c4.markdown(
            card_valor(
                "Luminosidade",
                f"{formatar_numero(luz, 0)}",
                estado_valor("luminosidade", luz),
                f"Abaixo de {LIMITE_LUMINOSIDADE_BAIXA}: azul",
            ),
            unsafe_allow_html=True,
        )

        dados_sensor = df_base[df_base["sensor_id"] == sensor].sort_values("timestamp", ascending=False)

        with st.expander(f"📋 Histórico recente de {sensor}"):
            st.dataframe(
                estilizar_dataframe(dados_sensor.head(30)),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    st.markdown("### 📈 Gráficos dos sensores")

    aba_geral, aba_temp, aba_umi, aba_co2, aba_luz = st.tabs(
        ["📊 Comparativo", "🌡️ Temperatura", "💧 Umidade", "🏭 CO₂", "💡 Luminosidade"]
    )

    with aba_geral:
        g1, g2 = st.columns(2)

        with g1:
            exibir_grafico(
                grafico_barra_ultima(
                    df_ultimas,
                    "temperatura",
                    "Temperatura atual por sensor",
                    "Temperatura (°C)",
                )
            )

        with g2:
            exibir_grafico(
                grafico_barra_ultima(
                    df_ultimas,
                    "co2",
                    "CO₂ atual por sensor",
                    "CO₂ (ppm)",
                )
            )

        g3, g4 = st.columns(2)

        with g3:
            exibir_grafico(
                grafico_barra_ultima(
                    df_ultimas,
                    "umidade",
                    "Umidade atual por sensor",
                    "Umidade (%)",
                )
            )

        with g4:
            exibir_grafico(
                grafico_barra_ultima(
                    df_ultimas,
                    "luminosidade",
                    "Luminosidade atual por sensor",
                    "Luminosidade",
                )
            )

    with aba_temp:
        exibir_grafico(
            grafico_linha(df_grafico, "temperatura", "Temperatura ao longo do tempo", "Temperatura (°C)")
        )

    with aba_umi:
        exibir_grafico(
            grafico_linha(df_grafico, "umidade", "Umidade ao longo do tempo", "Umidade (%)")
        )

    with aba_co2:
        exibir_grafico(
            grafico_linha(df_grafico, "co2", "CO₂ ao longo do tempo", "CO₂ (ppm)")
        )

    with aba_luz:
        exibir_grafico(
            grafico_linha(df_grafico, "luminosidade", "Luminosidade ao longo do tempo", "Luminosidade")
        )


# ============================================================
# PÁGINA: ALERTAS
# ============================================================

elif pagina == "🚨 Alertas":
    st.subheader("🚨 Central de alertas")

    if df_alertas.empty:
        st.markdown(
            '<div class="success-box">✅ Nenhum alerta encontrado no filtro atual.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            (
                f'<div class="alert-box">'
                f'🚨 Existem <strong>{len(df_alertas)}</strong> leituras em alerta no filtro atual. '
                f'Valores acima do limite ficam em vermelho. Luminosidade baixa fica em azul.'
                f'</div>'
            ),
            unsafe_allow_html=True,
        )

        st.dataframe(
            estilizar_dataframe(df_alertas.sort_values("timestamp", ascending=False)),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        alertas_por_sensor = (
            df_alertas
            .groupby("sensor_id")
            .size()
            .reset_index(name="total_alertas")
            .sort_values("total_alertas", ascending=False)
        )

        fig = px.bar(
            alertas_por_sensor,
            x="sensor_id",
            y="total_alertas",
            text="total_alertas",
            title="Quantidade de alertas por sensor",
            color="total_alertas",
            color_continuous_scale="Reds",
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title="Total de alertas",
            margin=dict(l=20, r=20, t=55, b=20),
            height=380,
            template="plotly_white",
            transition_duration=0,
            uirevision="ecosense",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )


# ============================================================
# PÁGINA: HISTÓRICO
# ============================================================

elif pagina == "📈 Histórico":
    st.subheader("📈 Histórico de leituras")

    col_h1, col_h2 = st.columns(2)

    tipo_grafico = col_h1.selectbox(
        "Variável",
        options=["temperatura", "umidade", "co2", "luminosidade"],
    )

    agrupamento = col_h2.selectbox(
        "Visualização",
        options=["Linha do tempo", "Média por sensor", "Distribuição"],
    )

    if agrupamento == "Linha do tempo":
        exibir_grafico(
            grafico_linha(
                df_grafico,
                tipo_grafico,
                f"{tipo_grafico.upper()} ao longo do tempo",
                tipo_grafico,
            )
        )

    elif agrupamento == "Média por sensor":
        df_media = (
            df_base
            .groupby("sensor_id")[tipo_grafico]
            .mean()
            .reset_index()
            .sort_values(tipo_grafico, ascending=False)
        )

        fig = px.bar(
            df_media,
            x="sensor_id",
            y=tipo_grafico,
            title=f"Média de {tipo_grafico} por sensor",
            text_auto=True,
            color_discrete_sequence=["#2563eb"],
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title=tipo_grafico,
            margin=dict(l=20, r=20, t=55, b=20),
            height=380,
            template="plotly_white",
            transition_duration=0,
            uirevision="ecosense",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )

    elif agrupamento == "Distribuição":
        fig = px.box(
            df_base,
            x="sensor_id",
            y=tipo_grafico,
            title=f"Distribuição de {tipo_grafico} por sensor",
            color="sensor_id",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title=tipo_grafico,
            margin=dict(l=20, r=20, t=55, b=20),
            height=380,
            template="plotly_white",
            transition_duration=0,
            uirevision="ecosense",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )

    st.markdown("---")
    st.subheader("📋 Leituras filtradas")

    st.dataframe(
        estilizar_dataframe(df_base.sort_values("timestamp", ascending=False)),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# PÁGINA: DIAGNÓSTICO
# ============================================================

elif pagina == "🛠️ Diagnóstico":
    st.subheader("🛠️ Diagnóstico do sistema")

    st.markdown(
        (
            '<div class="info-box">'
            'Tela de verificação da API, banco de dados, sensores, atualização e ponte MQTT.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    d1, d2, d3, d4 = st.columns(4)

    d1.metric("Total no Banco", len(df))
    d2.metric("Sensores Encontrados", len(todos_sensores))
    d3.metric("Sensores Ativos", len(lista_sensores_ativos))
    d4.metric("Status Geral", formatar_status(status_contexto))

    st.markdown("---")
    st.subheader("Última leitura recebida")

    if ultima_leitura_api:
        st.json(ultima_leitura_api)
    else:
        st.warning("Nenhuma última leitura retornada pela API.")

    st.markdown("---")
    st.subheader("Sensores encontrados")

    df_sensores = pd.DataFrame({
        "sensor_id": todos_sensores,
        "ativo": [
            "SIM" if sensor in lista_sensores_ativos else "NÃO"
            for sensor in todos_sensores
        ],
    })

    st.dataframe(df_sensores, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Comandos para rodar o projeto")

    st.code(
        """
Terminal 1 - API:
uvicorn api.main:app --reload --port 8050

Terminal 2 - Ponte MQTT:
python api/mqtt_bridge.py

Terminal 3 - Dashboard:
streamlit run dashboard/app.py

Wokwi:
Abrir o projeto ESP32 e clicar em Play.
        """,
        language="powershell",
    )