import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

from services import (
    buscar_leituras,
    buscar_estatisticas,
    buscar_ultima_leitura,
    limpar_leituras
)


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="EcoSense IoT",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Atualiza automaticamente a página a cada 2 segundos
st_autorefresh(interval=2000, key="dashboard_ecosense")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_numero(valor, casas=2):
    """
    Formata valores numéricos para exibição no dashboard.
    """
    try:
        return f"{float(valor):.{casas}f}"
    except (TypeError, ValueError):
        return "0.00"


def formatar_status(status: str) -> str:
    """
    Retorna o status formatado com ícone.
    """
    if status == "ALERTA":
        return "🚨 ALERTA"

    if status == "NORMAL":
        return "✅ NORMAL"

    return "⚪ SEM DADOS"


def classe_status(status: str) -> str:
    """
    Retorna a classe CSS de acordo com o status.
    """
    if status == "ALERTA":
        return "status-alerta"

    if status == "NORMAL":
        return "status-normal"

    return "status-neutro"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara o DataFrame para uso no dashboard:
    - converte timestamp;
    - converte colunas numéricas;
    - ordena por data/hora.
    """
    if df.empty:
        return df

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

    df = df.dropna(subset=["timestamp"])

    return df.sort_values("timestamp")


def obter_sensores_ativos(df: pd.DataFrame, minutos: int) -> list:
    """
    Retorna somente sensores que enviaram leitura dentro da janela definida.
    """
    if df.empty or "timestamp" not in df.columns:
        return []

    agora = pd.Timestamp.now()
    limite = agora - pd.Timedelta(minutes=minutos)

    df_recentes = df[df["timestamp"] >= limite]

    if df_recentes.empty:
        return []

    return sorted(df_recentes["sensor_id"].dropna().unique().tolist())


def filtrar_por_sensores_ativos(df: pd.DataFrame, sensores_ativos: list) -> pd.DataFrame:
    """
    Filtra o DataFrame mantendo apenas sensores ativos.
    """
    if df.empty or not sensores_ativos:
        return pd.DataFrame()

    return df[df["sensor_id"].isin(sensores_ativos)].copy()


def obter_ultima_leitura_por_sensor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna a última leitura de cada sensor.
    """
    if df.empty:
        return pd.DataFrame()

    df_ordenado = df.sort_values("timestamp")

    return (
        df_ordenado
        .groupby("sensor_id", as_index=False)
        .tail(1)
        .sort_values("sensor_id")
    )


def calcular_status_geral(df_ativos: pd.DataFrame) -> str:
    """
    Define o status geral do sistema com base nos sensores ativos.
    """
    if df_ativos.empty:
        return "SEM DADOS"

    if "ALERTA" in df_ativos["status"].values:
        return "ALERTA"

    return "NORMAL"


def calcular_taxa_alerta(df: pd.DataFrame) -> float:
    """
    Calcula a taxa de alertas em relação ao total de leituras.
    """
    if df.empty:
        return 0.0

    total = len(df)
    alertas = len(df[df["status"] == "ALERTA"])

    if total == 0:
        return 0.0

    return (alertas / total) * 100


def montar_grafico_linha(df: pd.DataFrame, y: str, titulo: str, eixo_y: str):
    """
    Monta gráfico de linha usando Plotly.
    """
    fig = px.line(
        df,
        x="timestamp",
        y=y,
        color="sensor_id",
        markers=True,
        title=titulo
    )

    fig.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title=eixo_y,
        legend_title="Sensor",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def montar_grafico_barra_ultima_leitura(
    df: pd.DataFrame,
    variavel: str,
    titulo: str,
    eixo_y: str
):
    """
    Monta gráfico de barras com a última leitura por sensor.
    """
    fig = px.bar(
        df,
        x="sensor_id",
        y=variavel,
        color="status",
        text_auto=True,
        title=titulo
    )

    fig.update_layout(
        xaxis_title="Sensor",
        yaxis_title=eixo_y,
        legend_title="Status",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


# ============================================================
# CSS / ESTILO VISUAL
# ============================================================

st.markdown(
    """
    <style>
        /* Sobe o conteúdo da página */
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 2rem !important;
        }

        header[data-testid="stHeader"] {
            height: 0rem;
            background: transparent;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        }

        section[data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stSlider label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stCheckbox label {
            color: #f8fafc !important;
            font-weight: 600;
        }

        .main {
            background-color: #f8fafc;
        }

        .titulo-principal {
            font-size: 2.15rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 0;
            line-height: 1.1;
        }

        .subtitulo {
            font-size: 1rem;
            color: #475569;
            margin-top: 0.15rem;
            margin-bottom: 0.9rem;
        }

        .card-status {
            padding: 1rem 1.1rem;
            border-radius: 1rem;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.8rem;
        }

        .card-sensor {
            padding: 1rem 1.1rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.9rem;
        }

        .card-sensor-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }

        .status-normal {
            color: #15803d;
            font-weight: 900;
            font-size: 1.35rem;
        }

        .status-alerta {
            color: #b91c1c;
            font-weight: 900;
            font-size: 1.35rem;
        }

        .status-neutro {
            color: #475569;
            font-weight: 900;
            font-size: 1.35rem;
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
            font-weight: 700;
            color: #475569;
        }

        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 900;
        }

        hr {
            margin-top: 0.8rem !important;
            margin-bottom: 0.8rem !important;
        }

        h2, h3 {
            margin-top: 0.5rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown(
    """
    <h1 class="titulo-principal">🌱 EcoSense IoT</h1>
    <p class="subtitulo">
        Monitoramento ambiental inteligente com ESP32, MQTT, FastAPI, Pandas e gráficos em tempo real
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

df = buscar_leituras(limite=1000)
df = preparar_dataframe(df)

estatisticas = buscar_estatisticas()
ultima_leitura_api = buscar_ultima_leitura()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🌱 EcoSense IoT")
st.sidebar.caption("Painel de controle do sistema")

pagina = st.sidebar.radio(
    "Menu",
    options=[
        "🏠 Visão Geral",
        "📡 Sensores Ativos",
        "🚨 Alertas",
        "📈 Histórico",
        "🛠️ Diagnóstico"
    ]
)

st.sidebar.markdown("---")

janela_atividade = st.sidebar.slider(
    "Sensor ativo se enviou nos últimos",
    min_value=1,
    max_value=30,
    value=2,
    step=1,
    help="Sensores sem leitura recente não aparecerão como ativos."
)

st.sidebar.caption(f"{janela_atividade} minuto(s)")

sensores_ativos = obter_sensores_ativos(df, janela_atividade)
df_ativos = filtrar_por_sensores_ativos(df, sensores_ativos)

st.sidebar.markdown("---")

if sensores_ativos:
    sensor_selecionado = st.sidebar.selectbox(
        "Sensor ativo",
        options=["Todos"] + sensores_ativos
    )
else:
    sensor_selecionado = "Todos"
    st.sidebar.warning("Nenhum sensor ativo encontrado.")

status_selecionado = st.sidebar.selectbox(
    "Status",
    options=["Todos", "NORMAL", "ALERTA"]
)

if not df_ativos.empty:
    max_registros_grafico = min(500, len(df_ativos))

    if max_registros_grafico < 20:
        quantidade_grafico = max_registros_grafico
        st.sidebar.info(f"{max_registros_grafico} registro(s) disponível(is)")
    else:
        quantidade_grafico = st.sidebar.slider(
            "Registros nos gráficos",
            min_value=20,
            max_value=max_registros_grafico,
            value=min(120, max_registros_grafico),
            step=20
        )
else:
    quantidade_grafico = 0

st.sidebar.markdown("---")

st.sidebar.subheader("📡 Sensores ativos")

if sensores_ativos:
    for sensor in sensores_ativos:
        st.sidebar.success(sensor)
else:
    st.sidebar.info("Aguardando leituras recentes.")

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
# VALIDAÇÃO INICIAL
# ============================================================

if df.empty:
    st.markdown(
        """
        <div class="alert-box">
            <strong>Nenhuma leitura encontrada.</strong><br>
            Verifique se a API, a ponte MQTT e o Wokwi estão rodando.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.code(
        """
Terminal 1 - API:
uvicorn api.main:app --reload --port 8050

Terminal 2 - Dashboard:
streamlit run dashboard/app.py

Terminal 3 - Ponte MQTT:
python api/mqtt_bridge.py

Wokwi:
Rodar simulação ESP32 + MQTT
        """,
        language="powershell"
    )

    st.stop()


if df_ativos.empty:
    st.markdown(
        f"""
        <div class="alert-box">
            <strong>Nenhum sensor ativo nos últimos {janela_atividade} minuto(s).</strong><br>
            O dashboard encontrou leituras antigas, mas nenhum sensor enviou dados recentemente.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Últimas leituras registradas")

    st.dataframe(
        df.sort_values("timestamp", ascending=False).head(20),
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# ============================================================
# FILTROS APLICADOS
# ============================================================

df_filtrado = df_ativos.copy()

if sensor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["sensor_id"] == sensor_selecionado]

if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == status_selecionado]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

df_grafico = df_filtrado.tail(quantidade_grafico)

status_geral = calcular_status_geral(df_ativos)
ultima_por_sensor = obter_ultima_leitura_por_sensor(df_ativos)
alertas_ativos = df_ativos[df_ativos["status"] == "ALERTA"].copy()
taxa_alerta_ativos = calcular_taxa_alerta(df_ativos)


# ============================================================
# PÁGINA: VISÃO GERAL
# ============================================================

if pagina == "🏠 Visão Geral":
    st.subheader("🏠 Visão geral do ambiente")

    st.markdown(
        f"""
        <div class="card-status">
            <div>Status geral dos sensores ativos</div>
            <div class="{classe_status(status_geral)}">{formatar_status(status_geral)}</div>
            <div class="small-muted">
                Considerando sensores com leitura nos últimos {janela_atividade} minuto(s).
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Sensores Ativos", len(sensores_ativos))
    col2.metric("Leituras Ativas", len(df_ativos))
    col3.metric("Alertas Ativos", len(alertas_ativos))
    col4.metric("Taxa de Alerta", f"{taxa_alerta_ativos:.1f}%")

    ultima_linha = df_ativos.iloc[-1]

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Temperatura Atual", f"{formatar_numero(ultima_linha.get('temperatura'))} °C")
    col6.metric("Umidade Atual", f"{formatar_numero(ultima_linha.get('umidade'))} %")
    col7.metric("CO₂ Atual", f"{formatar_numero(ultima_linha.get('co2'), 0)} ppm")
    col8.metric("Luminosidade Atual", f"{formatar_numero(ultima_linha.get('luminosidade'), 0)}")

    st.markdown("---")

    st.subheader("📡 Última leitura por sensor ativo")

    st.dataframe(
        ultima_por_sensor.sort_values("sensor_id"),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.subheader("📈 Tendência recente")

    aba_temp, aba_umidade, aba_co2, aba_luz = st.tabs(
        [
            "🌡️ Temperatura",
            "💧 Umidade",
            "🏭 CO₂",
            "💡 Luminosidade"
        ]
    )

    with aba_temp:
        fig = montar_grafico_linha(
            df_grafico,
            "temperatura",
            "Temperatura dos sensores ativos",
            "Temperatura (°C)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_umidade:
        fig = montar_grafico_linha(
            df_grafico,
            "umidade",
            "Umidade dos sensores ativos",
            "Umidade (%)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_co2:
        fig = montar_grafico_linha(
            df_grafico,
            "co2",
            "CO₂ dos sensores ativos",
            "CO₂ (ppm)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_luz:
        fig = montar_grafico_linha(
            df_grafico,
            "luminosidade",
            "Luminosidade dos sensores ativos",
            "Luminosidade"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PÁGINA: SENSORES ATIVOS
# ============================================================

elif pagina == "📡 Sensores Ativos":
    st.subheader("📡 Sensores ativos")

    st.markdown(
        f"""
        <div class="info-box">
            Esta tela exibe somente sensores que enviaram dados nos últimos
            <strong>{janela_atividade} minuto(s)</strong>.
            Sensores antigos ou de teste ficam ocultos desta visão.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Resumo dos sensores ativos")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    col_s1.metric("Sensores Ativos", len(sensores_ativos))
    col_s2.metric("Leituras Recentes", len(df_ativos))
    col_s3.metric(
        "Sensores em Alerta",
        df_ativos[df_ativos["status"] == "ALERTA"]["sensor_id"].nunique()
    )
    col_s4.metric("Taxa de Alerta", f"{taxa_alerta_ativos:.1f}%")

    st.markdown("---")

    st.markdown("### Situação atual por sensor")

    for sensor in sensores_ativos:
        dados_sensor = df_ativos[df_ativos["sensor_id"] == sensor].sort_values("timestamp")
        ultima = dados_sensor.iloc[-1]

        status = ultima.get("status", "SEM DADOS")

        st.markdown(
            f"""
            <div class="card-sensor">
                <div class="card-sensor-title">📍 {sensor}</div>
                <div class="{classe_status(status)}">{formatar_status(status)}</div>
                <div class="small-muted">
                    Última leitura: {ultima.get("timestamp")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Temperatura", f"{formatar_numero(ultima.get('temperatura'))} °C")
        c2.metric("Umidade", f"{formatar_numero(ultima.get('umidade'))} %")
        c3.metric("CO₂", f"{formatar_numero(ultima.get('co2'), 0)} ppm")
        c4.metric("Luminosidade", f"{formatar_numero(ultima.get('luminosidade'), 0)}")

        with st.expander(f"📋 Ver histórico recente de {sensor}"):
            st.dataframe(
                dados_sensor.sort_values("timestamp", ascending=False).head(20),
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")

    st.markdown("### 📈 Gráficos dos sensores ativos")

    aba_geral, aba_temp, aba_umidade, aba_co2, aba_luz = st.tabs(
        [
            "📊 Comparativo",
            "🌡️ Temperatura",
            "💧 Umidade",
            "🏭 CO₂",
            "💡 Luminosidade"
        ]
    )

    with aba_geral:
        st.markdown("#### Última leitura comparativa por sensor")

        ultima_por_sensor_grafico = obter_ultima_leitura_por_sensor(df_ativos)

        col_g1, col_g2 = st.columns(2)

        fig_temp_bar = montar_grafico_barra_ultima_leitura(
            ultima_por_sensor_grafico,
            "temperatura",
            "Temperatura atual por sensor",
            "Temperatura (°C)"
        )
        col_g1.plotly_chart(fig_temp_bar, use_container_width=True)

        fig_co2_bar = montar_grafico_barra_ultima_leitura(
            ultima_por_sensor_grafico,
            "co2",
            "CO₂ atual por sensor",
            "CO₂ (ppm)"
        )
        col_g2.plotly_chart(fig_co2_bar, use_container_width=True)

        col_g3, col_g4 = st.columns(2)

        fig_umidade_bar = montar_grafico_barra_ultima_leitura(
            ultima_por_sensor_grafico,
            "umidade",
            "Umidade atual por sensor",
            "Umidade (%)"
        )
        col_g3.plotly_chart(fig_umidade_bar, use_container_width=True)

        fig_luz_bar = montar_grafico_barra_ultima_leitura(
            ultima_por_sensor_grafico,
            "luminosidade",
            "Luminosidade atual por sensor",
            "Luminosidade"
        )
        col_g4.plotly_chart(fig_luz_bar, use_container_width=True)

    with aba_temp:
        fig = montar_grafico_linha(
            df_grafico,
            "temperatura",
            "Temperatura dos sensores ativos ao longo do tempo",
            "Temperatura (°C)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_umidade:
        fig = montar_grafico_linha(
            df_grafico,
            "umidade",
            "Umidade dos sensores ativos ao longo do tempo",
            "Umidade (%)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_co2:
        fig = montar_grafico_linha(
            df_grafico,
            "co2",
            "CO₂ dos sensores ativos ao longo do tempo",
            "CO₂ (ppm)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba_luz:
        fig = montar_grafico_linha(
            df_grafico,
            "luminosidade",
            "Luminosidade dos sensores ativos ao longo do tempo",
            "Luminosidade"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PÁGINA: ALERTAS
# ============================================================

elif pagina == "🚨 Alertas":
    st.subheader("🚨 Central de alertas")

    if alertas_ativos.empty:
        st.markdown(
            """
            <div class="success-box">
                Nenhum alerta ativo no momento.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="alert-box">
                Existem <strong>{len(alertas_ativos)}</strong> leituras em alerta
                entre os sensores ativos.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(
            alertas_ativos.sort_values("timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        alertas_por_sensor = (
            alertas_ativos
            .groupby("sensor_id")
            .size()
            .reset_index(name="total_alertas")
            .sort_values("total_alertas", ascending=False)
        )

        fig = px.bar(
            alertas_por_sensor,
            x="sensor_id",
            y="total_alertas",
            title="Alertas por sensor ativo",
            text="total_alertas"
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title="Total de alertas",
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PÁGINA: HISTÓRICO
# ============================================================

elif pagina == "📈 Histórico":
    st.subheader("📈 Histórico de leituras")

    col_h1, col_h2 = st.columns(2)

    tipo_grafico = col_h1.selectbox(
        "Variável",
        options=[
            "temperatura",
            "umidade",
            "co2",
            "luminosidade"
        ]
    )

    agrupamento = col_h2.selectbox(
        "Visualização",
        options=[
            "Linha do tempo",
            "Média por sensor",
            "Distribuição"
        ]
    )

    if agrupamento == "Linha do tempo":
        fig = montar_grafico_linha(
            df_grafico,
            tipo_grafico,
            f"{tipo_grafico.upper()} ao longo do tempo",
            tipo_grafico
        )

        st.plotly_chart(fig, use_container_width=True)

    elif agrupamento == "Média por sensor":
        df_media = (
            df_filtrado
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
            text_auto=True
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title=tipo_grafico,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    elif agrupamento == "Distribuição":
        fig = px.box(
            df_filtrado,
            x="sensor_id",
            y=tipo_grafico,
            title=f"Distribuição de {tipo_grafico} por sensor"
        )

        fig.update_layout(
            xaxis_title="Sensor",
            yaxis_title=tipo_grafico,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Leituras filtradas")

    st.dataframe(
        df_filtrado.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PÁGINA: DIAGNÓSTICO
# ============================================================

elif pagina == "🛠️ Diagnóstico":
    st.subheader("🛠️ Diagnóstico do sistema")

    st.markdown(
        """
        <div class="info-box">
            Esta tela ajuda a verificar se API, ponte MQTT, banco de dados e dashboard
            estão funcionando corretamente.
        </div>
        """,
        unsafe_allow_html=True
    )

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    col_d1.metric("Total no Banco", len(df))
    col_d2.metric("Sensores Ativos", len(sensores_ativos))
    col_d3.metric("Leituras Ativas", len(df_ativos))
    col_d4.metric("Status Geral", formatar_status(status_geral))

    st.markdown("---")

    st.subheader("Última leitura recebida pela API")

    if ultima_leitura_api:
        st.json(ultima_leitura_api)
    else:
        st.warning("Nenhuma última leitura retornada pela API.")

    st.markdown("---")

    st.subheader("Sensores encontrados no banco")

    sensores_banco = sorted(df["sensor_id"].dropna().unique().tolist())

    df_sensores = pd.DataFrame({
        "sensor_id": sensores_banco,
        "ativo": [
            "SIM" if sensor in sensores_ativos else "NÃO"
            for sensor in sensores_banco
        ]
    })

    st.dataframe(
        df_sensores,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    st.subheader("Comandos para rodar o projeto")

    st.code(
        """
Terminal 1 - API:
uvicorn api.main:app --reload --port 8050

Terminal 2 - Dashboard:
streamlit run dashboard/app.py

Terminal 3 - Ponte MQTT:
python api/mqtt_bridge.py

Terminal 4 - Simulador Python opcional:
python api/simulador_envio.py
        """,
        language="powershell"
    )
    