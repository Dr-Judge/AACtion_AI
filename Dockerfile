FROM python:3.13-slim

WORKDIR /app

# chromadb(hnswlib)가 3.13용 사전 빌드 wheel이 없을 수 있어 빌드 도구를 설치해둔다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
