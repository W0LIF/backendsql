from fastapi import FastAPI, BackgroundTasks
import os
import json
from run_parser import main as run_samara_parser

app = FastAPI(title="MFC Samara API")

@app.get("/")
def root():
    return {
        "message": "Сервер Самары запущен",
        "city": "samara",
        "docs": "/docs"
    }

@app.post("/parse")
def start_parsing(background_tasks: BackgroundTasks):
    """Запуск многопоточного парсинга Самары в фоне"""
    background_tasks.add_task(run_samara_parser, "samara")
    return {"status": "started", "info": "Парсинг Самары запущен в фоновом режиме"}

@app.get("/check-results")
def get_results():
    """Проверка наличия файлов в папке Самары"""
    path = "./backend/data/samara/"
    if os.path.exists(path):
        files = os.listdir(path)
        return {
            "city": "samara",
            "files_found": len(files),
            "filenames": files
        }
    return {"error": "Папка с данными еще не создана"}

@app.get("/health")
def health():
    return {"status": "ok"}