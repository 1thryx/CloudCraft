FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY app.py .

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN groupadd -r nonroot && useradd -r -g nonroot nonroot

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

RUN chown -R nonroot:nonroot /app

USER nonroot:nonroot

EXPOSE 5003

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]