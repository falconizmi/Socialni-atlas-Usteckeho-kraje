FROM python:3.11

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# sestaveni imagge
# docker build -t nazev-containeru .

# Spuštění kontejneru na portu 8000
# docker run -d -p 8000:8000 --name atlas-backend nazev-docker-containaru