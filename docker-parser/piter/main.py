from fastapi import FastAPI
import os

app = FastAPI()

# Определяем город из переменной окружения (берется из docker-compose)
CITY = os.getenv("PARSER_CITY", "unknown")

@app.get("/")
def home():
    # Проверяем, видит ли контейнер свои данные
    data_path = f"./data/{CITY}"
    files_count = 0
    if os.path.exists(data_path):
        files_count = len([f for f in os.listdir(data_path) if f.endswith('.json')])
    
    return {
        "status": "working",
        "city": CITY,
        "database_info": f"Found {files_count} JSON files in {data_path}"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}