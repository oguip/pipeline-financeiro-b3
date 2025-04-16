
from airflow import DAG
from airflow.operators.python import PythonOperator
from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import pandas as pd

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def limpar_dados_antigos():
    cluster = Cluster(['cassandra'])
    session = cluster.connect('cotacoes')
    
    # Buscar as datas disponíveis (exemplo com 1 ativo, assume que são iguais nos outros)
    resultados = session.execute("SELECT DISTINCT datetime FROM ibov WHERE ticker='PETR4.SA'")
    datas = sorted([row.datetime.date() for row in resultados])

    if len(datas) > 1:
        data_mais_antiga = datas[0]
        print(f"🧹 Removendo dados do dia: {data_mais_antiga}")

        # Remover dados antigos para todos os tickers
        ativos = ['^BVSP', 'PETR4.SA', 'VALE3.SA', 'ITUB4.SA']
        for ativo in ativos:
            query = f"DELETE FROM ibov WHERE ticker=%s AND datetime=%s"
            # Deleta todos os horários do dia específico
            resultados = session.execute("SELECT datetime FROM ibov WHERE ticker=%s ALLOW FILTERING", [ativo])
            for row in resultados:
                if row.datetime.date() == data_mais_antiga:
                    session.execute(query, (ativo, row.datetime))
        print("✅ Limpeza concluída.")
    else:
        print("⚠️ Nenhum dado antigo para remover.")

with DAG(
    dag_id='limpeza_diaria_dag',
    default_args=default_args,
    schedule_interval='@daily',  # Executa diariamente
    catchup=False
) as dag:

    tarefa_limpeza = PythonOperator(
        task_id='limpar_dados_antigos',
        python_callable=limpar_dados_antigos
    )
