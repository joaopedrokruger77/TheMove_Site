from supabase_client import supabase

resp = supabase.table('eventos').select('id,nome,source,imagem,is_sponsored').execute()
for e in resp.data:
    print(f"{e['id']} - {e['nome']} - src:{e['source']} - img:{e['imagem']} - spons:{e['is_sponsored']}")

# Delete wrong events:
print("Limpando lixo...")
supabase.table('eventos').delete().eq('imagem', 'contexto.jpg').eq('tipo', 'bar').execute()
supabase.table('eventos').delete().eq('nome', 'Panificadora Cinco Estrelas').execute()
supabase.table('eventos').delete().eq('nome', 'Bar do Juca').execute()

print("Feito")
