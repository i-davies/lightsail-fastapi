# SPDX-License-Identifier: MIT
# Exemplo simples de FastAPI + PostgreSQL para AWS Lightsail
"""API de exemplo com FastAPI e PostgreSQL (AWS Lightsail).

Este módulo expõe uma API REST simples para gerenciar tarefas (todos),
criando a tabela no banco de dados durante a inicialização da aplicação.
"""

import os
try:
    # Carrega variáveis do arquivo .env (se existir)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    # Se python-dotenv não estiver instalado, apenas ignora
    pass
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Ler variáveis de ambiente
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "postgres")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "")
# Permite configurar o modo SSL via variável; em produção use "require", localmente use "disable"
PGSSLMODE = os.getenv("PGSSLMODE", "require")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ciclo de vida da aplicação.

    Na inicialização, garante que a tabela `todos` exista.
    No encerramento, não há limpeza necessária (conexões são por requisição).
    """
    # Inicialização: cria a tabela se não existir
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS todos (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    );
                    """
                )
                conn.commit()
    except psycopg2.Error as e:
        # Não derruba a API em erro de inicialização; apenas registra para depuração
        print(f"[startup] DB init error: {e}")

    # Entrega o controle para execução do app
    yield

    # Encerramento: nada a limpar (conexões são por requisição)


app = FastAPI(title="Lightsail FastAPI Demo", version="1.0.0", lifespan=lifespan)


def get_conn():
    """Abre e retorna uma nova conexão com o PostgreSQL usando as variáveis de ambiente."""
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        connect_timeout=5,
        sslmode=PGSSLMODE,  # Em Lightsail, use "require"; para Docker local, use "disable"
    )


class TodoIn(BaseModel):
    """Modelo de entrada para criar uma tarefa (todo)."""
    title: str


class TodoOut(BaseModel):
    """Modelo de saída que representa uma tarefa (todo)."""
    id: int
    title: str
    done: bool


@app.get("/health")
def health():
    """Verifica a saúde da aplicação e a conectividade com o banco de dados."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        db_status = "ok"
    except psycopg2.Error as e:
        db_status = f"error: {e}"
    return {"service": "ok", "database": db_status}


@app.get("/")
def root():
    """Endpoint raiz que retorna uma mensagem e o link da documentação."""
    return {"message": "Lightsail FastAPI Demo", "docs": "/docs"}


@app.get("/todos", response_model=list[TodoOut])
def list_todos():
    """Lista todas as tarefas em ordem decrescente de ID."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, title, done FROM todos ORDER BY id DESC")
            rows = cur.fetchall()
            return [
                TodoOut(id=r["id"], title=r["title"], done=r["done"])  # mapeamento explícito para analisadores de tipo
                for r in rows
            ]


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(todo: TodoIn):
    """Cria uma nova tarefa com o título informado e retorna o registro criado."""
    if not todo.title.strip():
        raise HTTPException(status_code=400, detail="título é obrigatório")
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO todos(title, done) VALUES (%s, FALSE) RETURNING id, title, done",
                (todo.title.strip(),),
            )
            row = cur.fetchone()
            conn.commit()
            if not row:
                raise HTTPException(status_code=500, detail="falha ao inserir registro")
            return TodoOut(id=row["id"], title=row["title"], done=row["done"])  # mapeamento explícito


@app.patch("/todos/{todo_id}", response_model=TodoOut)
def toggle_done(todo_id: int):
    """Alterna o campo `done` (concluída) da tarefa com o ID informado."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE todos SET done = NOT done WHERE id = %s RETURNING id, title, done",
                (todo_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="não encontrado")
            conn.commit()
            return TodoOut(id=row["id"], title=row["title"], done=row["done"])  # mapeamento explícito


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    """Exclui a tarefa com o ID informado."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="não encontrado")
            conn.commit()
            return None
