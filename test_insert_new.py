from db_supabase import insert_presenca
print("Inserindo novo evento sem presenca...")
try:
    resp = insert_presenca(1, 240, None)
    print("Sucesso:", resp)
except Exception as e:
    print("Erro:", e)
