FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Default role: Web UI (Streamlit). Override in docker-compose / Render worker to run `python main.py`.
CMD ["streamlit", "run", "news_aggregator/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]