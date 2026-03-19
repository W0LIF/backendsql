FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install schedule

# Копируем весь код парсеров (все папки piter, moscow, samara)
COPY . .

# Запускаем управляющий скрипт, который мы обсуждали раньше (run_parsers.py)
CMD ["python", "run_parsers.py"]