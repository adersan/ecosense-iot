# 🌱 EcoSense IoT

## Monitoramento Ambiental Inteligente com ESP32, MQTT, FastAPI, SQLite, Pandas e Dashboard em Tempo Real

O **EcoSense IoT** é um projeto acadêmico de Internet das Coisas desenvolvido para simular uma rede de sensores ambientais conectados a um microcontrolador ESP32. O sistema coleta dados simulados de temperatura, umidade, CO₂ e luminosidade, envia essas informações via protocolo MQTT, processa os dados em uma API Python, armazena as leituras em banco SQLite e exibe os resultados em um dashboard interativo em tempo real.

O projeto foi desenvolvido como parte da disciplina **Aplicação de Cloud, IoT e Indústria 4.0 em Python**, com foco na integração entre dispositivos IoT, comunicação em rede, backend, armazenamento, análise de dados e visualização.

---

## 📌 Objetivo do Projeto

Desenvolver uma solução IoT capaz de simular o monitoramento ambiental de diferentes ambientes, utilizando microcontrolador ESP32, sensores simulados, comunicação MQTT, API em Python e dashboard em tempo real.

O sistema permite acompanhar variáveis ambientais críticas e identificar automaticamente situações de alerta, como:

- temperatura elevada;
- umidade excessiva;
- concentração elevada de CO₂;
- baixa luminosidade.

---

## 🧠 Problema Resolvido

Ambientes como salas de aula, laboratórios, salas técnicas e almoxarifados podem sofrer alterações ambientais que comprometem conforto, segurança, conservação de equipamentos e qualidade do ambiente.

Sem monitoramento contínuo, situações como aumento de temperatura, excesso de umidade, baixa iluminação ou concentração elevada de CO₂ podem passar despercebidas.

O EcoSense IoT propõe uma solução simulada e funcional para monitorar esses ambientes em tempo real, permitindo rápida identificação de anomalias por meio de alertas visuais, sonoros e gráficos no dashboard.

---

## 🏗️ Arquitetura da Solução

A arquitetura final do projeto utiliza comunicação MQTT, mais adequada ao contexto de IoT.

```text
Wokwi / ESP32
     ↓
Sensores simulados
     ↓
Publicação MQTT
     ↓
Broker MQTT HiveMQ
     ↓
Ponte MQTT em Python
     ↓
API FastAPI
     ↓
Banco SQLite
     ↓
Dashboard Streamlit + Pandas + Plotly
```

### Fluxo de funcionamento

1. O ESP32 no Wokwi simula uma rede com múltiplos sensores ambientais.
2. Cada sensor gera leituras de temperatura, umidade, CO₂ e luminosidade.
3. O ESP32 publica as leituras no tópico MQTT.
4. A ponte Python `mqtt_bridge.py` escuta o tópico MQTT.
5. Ao receber uma mensagem, a ponte envia os dados para a API FastAPI.
6. A API valida, classifica e salva as leituras no banco SQLite.
7. O dashboard consulta a API, trata os dados com Pandas e exibe gráficos em tempo real.

---

## 📡 Sensores Simulados

O projeto simula quatro sensores ambientais, representando diferentes ambientes:

```text
SALA_AULA_01
LABORATORIO_01
SALA_TECNICA_01
ALMOXARIFADO_01
```

Cada sensor possui comportamento próprio:

| Sensor | Ambiente | Comportamento Simulado |
|---|---|---|
| `SALA_AULA_01` | Sala de Aula | Ambiente normalmente estável, com possível aumento de CO₂ |
| `LABORATORIO_01` | Laboratório | Pode apresentar aumento de temperatura |
| `SALA_TECNICA_01` | Sala Técnica | Simula aquecimento por presença de equipamentos |
| `ALMOXARIFADO_01` | Almoxarifado | Pode apresentar umidade alta e baixa luminosidade |

---

## 🚨 Regras de Alerta

A API classifica uma leitura como `ALERTA` quando pelo menos uma das condições abaixo é verdadeira:

| Variável | Condição de Alerta |
|---|---|
| Temperatura | Maior que 30 °C |
| Umidade | Maior que 80% |
| CO₂ | Maior que 1000 ppm |
| Luminosidade | Menor que 200 |

Caso nenhuma condição seja atendida, a leitura é classificada como `NORMAL`.

---

## 💡 Sinalização no Wokwi

O circuito simulado possui LEDs e buzzer para representação visual do estado dos ambientes.

| Componente | Função |
|---|---|
| LED verde geral | Indica que todos os ambientes estão normais |
| LED vermelho geral | Indica que existe pelo menos um ambiente em alerta |
| LED azul | Alerta na Sala de Aula |
| LED amarelo | Alerta no Laboratório |
| LED laranja | Alerta na Sala Técnica |
| LED roxo | Alerta no Almoxarifado |
| Buzzer | Emite um bipe curto quando o sistema entra em alerta |

---

## 🧰 Tecnologias Utilizadas

### Hardware / Simulação

- ESP32
- Sensor DHT22
- Potenciômetros simulando CO₂ e luminosidade
- LEDs
- Buzzer
- Resistores
- Wokwi

### Comunicação

- Wi-Fi simulado no Wokwi
- MQTT
- Broker público HiveMQ

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- SQLite
- Requests
- Paho MQTT

### Dashboard

- Streamlit
- Pandas
- Plotly
- Streamlit Autorefresh

### Ferramentas

- VS Code
- Git
- GitHub
- PowerShell

---

## 📁 Estrutura do Projeto

```text
ecosense-iot/
│
├── README.md
├── requirements.txt
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── schemas.py
│   ├── mqtt_bridge.py
│   └── simulador_envio.py
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py
│   └── services.py
│
├── microcontrolador/
│   ├── sketch.ino
│   └── diagram.json
│
├── data/
│   └── ecosense.db
│
├── circuito/
│   ├── vista_circuito.png
│   ├── esquema_eletrico.png
│   └── link_wokwi.txt
│
├── documentacao/
│   ├── projeto_abnt.docx
│   └── projeto_abnt.pdf
│
└── slides/
    └── apresentacao_ecosense_iot.pptx
```

---

## ⚙️ Instalação do Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/ecosense-iot.git
cd ecosense-iot
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
```

### 3. Ativar ambiente virtual no Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a ativação, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Depois tente novamente:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 📦 Dependências

O arquivo `requirements.txt` deve conter:

```txt
fastapi
uvicorn
pydantic
pandas
streamlit
plotly
requests
streamlit-autorefresh
python-multipart
paho-mqtt
```

---

## ▶️ Como Rodar o Projeto

Para executar o sistema completo, utilize três terminais no VS Code.

### Terminal 1 — Rodar a API FastAPI

```bash
uvicorn api.main:app --reload --port 8050
```

A API ficará disponível em:

```text
http://127.0.0.1:8050
```

A documentação automática da API ficará disponível em:

```text
http://127.0.0.1:8050/docs
```

### Terminal 2 — Rodar o Dashboard

```bash
streamlit run dashboard/app.py
```

O Streamlit abrirá no navegador em um endereço parecido com:

```text
http://localhost:8501
```

### Terminal 3 — Rodar a Ponte MQTT

```bash
python api/mqtt_bridge.py
```

A ponte MQTT ficará escutando o tópico:

```text
ecosense/santiago/leituras
```

Toda mensagem recebida será enviada automaticamente para a API local.

### Wokwi — Rodar o ESP32

1. Acesse o projeto no Wokwi.
2. Abra o arquivo `sketch.ino`.
3. Confirme o código do ESP32.
4. Abra o arquivo `diagram.json`.
5. Confirme o circuito.
6. Clique em **Play**.

O ESP32 começará a publicar mensagens MQTT simulando os sensores ambientais.

---

## 🔄 Ordem Correta de Execução

Execute nesta ordem:

```text
1. API FastAPI
2. Dashboard Streamlit
3. Ponte MQTT
4. Simulação Wokwi
```

---

## 📊 Funcionalidades do Dashboard

O dashboard possui menu lateral com as seguintes páginas:

### 🏠 Visão Geral

Exibe:

- status geral dos sensores ativos;
- quantidade de sensores ativos;
- quantidade de leituras recentes;
- quantidade de alertas;
- taxa de alerta;
- última leitura de cada sensor;
- gráficos recentes.

### 📡 Sensores Ativos

Exibe apenas sensores que enviaram leituras recentemente.

Mostra:

- cards por sensor;
- status individual;
- temperatura;
- umidade;
- CO₂;
- luminosidade;
- histórico recente;
- gráficos comparativos;
- gráficos por variável.

### 🚨 Alertas

Exibe:

- leituras em estado de alerta;
- tabela de alertas ativos;
- gráfico de alertas por sensor.

### 📈 Histórico

Permite visualizar:

- linha do tempo;
- média por sensor;
- distribuição dos dados;
- tabela com leituras filtradas.

### 🛠️ Diagnóstico

Exibe:

- total de registros no banco;
- sensores ativos;
- última leitura recebida;
- sensores encontrados no banco;
- comandos para execução do projeto.

---

## 🧪 Simulador Python Opcional

Além do Wokwi, o projeto possui um simulador Python de envio de dados para testes locais.

Para rodar:

```bash
python api/simulador_envio.py
```

Esse simulador envia dados diretamente para a API, sendo útil como plano B durante a apresentação.

---

## 🌐 Protocolo MQTT

O projeto utiliza MQTT para representar uma comunicação típica de sistemas IoT.

### Broker MQTT

```text
broker.hivemq.com
```

### Porta

```text
1883
```

### Tópico

```text
ecosense/santiago/leituras
```

### Exemplo de mensagem MQTT

```json
{
  "sensor_id": "SALA_AULA_01",
  "temperatura": 26.5,
  "umidade": 62,
  "co2": 760,
  "luminosidade": 700
}
```

---

## 🔌 API FastAPI

### Rota inicial

```http
GET /
```

Retorna informações básicas da API.

### Receber leitura

```http
POST /leituras
```

Exemplo de corpo JSON:

```json
{
  "sensor_id": "SALA_AULA_01",
  "temperatura": 26.5,
  "umidade": 62,
  "co2": 760,
  "luminosidade": 700
}
```

### Listar leituras

```http
GET /leituras
```

### Obter última leitura

```http
GET /leituras/ultima
```

### Obter estatísticas

```http
GET /estatisticas
```

### Apagar leituras

```http
DELETE /leituras
```

---

## 🗄️ Banco de Dados

O projeto utiliza SQLite para armazenar as leituras ambientais.

A tabela principal é:

```text
leituras
```

Campos:

| Campo | Descrição |
|---|---|
| id | Identificador da leitura |
| sensor_id | Identificação do sensor |
| timestamp | Data e hora da leitura |
| temperatura | Temperatura em °C |
| umidade | Umidade em % |
| co2 | CO₂ em ppm |
| luminosidade | Luminosidade simulada |
| status | NORMAL ou ALERTA |

---

## 🖥️ Demonstração Esperada

Durante a apresentação, o fluxo demonstrado será:

1. Abrir a simulação no Wokwi.
2. Mostrar o ESP32 conectado ao Wi-Fi.
3. Mostrar o ESP32 publicando mensagens MQTT.
4. Mostrar a ponte MQTT recebendo os dados.
5. Mostrar a API recebendo requisições `POST`.
6. Mostrar o dashboard atualizando em tempo real.
7. Apresentar sensores ativos.
8. Demonstrar alertas por temperatura, umidade, CO₂ ou baixa luminosidade.

---

## 📸 Imagens do Projeto

As imagens do circuito e dashboard devem ser armazenadas na pasta:

```text
circuito/
```

Sugestão de arquivos:

```text
vista_circuito.png
esquema_eletrico.png
dashboard_visao_geral.png
dashboard_sensores_ativos.png
dashboard_alertas.png
```

---

## 📚 Relação com IoT, Cloud e Indústria 4.0

O EcoSense IoT demonstra conceitos importantes de Internet das Coisas e Indústria 4.0:

- coleta de dados por dispositivos conectados;
- transmissão de dados por protocolo MQTT;
- uso de broker de mensagens;
- processamento em backend Python;
- armazenamento em banco de dados;
- análise de dados com Pandas;
- visualização em dashboard;
- tomada de decisão baseada em dados;
- detecção de anomalias ambientais.

---

## 🧾 Possíveis Melhorias Futuras

O projeto pode ser expandido com:

- sensores físicos reais;
- autenticação de dispositivos;
- broker MQTT privado;
- banco PostgreSQL;
- deploy da API em nuvem;
- dashboard publicado online;
- notificações por e-mail ou WhatsApp;
- alertas por Telegram;
- machine learning para previsão de anomalias;
- histórico por data;
- exportação de relatórios em PDF.

---

## 👥 Equipe

```text
[NOME DO ALUNO 1]
[NOME DO ALUNO 2]
[NOME DO ALUNO 3]
[NOME DO ALUNO 4]
```

---

## 🎓 Informações Acadêmicas

```text
Instituição: [NOME DA INSTITUIÇÃO]
Curso: [NOME DO CURSO]
Disciplina: Aplicação de Cloud, IoT e Indústria 4.0 em Python
Professor: Prof. MSc Heleno Cardoso
Ano: 2026
Cidade: Salvador - BA
```

---

## 👨‍💻 Desenvolvido por

Projeto desenvolvido por:

```text
Equipe EcoSense IoT
```

Orientação:

```text
Prof. MSc Heleno Cardoso
```

---

## 📄 Licença

Este projeto é de uso acadêmico e educacional.

