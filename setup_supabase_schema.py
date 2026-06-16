"""
setup_supabase_schema.py
Cria as tabelas no Supabase usando a API de SQL (rpc exec_sql ou REST).
Execute: python setup_supabase_schema.py
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL_RAW = os.environ.get("SUPABASE_URL", "")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

# Base URL sem o /rest/v1/
BASE_URL = SUPABASE_URL_RAW.replace("/rest/v1/", "")

HEADERS = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json",
}

SQL_STATEMENTS = [
    # Tabela usuarios
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id        BIGSERIAL PRIMARY KEY,
        nome      TEXT NOT NULL,
        email     TEXT UNIQUE NOT NULL,
        senha     TEXT NOT NULL,
        nascimento TEXT,
        username  TEXT UNIQUE NOT NULL,
        foto      TEXT,
        bio       TEXT,
        tags      TEXT
    )
    """,
    # Tabela seguidores
    """
    CREATE TABLE IF NOT EXISTS seguidores (
        id          BIGSERIAL PRIMARY KEY,
        seguidor_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        seguido_id  BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """,
    # Tabela eventos
    """
    CREATE TABLE IF NOT EXISTS eventos (
        id         BIGSERIAL PRIMARY KEY,
        nome       TEXT,
        local      TEXT,
        data       TEXT,
        imagem     TEXT,
        tipo       TEXT,
        link       TEXT,
        tags       TEXT,
        criador_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL
    )
    """,
    # Tabela presencas
    """
    CREATE TABLE IF NOT EXISTS presencas (
        id         BIGSERIAL PRIMARY KEY,
        usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        evento_id  BIGINT NOT NULL REFERENCES eventos(id) ON DELETE CASCADE
    )
    """,
    # Seed admin
    """
    INSERT INTO usuarios (nome, email, senha, nascimento, username, tags)
    VALUES ('the move', 'adm@themove.com', 'themove10neymar@', '2026-01-01', '@themove', 'Admin,Todos')
    ON CONFLICT (username) DO NOTHING
    """,
]

def run_sql(sql: str, description: str):
    """Executa SQL via endpoint /rest/v1/rpc/exec_sql (precisa de função no Supabase)."""
    # Usamos o endpoint direto do PostgREST para queries simples via RPC
    url = f"{BASE_URL}/rest/v1/rpc/exec_sql"
    resp = httpx.post(url, headers=HEADERS, json={"query": sql.strip()}, timeout=30)
    
    if resp.status_code in (200, 201, 204):
        print(f"  ✅ {description}")
        return True
    else:
        print(f"  ⚠️  {description} — Status {resp.status_code}: {resp.text[:200]}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  THE MOVE SITE — Setup Supabase Schema")
    print("=" * 60)
    print()
    print("IMPORTANTE: Se este script falhar com erro 404/400,")
    print("execute manualmente o arquivo supabase_schema.sql no")
    print("Supabase SQL Editor:")
    print(f"  https://supabase.com/dashboard/project/ikrhzfdnrodphsjfsmyj/sql")
    print()
    
    descriptions = [
        "Criar tabela usuarios",
        "Criar tabela seguidores",
        "Criar tabela eventos",
        "Criar tabela presencas",
        "Inserir admin @themove",
    ]
    
    for sql, desc in zip(SQL_STATEMENTS, descriptions):
        run_sql(sql, desc)
    
    print()
    print("Verificando tabelas criadas...")
    from supabase_client import supabase
    for tabela in ["usuarios", "seguidores", "eventos", "presencas"]:
        try:
            resp = supabase.table(tabela).select("id").limit(1).execute()
            print(f"  ✅ Tabela '{tabela}' acessível")
        except Exception as e:
            print(f"  ❌ Tabela '{tabela}' com problema: {e}")
