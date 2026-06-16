from supabase_client import supabase

print("=== LIMPEZA E EXPANSÃO ===")

# 1. Remover restaurantes
print("Removendo restaurantes...")
supabase.table('eventos').delete().eq('tipo', 'restaurante').execute()

# 2. Adicionar shows reais de 2027 em BSB e baladas semanais
admin_resp = supabase.table('usuarios').select('id').eq('username', '@themove').execute()
admin_id = admin_resp.data[0]['id'] if admin_resp.data else 1

novos_shows = [
    # SHOWS 2027 EM BSB
    {'nome': 'JORGE & MATEUS - TERRA SEM CEP', 'local': 'Arena BRB - Asa Norte', 'data': 'Março 2027', 'tipo': 'show', 'tags': 'sertanejo, show grande, jovem, adulto', 'is_sponsored': False},
    {'nome': 'ANA CASTELA EM BSB', 'local': 'Parque da Cidade', 'data': 'Abril 2027', 'tipo': 'show', 'tags': 'sertanejo, boiadeira, jovem', 'is_sponsored': False},
    {'nome': 'MATUÊ - 333 TOUR', 'local': 'Arena BRB - Asa Norte', 'data': 'Maio 2027', 'tipo': 'show', 'tags': 'rap, trap, jovem', 'is_sponsored': False},
    {'nome': 'ALOK IN BSB', 'local': 'Setor de Clubes Sul', 'data': 'Junho 2027', 'tipo': 'show', 'tags': 'eletrônica, dj, jovem, adulto', 'is_sponsored': False},
    {'nome': 'THIAGUINHO - TARDEZINHA BSB', 'local': 'Pontão do Lago Sul', 'data': 'Julho 2027', 'tipo': 'show', 'tags': 'pagode, samba, adulto, jovem', 'is_sponsored': False},
    {'nome': 'ZECA PAGODINHO - TREM BALA', 'local': 'Arena BRB - Asa Norte', 'data': 'Agosto 2027', 'tipo': 'show', 'tags': 'pagode, samba, adulto', 'is_sponsored': False},
    {'nome': 'IVETE SANGALO EM BSB', 'local': 'Estádio Mané Garrincha', 'data': 'Setembro 2027', 'tipo': 'show', 'tags': 'axé, pop, jovem, adulto, grande', 'is_sponsored': False},
    {'nome': 'CAPITAL INICIAL - ACÚSTICO', 'local': 'Teatro Nacional', 'data': 'Outubro 2027', 'tipo': 'show', 'tags': 'rock nacional, adulto', 'is_sponsored': False},
    {'nome': 'LUDMILLA - NUMANICE BSB', 'local': 'Parque da Cidade', 'data': 'Novembro 2027', 'tipo': 'show', 'tags': 'pagode, funk, pop, jovem', 'is_sponsored': False},
    {'nome': 'WESLEY SAFADÃO - SAFADÃO EM BSB', 'local': 'Arena BRB - Asa Norte', 'data': 'Dezembro 2027', 'tipo': 'show', 'tags': 'forró, sertanejo, jovem, adulto', 'is_sponsored': False},
    {'nome': 'RACIONAIS MC\'S - 30 ANOS', 'local': 'Arena BRB - Asa Norte', 'data': 'Fevereiro 2027', 'tipo': 'show', 'tags': 'rap, hip-hop, adulto', 'is_sponsored': False},
    {'nome': 'MARISA MONTE EM BSB', 'local': 'Centro de Convenções - Asa Sul', 'data': 'Março 2027', 'tipo': 'show', 'tags': 'mpb, jazz, adulto', 'is_sponsored': False},
    {'nome': 'FRESNO - 20 ANOS DE TURNÊ', 'local': 'Centro de Convenções - Asa Sul', 'data': 'Abril 2027', 'tipo': 'show', 'tags': 'rock, emo, indie, jovem', 'is_sponsored': False},
    {'nome': 'MC CABELINHO & POZE DO RODO', 'local': 'AABB - Lago Sul', 'data': 'Janeiro 2027', 'tipo': 'show', 'tags': 'funk, trap, jovem', 'is_sponsored': False},
    {'nome': 'DJAVAN - AO VIVO', 'local': 'Teatro Nacional', 'data': 'Maio 2027', 'tipo': 'show', 'tags': 'mpb, jazz, adulto', 'is_sponsored': False},
    
    # BALADAS SEMANAIS (recorrentes)
    {'nome': 'GARAGE BSB', 'local': 'Asa Sul', 'data': 'Sexta e Sábado', 'tipo': 'balada', 'tags': 'rock, indie, alternativo, jovem', 'is_sponsored': False},
    {'nome': 'ARMAZÉM DO FORRÓ', 'local': 'SAAN', 'data': 'Sexta a Domingo', 'tipo': 'balada', 'tags': 'forró, sertanejo, jovem, adulto', 'is_sponsored': False},
    {'nome': 'DUO MUSIC HALL', 'local': 'Asa Sul', 'data': 'Sexta e Sábado', 'tipo': 'balada', 'tags': 'eletrônica, funk, pop, jovem', 'is_sponsored': False},
]

for ev in novos_shows:
    ev['criador_id'] = admin_id
    ev['source'] = 'themove'
    ev['imagem'] = ''
    ev['link'] = '#'

print(f"Inserindo {len(novos_shows)} shows e baladas...")
supabase.table('eventos').insert(novos_shows).execute()

# 3. Limpar cache de recomendações
print("Limpando cache de recomendações...")
supabase.table('recomendacoes_cache').delete().neq('id', 0).execute()

# 4. Verificar resultado
resp = supabase.table('eventos').select('id,nome,tipo').execute()
tipos = {}
for e in resp.data:
    t = e['tipo']
    tipos[t] = tipos.get(t, 0) + 1

print(f"\n=== RESUMO DO BANCO ===")
print(f"Total de eventos: {len(resp.data)}")
for t, c in sorted(tipos.items()):
    print(f"  {t}: {c}")
print("Pronto!")
