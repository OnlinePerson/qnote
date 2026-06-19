FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn[standard] aiofiles python-dotenv
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
