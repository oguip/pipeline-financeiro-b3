from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import yfinance as yf
from cassandra.cluster import Cluster
import time
import pandas as pd

def conectar_cassandra():
    tentativas = 0
    while tentativas < 10:
        try:
            cluster = Cluster(['cassandra'])
            session = cluster.connect()
            session.execute("""
                CREATE KEYSPACE IF NOT EXISTS cotacoes
                WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
            """)
            session.set_keyspace('cotacoes')
            session.execute("""
                CREATE TABLE IF NOT EXISTS ibov (
                    ticker TEXT,
                    datetime TIMESTAMP,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume BIGINT,
                    PRIMARY KEY (ticker, datetime)
                )
            """)
            print("✅ Conectado e tabela verificada.")
            return session
        except Exception as e:
            print(f"Tentativa {tentativas + 1}: Cassandra não está pronto ainda. Erro: {e}")
            tentativas += 1
            time.sleep(5)
    raise Exception("❌ Erro ao conectar ao Cassandra após várias tentativas.")

def coletar_ativos():
    session = conectar_cassandra()
    ativos = ['^BVSP', 'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA',
              'BBAS3.SA', 'SANB11.SA', 'WEGE3.SA', 'ABEV3.SA', 'RENT3.SA']
    for ticker in ativos:
        print(f"🔁 Coletando dados para {ticker}")
        df = yf.download(ticker, period="1d", interval="15m", auto_adjust=True)
        if df.empty:
            print(f"⚠️ Sem dados para {ticker}")
            continue
        df = df.reset_index()
        for row in df.itertuples():
            session.execute("""
                INSERT INTO ibov (ticker, datetime, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                ticker,
                row.Datetime.to_pydatetime(),
                float(row.Open),
                float(row.High),
                float(row.Low),
                float(row.Close),
                int(row.Volume) if not pd.isna(row.Volume) and pd.notnull(row.Volume) else 0
            ))
        print(f"✅ Dados de {ticker} inseridos com sucesso.")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 4, 15),
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='coleta_ativos_direto_cassandra',
    default_args=default_args,
    schedule_interval='*/15 * * * *',
    catchup=False,
    tags=['financas']
) as dag:
    tarefa_coleta = PythonOperator(
        task_id='coletar_ativos',
        python_callable=coletar_ativos
    )
    tarefa_coleta
