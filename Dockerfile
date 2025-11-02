# Imagem para a aplicação FastAPI (sem banco)
# Adequada para uso no AWS Lightsail Container Service

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Dependências do sistema mínimas (certificados + locale + tz + build deps se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências primeiro (cache eficiente de camadas)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY ./main.py ./

# Usuário não-root por segurança
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Porta exposta pelo uvicorn
EXPOSE 8000

# Por padrão, usamos TLS no banco (Lightsail). Para ambiente local, defina PGSSLMODE=disable
# Variáveis típicas esperadas:
#   PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, PGSSLMODE

# Comando de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
