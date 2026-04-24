# Stage 1 — Build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt --ignore-requires-python || true && \
    pip install --no-cache-dir --user flask azure-storage-blob azure-identity python-dotenv prometheus-client web3

# Stage 2 — Production
FROM python:3.11-slim AS production
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ .
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]