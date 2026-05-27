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


st.set_page_config(
    page_title="EcoSense IoT",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Atualiza automaticamente a página a cada 3 segundos.
st_autorefresh(interval=3000, key="dashboard_ecosense")


def formatar_numero(valor, casas=2):
    """
    Formata números para exibição segura no dashboard.
    """
    try:
        return f"{float(valor):.{casas}f}"
    except (TypeError, ValueError):
        return "0.00"


def formatar_status(status: str) -> str:
    """
    Retorna uma versão visual do status.
    """
    if status == "ALERTA":
        return "🚨 ALERTA"

    if status == "NORMAL":
        return "✅ NORMAL"

    return "⚪ SEM DADOS"


def classificar_cor_status(status: str) -> str:
    """
    Retorna uma classe visual simples para status.
    """
    if status == "ALERTA":
        return "alerta"

    if status == "NORMAL":
        return "normal"

    return "neutro"


st.markdown(
    """
    <style>
        .main {
            background-color: #f8fafc;
        }

        .titulo-principal {
            font-size: 2.4rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0;
        }

        .subtitulo {
            font-size: 1.05rem;
            color: #475569;
            margin-top: 0.2rem;
            margin-bottom: 1.5rem;
        }

        .card-status {
            padding: 1.2rem;
            border-radius: 1rem;
            background: white;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }

        .status-normal {
            color: #15803d;
            font-weight: 800;
            font-size: 1.4rem;
        }

        .status-alerta {
            color: #b91c1c;
            font-weight: 800;
            font-size: 1.4rem;
        }

        .status-neutro {
            color: #475569;
            font-weight: 800;
            font-size: 1.4rem;
        }

        .info-box {
            padding: 0.9rem 1rem;
            border-radius: 0.8rem;
            background-color: #eff6ff;
            border-left: 5px solid #2563eb;
            color: #1e3a8a;
            margin-bottom: 1rem;
        }

        .alert-box {
            padding: 0.9rem 1rem;
            border-radius: 0.8rem;
            background-color: #fef2f2;
            border-left: 5px solid #dc2626;
            color: #7f1d1d;
            margin-bottom: 1rem;
        }

        .success-box {
            padding: 0.9rem 1rem;
            border-radius: 0.8rem;
            background-color: #f0fdf4;
            border-left: 5px solid #16a34a;
            color: #14532d;
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <h1 class="titulo-principal">🌱 EcoSense IoT</h1>
    <p class="subtitulo">
        Monitoramento Ambiental com ESP32, API Python, Pandas e Dashboard em Tempo Real
    </p>
    """,
    unsafe_allow_html=True
)


# Sidebar
st.sidebar.title("⚙️ Configurações")

limite_registros = st.sidebar.slider(
    "Quantidade de leituras carregadas",
    min_value=50,
    max_value=1000,
    value=500,
    step=50
)

st.sidebar.markdown("---")

st.sidebar.info(
    "A API esperada está em:\n\n"
    "http://127.0.0.1:8050"
)

confirmar_limpeza = st.sidebar.checkbox(
    "Habilitar limpeza dos dados"
)

if confirmar_limpeza:
    if st.sidebar.button("🗑️ Apagar todas as leituras"):
        sucesso = limpar_leituras()

        if sucesso:
            st.sidebar.success("Leituras apagadas com sucesso.")
            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.error("Não foi possível apagar as leituras.")


# Buscar dados
df = buscar_leituras(limite=limite_registros)
estatisticas = buscar_estatisticas()
ultima_leitura = buscar_ultima_leitura()


if df.empty:
    st.markdown(
        """
        <div class="alert-box">
            <strong>Nenhuma leitura encontrada.</strong><br>
            Verifique se a API está rodando na porta 8050 e se já existem dados enviados para o endpoint /leituras.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Como testar rapidamente")

    st.code(
        """
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8050/leituras" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{
    "sensor_id": "ESP32_01",
    "temperatura": 31.8,
    "umidade": 72,
    "co2": 950,
    "luminosidade": 620
  }'
        """,
        language="powershell"
    )

    st.stop()


# Ordenação segura por data
if "timestamp" in df.columns:
    df = df.sort_values("timestamp")


# Última leitura
if ultima_leitura:
    status_atual = ultima_leitura.get("status", "SEM DADOS")
    classe_status = classificar_cor_status(status_atual)

    if classe_status == "alerta":
        classe_css = "status-alerta"
    elif classe_status == "normal":
        classe_css = "status-normal"
    else:
        classe_css = "status-neutro"

    st.markdown(
        f"""
        <div class="card-status">
            <div>Último status do ambiente</div>
            <div class="{classe_css}">{formatar_status(status_atual)}</div>
            <div style="color:#64748b; margin-top:0.4rem;">
                Sensor: {ultima_leitura.get("sensor_id", "N/A")} |
                Data/Hora: {ultima_leitura.get("timestamp", "N/A")}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# Indicadores principais
st.subheader("📌 Indicadores atuais")

ultima_linha = df.iloc[-1]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    label="Temperatura",
    value=f"{formatar_numero(ultima_linha.get('temperatura'))} °C"
)

col2.metric(
    label="Umidade",
    value=f"{formatar_numero(ultima_linha.get('umidade'))} %"
)

col3.metric(
    label="CO₂",
    value=f"{formatar_numero(ultima_linha.get('co2'), 0)} ppm"
)

col4.metric(
    label="Luminosidade",
    value=f"{formatar_numero(ultima_linha.get('luminosidade'), 0)}"
)

col5.metric(
    label="Status",
    value=formatar_status(ultima_linha.get("status", "SEM DADOS"))
)


st.markdown("---")


# Indicadores gerais
st.subheader("📊 Estatísticas gerais")

col6, col7, col8, col9 = st.columns(4)

col6.metric(
    label="Total de Leituras",
    value=estatisticas.get("total_leituras", 0)
)

col7.metric(
    label="Alertas Detectados",
    value=estatisticas.get("total_alertas", 0)
)

col8.metric(
    label="Sensores Ativos",
    value=estatisticas.get("sensores_ativos", 0)
)

taxa_alerta = 0

if estatisticas.get("total_leituras", 0) > 0:
    taxa_alerta = (
        estatisticas.get("total_alertas", 0)
        / estatisticas.get("total_leituras", 1)
    ) * 100

col9.metric(
    label="Taxa de Alerta",
    value=f"{taxa_alerta:.1f}%"
)


col10, col11, col12, col13 = st.columns(4)

col10.metric(
    label="Média Temperatura",
    value=f"{formatar_numero(estatisticas.get('media_temperatura'))} °C"
)

col11.metric(
    label="Média Umidade",
    value=f"{formatar_numero(estatisticas.get('media_umidade'))} %"
)

col12.metric(
    label="Média CO₂",
    value=f"{formatar_numero(estatisticas.get('media_co2'), 0)} ppm"
)

col13.metric(
    label="Média Luminosidade",
    value=f"{formatar_numero(estatisticas.get('media_luminosidade'), 0)}"
)


st.markdown("---")


# Filtros
st.subheader("🔎 Filtros de visualização")

col_f1, col_f2, col_f3 = st.columns(3)

sensores_disponiveis = sorted(df["sensor_id"].dropna().unique().tolist())

sensor_selecionado = col_f1.selectbox(
    "Sensor",
    options=["Todos"] + sensores_disponiveis
)

status_selecionado = col_f2.selectbox(
    "Status",
    options=["Todos", "NORMAL", "ALERTA"]
)

total_registros = len(df)

if total_registros <= 1:
    quantidade_grafico = total_registros

elif total_registros < 20:
    quantidade_grafico = col_f3.slider(
        "Registros nos gráficos",
        min_value=1,
        max_value=total_registros,
        value=total_registros,
        step=1
    )

else:
    quantidade_grafico = col_f3.slider(
        "Registros nos gráficos",
        min_value=20,
        max_value=min(500, total_registros),
        value=min(100, total_registros),
        step=10
    )


df_filtrado = df.copy()

if sensor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["sensor_id"] == sensor_selecionado]

if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == status_selecionado]

df_grafico = df_filtrado.tail(quantidade_grafico)


if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


st.markdown("---")


# Gráficos
st.subheader("📈 Gráficos em tempo real")

aba_temp, aba_umidade, aba_co2, aba_luz = st.tabs(
    [
        "🌡️ Temperatura",
        "💧 Umidade",
        "🏭 CO₂",
        "💡 Luminosidade"
    ]
)


with aba_temp:
    fig_temp = px.line(
        df_grafico,
        x="timestamp",
        y="temperatura",
        color="sensor_id",
        markers=True,
        title="Temperatura ao longo do tempo"
    )

    fig_temp.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title="Temperatura (°C)",
        legend_title="Sensor"
    )

    st.plotly_chart(fig_temp, use_container_width=True)


with aba_umidade:
    fig_umidade = px.line(
        df_grafico,
        x="timestamp",
        y="umidade",
        color="sensor_id",
        markers=True,
        title="Umidade ao longo do tempo"
    )

    fig_umidade.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title="Umidade (%)",
        legend_title="Sensor"
    )

    st.plotly_chart(fig_umidade, use_container_width=True)


with aba_co2:
    fig_co2 = px.line(
        df_grafico,
        x="timestamp",
        y="co2",
        color="sensor_id",
        markers=True,
        title="CO₂ ao longo do tempo"
    )

    fig_co2.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title="CO₂ (ppm)",
        legend_title="Sensor"
    )

    st.plotly_chart(fig_co2, use_container_width=True)


with aba_luz:
    fig_luz = px.line(
        df_grafico,
        x="timestamp",
        y="luminosidade",
        color="sensor_id",
        markers=True,
        title="Luminosidade ao longo do tempo"
    )

    fig_luz.update_layout(
        xaxis_title="Data/Hora",
        yaxis_title="Luminosidade",
        legend_title="Sensor"
    )

    st.plotly_chart(fig_luz, use_container_width=True)


st.markdown("---")


# Alertas
st.subheader("🚨 Leituras em alerta")

df_alertas = df[df["status"] == "ALERTA"].copy()

if df_alertas.empty:
    st.markdown(
        """
        <div class="success-box">
            Nenhuma leitura em alerta foi encontrada no momento.
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.dataframe(
        df_alertas.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )


st.markdown("---")


# Últimas leituras
st.subheader("📋 Últimas leituras registradas")

st.dataframe(
    df.sort_values("timestamp", ascending=False),
    use_container_width=True,
    hide_index=True
)


st.markdown("---")


# Diagnóstico final
st.markdown(
    """
    <div class="info-box">
        <strong>EcoSense IoT em execução.</strong><br>
        O dashboard consulta a API automaticamente e atualiza os dados a cada 3 segundos.
    </div>
    """,
    unsafe_allow_html=True
)