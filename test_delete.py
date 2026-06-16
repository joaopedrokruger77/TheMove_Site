from db_supabase import delete_presenca
print("Deletando presenca...")
try:
    delete_presenca(1, 253, None)
    print("Sucesso!")
except Exception as e:
    print("Erro:", e)
