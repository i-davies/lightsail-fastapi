# Lightsail FastAPI

API simples com FastAPI + PostgreSQL, preparada para desenvolvimento local (Docker Compose) e deploy no AWS Lightsail Container Service.

## 1) Rodando localmente

Pré-requisitos:
- Windows com PowerShell
- Docker Desktop
- Python 3.10+ e pip

Passo a passo (PowerShell):

1. Suba o PostgreSQL local com Docker Compose:
```powershell
# Na raiz do projeto
docker compose up -d
```

2. Configure as variáveis de ambiente (local, sem TLS):
- Edite o arquivo `.env` (ou copie do `.env.example`) com:
```
PGHOST=localhost
PGPORT=5432
PGDATABASE=postgres
PGUSER=postgres
PGPASSWORD=postgres
PGSSLMODE=disable
```

3. Crie e ative a virtualenv, e instale as dependências:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

4. Rode a API localmente (CLI do FastAPI):
```powershell
fastapi dev
```



5. Teste:
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

> Dica: Se quiser rodar a API em container localmente, construa a imagem e passe o `.env`:
```powershell
docker build -t lightsail-fastapi-app .
docker run --rm -it -p 8000:8000 --env-file .env lightsail-fastapi-app
```
Se o Postgres estiver no host (Docker Desktop), use `PGHOST=host.docker.internal` no `.env`.

---

## 2) Enviar a imagem para o Docker Hub

1. Faça login no Docker Hub:
```powershell
docker login
```

2. Construa e marque a imagem com seu usuário do Docker Hub:
```powershell
# Substitua <usuario> pelo seu usuário do Docker Hub
docker build -t <usuario>/lightsail-fastapi:latest .
```

3. Envie (push) a imagem:
```powershell
docker push <usuario>/lightsail-fastapi:latest
```

> Anote o nome completo da imagem (ex.: `docker.io/<usuario>/lightsail-fastapi:latest`). Ele será usado no Lightsail.

---

## 3) Usar no AWS Lightsail Container Service (gratuito)

No console do Lightsail:
1. Crie um Container Service (escolha o menor plano disponível; verifique as condições do período gratuito na página da AWS).
2. Adicione um deployment usando a imagem do Docker Hub (ex.: `docker.io/<usuario>/lightsail-fastapi:latest`).
3. Configure o container:
   - Porta de escuta: 8000 (o Dockerfile já inicia `uvicorn` nessa porta)
   - Endpoint público: habilitado na porta 8000
   - Health check HTTP: path `/health`
4. Configure as variáveis de ambiente do banco gerenciado (Lightsail Managed Database):
   - `PGHOST` = endpoint do banco
   - `PGPORT` = `5432`
   - `PGDATABASE` = nome do seu DB
   - `PGUSER` = usuário
   - `PGPASSWORD` = senha
   - `PGSSLMODE` = `require` (recomendado para banco gerenciado)
5. Salve e faça o deploy. Acesse a URL pública do serviço (exposta pelo Lightsail) e teste `/health` e `/docs`.

> Observações:
> - O arquivo `.env` não vai dentro da imagem; defina as variáveis no Lightsail.
> - Para desenvolvimento local, use `PGSSLMODE=disable`; em produção (Lightsail DB), use `require`.