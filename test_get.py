from db_supabase import get_presenca
print("Buscando presenca...")
try:
    resp = get_presenca(1, 253, None)
    print("Sucesso get_presenca:", resp)
except Exception as e:
    print("Erro get_presenca:", e)
