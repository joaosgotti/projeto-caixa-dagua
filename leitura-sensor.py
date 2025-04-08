import sqlite3
import time
import datetime
import threading
import os
import RPi.GPIO as GPIO

# Configuração do GPIO
GPIO.setwarnings(False)
TRIG = 23
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Define o caminho correto do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leituras.db")

# Função para medir a distância
def medir_distancia():
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()

    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distancia = pulse_duration * 17150
    return round(distancia, 2)

# Verifica a saude do dado
def dado_saudavel(distancia, media_5_ultimas):
    if media_5_ultimas is None or distancia is None:
        return False

    margem = 0.2
    limite_superior = media_5_ultimas * (1 + margem)
    limite_inferior = media_5_ultimas * (1 - margem)
    
    return limite_inferior <= distancia <= limite_superior


# Função para salvar no banco de dados
def salvar_no_bd(distancia):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(distancia)
        FROM (
            SELECT distancia
            FROM leituras
            ORDER BY timestamp DESC
            LIMIT 5
        )
    """)

    media_5_ultimas = cursor.fetchone()[0]

    if dado_saudavel(distancia, media_5_ultimas):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO leituras (timestamp, distancia) VALUES (?, ?)", (timestamp, distancia))
        conn.commit()

    else:
        print(f"Distância {distancia:.2f} ignorada (fora de 20% da média {media_5_ultimas:.2f})")
    
    conn.close()

# Criando a tabela no banco de dados
def criar_tabela():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        distancia REAL
    )
    ''')
    conn.commit()
    conn.close()

# Função principal para iniciar as medições continuamente
def iniciar_medicoes():
    while True:
        distancia = medir_distancia()
        print(f"Distância medida: {distancia} cm")
        if check_saude_sensor(distancia):
            salvar_no_bd(distancia)
        time.sleep(10)

# Criar tabela no banco e iniciar medições
criar_tabela()
iniciar_medicoes()
