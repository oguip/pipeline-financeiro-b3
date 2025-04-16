@echo off
setlocal enabledelayedexpansion
cls

echo ===================================================
echo INICIANDO PROJETO - B3
echo ===================================================
echo.

echo [1/6] Subindo containers Docker...
docker-compose up -d --build

echo [2/6] Aguardando inicialização dos serviços...
timeout /t 90 >nul

echo [3/6] Instalando bibliotecas no Airflow...
docker exec -it airflow-web python -m pip install --user yfinance pandas cassandra-driver

echo [5/6] Reiniciando Airflow para carregar DAGs...
docker restart airflow-web
docker restart airflow-scheduler

echo [6/6] Abrindo interfaces no navegador...
start http://localhost:8082
start http://localhost:5000/cotacoes
start http://localhost:3000

echo.
echo Projeto iniciado com sucesso! Logs de execução serao exibidos abaixo:
echo ---------------------------------------------------

REM :: Logs contínuos da API Flask
docker logs api-ibov --follow
