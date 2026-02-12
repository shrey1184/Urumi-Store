FROM python:3.12-slim

WORKDIR /app

# Install helm CLI
RUN apt-get update && apt-get install -y curl && \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# Copy helm charts into the image
COPY ../helm/ /helm/

ENV PYTHONUNBUFFERED=1
ENV HELM_BINARY=helm
ENV IN_CLUSTER=true
ENV STORE_CHART_PATH=/helm

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
