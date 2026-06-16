from supabase_client import supabase

print("=== UPDATE LOCATIONS & ADD NEW PLACES ===")

# 1. Update Na Praia and Quinta Marcha locations
supabase.table('eventos').update({'local': 'Setor de Clubes Sul'}).eq('nome', 'Na Praia Festival').execute()
supabase.table('eventos').update({'local': 'Setor de Clubes Sul'}).eq('nome', 'Quinta Marcha').execute()
# Let's just update all matching na praia and quinta marcha
resp = supabase.table('eventos').select('id,nome,local,tags').execute()
for ev in resp.data:
    nome = ev['nome'].lower()
    if 'na praia' in nome or 'quinta marcha' in nome:
        print(f"Updating location for {ev['nome']}")
        supabase.table('eventos').update({'local': 'Setor de Clubes Sul'}).eq('id', ev['id']).execute()
    
    # 2. Update Deboche to be strictly young
    if 'deboche' in nome or 'deboxe' in nome:
        print(f"Updating tags for {ev['nome']}")
        # Remove 'adulto' if present, add 'jovem' if not present
        tags = ev['tags'].replace('adulto', '').replace(', ,', ',')
        if 'jovem' not in tags:
            tags += ', jovem'
        supabase.table('eventos').update({'tags': tags}).eq('id', ev['id']).execute()

# 3. Add new places from article
admin_resp = supabase.table('usuarios').select('id').eq('username', '@themove').execute()
admin_id = admin_resp.data[0]['id'] if admin_resp.data else 1

novos_locais = [
    {'nome': 'Clube do Choro', 'local': 'Eixo Monumental', 'data': 'Sexta a Domingo', 'tipo': 'show', 'tags': 'choro, samba, mpb, adulto', 'is_sponsored': False},
    {'nome': 'Carcassonne Pub', 'local': 'Asa Norte - 407 Norte', 'data': 'Quarta a Domingo', 'tipo': 'bar', 'tags': 'pub, jogos, cerveja artesanal, jovem, adulto', 'is_sponsored': False},
    {'nome': 'O\'Rilley', 'local': 'Asa Sul - 409 Sul', 'data': 'Terça a Sábado', 'tipo': 'bar', 'tags': 'rock, blues, pub, adulto, jovem', 'is_sponsored': False},
    {'nome': 'UK Music Hall', 'local': 'Asa Sul - 411 Sul', 'data': 'Terça a Sábado', 'tipo': 'bar', 'tags': 'rock, pop rock, pub, adulto', 'is_sponsored': False},
    {'nome': 'Forró ao Pôr do Sol', 'local': 'Praça do Cruzeiro', 'data': 'Domingo 17h', 'tipo': 'festa', 'tags': 'forró, dança, jovem, adulto', 'is_sponsored': False},
    {'nome': 'Sexta Gode no Arena Bar', 'local': 'Estádio Mané Garrincha', 'data': 'Sexta-feira', 'tipo': 'festa', 'tags': 'pagode, jovem, adulto', 'is_sponsored': False},
]

for ev in novos_locais:
    ev['criador_id'] = admin_id
    ev['source'] = 'themove'
    ev['imagem'] = ''
    ev['link'] = '#'

print(f"Inserindo {len(novos_locais)} novos locais...")
supabase.table('eventos').insert(novos_locais).execute()

# Limpar cache do gemini novamente para atualizar a ia
supabase.table('recomendacoes_cache').delete().neq('id', 0).execute()

print("Pronto!")
