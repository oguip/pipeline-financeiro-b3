import yfinance as yf
import pandas as pd
from flask import Flask, jsonify, request
from cassandra.cluster import Cluster
import time
import calendar
import datetime

app = Flask(__name__)

ATIVOS = ['^BVSP', 'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA', 'SANB11.SA', 'WEGE3.SA', 'ABEV3.SA', 'RENT3.SA']

def conectar_cassandra(max_tentativas=20, espera=5):
    tentativas = 0
    while tentativas < max_tentativas:
        try:
            cluster = Cluster(['cassandra'], port=9042, connect_timeout=10)
            session = cluster.connect()
            print("✅ Conexão com Cassandra estabelecida.")
            return session
        except Exception as e:
            tentativas += 1
            print(f"Tentativa {tentativas}: Cassandra não está pronto ainda.")
            time.sleep(espera)
    raise Exception("Erro ao conectar ao Cassandra.")

def criar_keyspace_e_tabela(session):
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
    print("✅ Tabela `ibov` criada com sucesso.")

def carregar_historico(session, ticker):
    print(f"🔁 Coletando histórico de 3 meses para {ticker}...")
    ativo = yf.Ticker(ticker)
    hist = ativo.history(period="60d", interval="15m")
    hist = hist.reset_index()
    for _, row in hist.iterrows():
        dt = pd.to_datetime(row['Datetime'])
        session.execute("""
            INSERT INTO ibov (ticker, datetime, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            ticker,
            dt.to_pydatetime(),
            float(row['Open']),
            float(row['High']),
            float(row['Low']),
            float(row['Close']),
            int(row['Volume']) if not pd.isna(row['Volume']) else 0
        ))
    print(f"✅ Histórico de {ticker} carregado.")

@app.route('/')
def health_check():
    return {'status': 'ok'}, 200

@app.route("/cotacoes", methods=["GET"])
def listar_todos():
    resultados = session.execute("SELECT * FROM ibov")
    dados = [dict(row._asdict()) for row in resultados]
    return jsonify(dados)

@app.route("/ativos", methods=["GET"])
def listar_ativos_disponiveis():
    return jsonify(ATIVOS)

@app.route("/cotacoes/<ticker>", methods=["GET"])
def listar_por_ativo(ticker):
    from_ts = request.args.get("from")
    to_ts = request.args.get("to")
    if from_ts and to_ts:
        try:
            from_ts = int(from_ts)
            to_ts = int(to_ts)
        except ValueError:
            return {"error": "Parâmetros de tempo inválidos."}, 400
        from_dt = datetime.utcfromtimestamp(from_ts)
        to_dt = datetime.utcfromtimestamp(to_ts)
        resultados = session.execute(
            "SELECT * FROM ibov WHERE ticker=%s AND datetime >= %s AND datetime <= %s",
            [ticker, from_dt, to_dt]
        )
    else:
        resultados = session.execute("SELECT * FROM ibov WHERE ticker=%s", [ticker])
    dados = []
    for row in resultados:
        r = row._asdict()
        timestamp_ms = int(calendar.timegm(r["datetime"].timetuple()) * 1000)
        dados.append({
            "timestamp": timestamp_ms,
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"]
        })
    return jsonify(dados)

@app.route("/cotacoes/<ticker>/<campo>", methods=["GET"])
def listar_campo_por_ativo(ticker, campo):
    if campo not in ["open", "high", "low", "close", "volume"]:
        return {"error": "Campo inválido."}, 400
    from_ts = request.args.get("from")
    to_ts = request.args.get("to")
    query = f"SELECT datetime, {campo} FROM ibov WHERE ticker=%s"
    params = [ticker]
    if from_ts and to_ts:
        try:
            from_ts = int(from_ts)
            to_ts = int(to_ts)
        except ValueError:
            return {"error": "Parâmetros de tempo inválidos."}, 400
        from_dt = datetime.utcfromtimestamp(from_ts)
        to_dt = datetime.utcfromtimestamp(to_ts)
        query += " AND datetime >= %s AND datetime <= %s"
        params.extend([from_dt, to_dt])
    resultados = session.execute(query, params)
    dados = []
    for row in resultados:
        valor = getattr(row, campo)
        timestamp_ms = int(calendar.timegm(row.datetime.timetuple()) * 1000)
        dados.append([valor, timestamp_ms])
    return jsonify([{"datapoints": dados}])

if __name__ == "__main__":
    session = conectar_cassandra()
    criar_keyspace_e_tabela(session)
    for ativo in ATIVOS:
        carregar_historico(session, ativo)
    app.run(host="0.0.0.0", port=5000)
