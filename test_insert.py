from db_supabase import insert_presenca
print("Inserindo presenca legitima...")
try:
    resp = insert_presenca(usuario_id=1, evento_id=253, data_presenca=None)
    print("Sucesso legitima:", resp)
except Exception as e:
    print("Erro legitima:", e)
