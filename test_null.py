from db_supabase import get_presenca
print("Buscando null...")
try:
    resp = get_presenca(1, 253, None)
    print("Sucesso:", resp)
except Exception as e:
    print("Erro:", e)
