# 📈 Pipeline de Análise B3

Pipeline de dados completo para análise de ações da B3 (Bolsa de Valores Brasileira), integrando coleta automatizada de cotações via Yahoo Finance, armazenamento em banco NoSQL, orquestração de pipelines de ETL e visualização interativa com dashboard e alertas em tempo real. Este projeto demonstra uma arquitetura end-to-end envolvendo **Flask**, **yfinance**, **Apache Cassandra**, **Apache Airflow** e **Grafana**.

---

## 🧩 Descrição do Projeto

O Pipeline de Análise B3 realiza a coleta periódica de dados de cotações de ativos listados na B3 e os disponibiliza em um painel analítico. Os principais componentes são:

- **API Flask + yfinance** – Serviço Flask que utiliza a biblioteca `yfinance` para obter cotações do Yahoo Finance. Fornece endpoints REST que permitem recuperar dados históricos de ativos em formato JSON.
- **Banco de dados Apache Cassandra** – Banco NoSQL distribuído usado para armazenar as cotações coletadas. Foi escolhido pela eficiência em gravações frequentes e consultas por chave primária.
- **Orquestração Apache Airflow** – Scheduler responsável por gerenciar duas DAGs de ETL: uma para coleta periódica de dados e outra para limpeza diária de dados antigos no banco.
- **Dashboard Grafana (Plugin JSON API)** – Interface de visualização dos dados de mercado, construída no Grafana utilizando o plugin JSON API para consumir os dados diretamente da API Flask.

---

## ✅ Requisitos

- **Docker** (Docker Engine 20.x ou superior)
- **Docker Compose** (v2 ou integrado)
- **Windows** (para uso com `.bat`)

⚠️ Portas utilizadas:
- Cassandra: `9042`
- API Flask: `5000`
- Airflow: `8082`
- Grafana: `3000`

---

## 🚀 Como Executar

Clone o repositório:

```bash
git clone https://github.com/usuario/pipeline-financeiro-b3.git
cd pipeline-financeiro-b3
```

Execute o script de inicialização:

```bash
start_projeto_financas.bat
```

O script irá:
- Subir todos os containers Docker
- Aguardar a inicialização dos serviços
- Instalar dependências no Airflow
- Reiniciar o Airflow para carregar as DAGs
- Abrir as interfaces no navegador

### Interfaces:
- [Airflow](http://localhost:8082)
- [API de Cotações (Flask)](http://localhost:5000/cotacoes)
- [Grafana](http://localhost:3000)

Para encerrar:

```bash
end_projeto.bat
```

---

## 🧠 Funcionamento do Pipeline

1. **Carga Inicial**: A API Flask cria a estrutura no Cassandra e carrega 60 dias de histórico por ativo usando `yfinance`.
2. **Coleta com Airflow**: DAG `coleta_ativos_direto_cassandra` roda a cada 15 minutos, inserindo novas cotações no banco.
3. **Limpeza Diária**: DAG `limpeza_diaria_dag` remove registros antigos mantendo uma janela deslizante no Cassandra.
4. **Consulta via API Flask**:
    - `/ativos`: lista de tickers
    - `/cotacoes`: todas as cotações
    - `/cotacoes/<ticker>?campo=close`: série temporal formatada para o Grafana

5. **Visualização com Grafana**:
    - Fonte de dados JSON API apontando para a API Flask
    - Dashboard provisionado com gráficos:
        - Abertura, Máxima, Mínima, Fechamento, Volume
    - Alertas:
        - Queda > 5%
        - Volume > 10 milhões

---

## 🧪 Trechos de Código Relevantes

### 🔹 Endpoint Flask
```python
@app.route("/cotacoes/<ticker>")
def listar_por_ativo(ticker):
    campo = request.args.get("campo", "close")
    ...
    return jsonify([{"datapoints": dados}])
```

### 🔹 DAG Airflow
```python
with DAG(
    dag_id='coleta_ativos_direto_cassandra',
    schedule_interval='*/15 * * * *',
) as dag:
    tarefa_coleta = PythonOperator(
        task_id='coletar_ativos',
        python_callable=coletar_ativos
    )
```

### 🔹 Script .BAT
```bat
docker-compose up -d --build
timeout /t 90 >nul
docker exec -it airflow-web pip install --user yfinance pandas cassandra-driver
docker restart airflow-web
docker restart airflow-scheduler
start http://localhost:8082
start http://localhost:5000/cotacoes
start http://localhost:3000
docker logs api-ibov --follow
```

---

## 📦 Provisionamento Grafana

- `provisioning/datasources/datasource.yaml`: define a fonte JSON API (uid: `json-api`)
- `provisioning/dashboards/dashboard.yaml`: carrega o dashboard `dashboard.json`
- Os painéis e alertas são automaticamente carregados ao subir o container Grafana

---

## 🔔 Alertas no Dashboard

- **Alerta de Queda**: dispara se o preço de fechamento cair >5% na última hora
- **Alerta de Volume Alto**: dispara se o volume ultrapassar 10 milhões

---

## 📁 Estrutura do Projeto

```plaintext
project-root/
├── airflow/
│   └── dags/
├── app/
│   ├── api_ibov.py
│   ├── requirements.txt
│   └── Dockerfile
├── provisioning/
│   ├── datasources/
│   └── dashboards/
├── docker-compose.yml
├── start_projeto_financas.bat
└── end_projeto.bat
```

---

## 🎥 Demonstração

- 📽️ **Vídeo do Projeto**: 
- 🖼️ **Screenshot do Dashboard**: ![Dashboard Grafana](https://i.imgur.com/xdc5A7U.png)

---

## 🧼 Observações Finais

- Evite reexecutar DAGs manualmente fora do horário de pregão
- Alertas são configurados apenas para fins de demonstração
- O `.bat` simplifica o setup para ambiente local e acadêmico
- Para produção, recomenda-se gestão de credenciais, segurança e volumes externos

---

**Desenvolvido por Guilherme de Oliveira | Mestrando em Computação Aplicada**
