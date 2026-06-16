from db_supabase import get_presencas_de_evento_filtrado
print("Buscando presencas do evento 253 para user 1...")
try:
    resp = get_presencas_de_evento_filtrado(253, [1])
    print("Sucesso:", resp)
except Exception as e:
    print("Erro:", e)
