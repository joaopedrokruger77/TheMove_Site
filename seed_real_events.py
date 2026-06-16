from supabase_client import supabase

print("Deletando Boteco do Juca...")
supabase.table('eventos').delete().eq('nome', 'BOTECO DO JUCA').execute()

print("Buscando admin id...")
admin_resp = supabase.table('usuarios').select('id').eq('username', '@themove').execute()
admin_id = admin_resp.data[0]['id'] if admin_resp.data else 1

novos = [
    # BALADAS E CLUBES
    {'nome': 'BIROSCA DO CONIC', 'local': 'Conic', 'data': 'Sexta e Sábado', 'tipo': 'balada', 'tags': 'alternativo, funk, eletrônica, jovem', 'is_sponsored': False},
    {'nome': 'COMPLEXO FORA DO EIXO', 'local': 'SAAN', 'data': 'Sexta a Domingo', 'tipo': 'balada', 'tags': 'pagode, funk, sertanejo, jovem, agito', 'is_sponsored': False},
    {'nome': 'MEZANINO BRB', 'local': 'Torre de TV', 'data': 'Fim de semana', 'tipo': 'balada', 'tags': 'eletrônica, house, premium, adulto, vista', 'is_sponsored': False},
    {'nome': 'CAFE DE LA MUSIQUE', 'local': 'Setor de Clubes Sul', 'data': 'Sábados', 'tipo': 'balada', 'tags': 'eletrônica, premium, luxo', 'is_sponsored': False},
    {'nome': 'PISTINHA', 'local': 'Setor Comercial Sul', 'data': 'Sexta', 'tipo': 'balada', 'tags': 'eletrônica, techno, alternativo', 'is_sponsored': False},
    {'nome': 'PUTZ CLUB', 'local': 'SAAN', 'data': 'Sexta e Sábado', 'tipo': 'balada', 'tags': 'pop, funk, lgbtqia+', 'is_sponsored': False},
    {'nome': 'VICTORIA HAUS', 'local': 'SAAN', 'data': 'Sábado', 'tipo': 'balada', 'tags': 'pop, funk, lgbtqia+, show', 'is_sponsored': False},
    
    # BARES E BOTECOS ANIMADOS
    {'nome': 'PRIMEIRO BAR', 'local': 'Sudoeste', 'data': 'Terça a Domingo', 'tipo': 'bar', 'tags': 'pagode, rock, música ao vivo, chopp, adulto', 'is_sponsored': False},
    {'nome': 'MIAU QUE MIA', 'local': 'Asa Sul', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'barato, jovem, amigos, cerveja', 'is_sponsored': False},
    {'nome': 'BEIRUTE', 'local': 'Asa Sul / Asa Norte', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'tradicional, amigos, cerveja, família', 'is_sponsored': False},
    {'nome': 'FAUSTO & MANOEL', 'local': 'Asa Norte', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'chopp, petiscos, adulto, família', 'is_sponsored': False},
    {'nome': 'PINELLA', 'local': 'Asa Norte', 'data': 'Segunda a Sábado', 'tipo': 'bar', 'tags': 'rock, jazz, alternativo, cerveja artesanal', 'is_sponsored': False},
    {'nome': 'PORKS', 'local': 'Águas Claras / Asa Sul', 'data': 'Terça a Domingo', 'tipo': 'bar', 'tags': 'porco, chopp, rock, barato', 'is_sponsored': False},
    {'nome': 'VILA TAREGO', 'local': 'Park Way', 'data': 'Quinta a Domingo', 'tipo': 'bar', 'tags': 'hamburguer, cerveja, descontraído', 'is_sponsored': False},
    {'nome': 'LIVING HNK', 'local': 'Aeroporto', 'data': '24 horas', 'tipo': 'bar', 'tags': 'chopp, rock, aeroporto', 'is_sponsored': False},
    {'nome': 'BAR BRASÍLIA', 'local': 'Asa Sul', 'data': 'Segunda a Sábado', 'tipo': 'bar', 'tags': 'tradicional, mpb, chopp, boemia', 'is_sponsored': False},
    {'nome': 'MENDES BAR', 'local': 'Asa Norte', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'universitário, barato, litrão', 'is_sponsored': False},
    
    # LUGARES GASTRONÔMICOS / VIBE MAIS CALMA
    {'nome': 'MANÉ MERCADO', 'local': 'Eixo Monumental', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'gastronomia, variedade, vinho, família, amigos, premium', 'is_sponsored': False},
    {'nome': 'SALLVA', 'local': 'Pontão do Lago Sul', 'data': 'Todo dia', 'tipo': 'restaurante', 'tags': 'vinho, premium, casal, romântico, vista', 'is_sponsored': False},
    {'nome': 'TAYPÁ', 'local': 'Lago Sul', 'data': 'Todo dia', 'tipo': 'restaurante', 'tags': 'peruano, premium, romântico, vinho', 'is_sponsored': False},
    {'nome': 'OLI RESTAURANTE', 'local': 'Asa Sul', 'data': 'Terça a Domingo', 'tipo': 'restaurante', 'tags': 'italiano, romântico, vinho, casal', 'is_sponsored': False},
    {'nome': 'CARPE DIEM', 'local': 'Asa Sul', 'data': 'Todo dia', 'tipo': 'restaurante', 'tags': 'tradicional, almoço, vinho, calmo', 'is_sponsored': False},
    {'nome': 'TICIANA WERNER', 'local': 'Asa Sul', 'data': 'Segunda a Sábado', 'tipo': 'restaurante', 'tags': 'vinho, jazz ao vivo, fondue, romântico', 'is_sponsored': False},
    {'nome': 'SANTÉ 13', 'local': 'Asa Norte', 'data': 'Todo dia', 'tipo': 'restaurante', 'tags': 'romântico, vinho, jantar, premium', 'is_sponsored': False},
    {'nome': 'BIERFASS LAGO', 'local': 'Pontão do Lago Sul', 'data': 'Todo dia', 'tipo': 'bar', 'tags': 'cerveja, vista, premium, almoço', 'is_sponsored': False},
    
    # SHOWS E EVENTOS GERAIS
    {'nome': 'BUTECO DO GUSTTAVO LIMA', 'local': 'Arena BRB', 'data': 'Outubro', 'tipo': 'show', 'tags': 'sertanejo, show grande, agito', 'is_sponsored': False},
    {'nome': 'SAMBA URBANO', 'local': 'Setor Comercial Sul', 'data': 'Sábado à tarde', 'tipo': 'festa', 'tags': 'samba, pagode, rua, jovem', 'is_sponsored': False},
    {'nome': 'FESTIVAL MOTO CAPITAL', 'local': 'Granja do Torto', 'data': 'Julho', 'tipo': 'festa', 'tags': 'rock, motos, cerveja, show grande, adulto', 'is_sponsored': False},
    {'nome': 'CHURRASCO ON FIRE - FERNANDO E SOROCABA', 'local': 'Parque da Cidade', 'data': 'Setembro', 'tipo': 'show', 'tags': 'sertanejo, churrasco, show grande', 'is_sponsored': False},
    {'nome': 'FESTA DA LILI', 'local': 'AABB', 'data': 'Mensal', 'tipo': 'festa', 'tags': 'eletrônica, lgbtqia+, agito, madrugada', 'is_sponsored': False},
]

for ev in novos:
    ev['criador_id'] = admin_id
    ev['source'] = 'themove'
    ev['imagem'] = ''
    ev['link'] = '#'

print("Inserindo 30 eventos reais curados...")
supabase.table('eventos').insert(novos).execute()

print("Limpando cache de recomendacoes para forcar atualizacao...")
supabase.table('recomendacoes_cache').delete().neq('id', 0).execute()

print("Pronto! Banco atualizado e limpo.")
