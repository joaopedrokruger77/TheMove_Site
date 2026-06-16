# =================================================================
# supabase_client.py — Inicialização do cliente Supabase
# Lê as credenciais do arquivo .env e cria um cliente singleton.
# Importado por db_supabase.py
# =================================================================

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# A URL fornecida aponta para o endpoint REST (/rest/v1/).
# O SDK do Supabase precisa apenas da URL base do projeto.
# Removemos o sufixo /rest/v1/ se estiver presente.
if SUPABASE_URL and SUPABASE_URL.endswith("/rest/v1/"):
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1/", "")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_URL e SUPABASE_ANON_KEY devem estar definidos no arquivo .env"
    )

# Cliente singleton — reutilizado em toda a aplicação
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
