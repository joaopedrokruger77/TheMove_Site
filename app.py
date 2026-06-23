import math
from flask import Flask, render_template, request, redirect, url_for, session, flash

# =================================================================
# MIGRAÇÃO SUPABASE: importa todas as funções de banco de dados
# do módulo db_supabase.py (substitui sqlite3 completamente)
# =================================================================
from db_supabase import (
    get_usuario_by_email_senha,
    get_usuario_by_username,
    get_usuario_by_id,
    get_todos_usuarios,
    buscar_usuarios,
    insert_usuario,
    update_usuario_preferencias,
    update_usuario_perfil,
    username_em_uso,
    get_todos_eventos,
    get_eventos_patrocinados,
    get_eventos_proximos,
    get_eventos_recentes,
    insert_evento,
    get_presenca,
    insert_presenca,
    delete_presenca,
    get_total_presencas,
    get_presencas_de_evento_com_usuario,
    get_presencas_de_evento_filtrado,
    get_presencas_de_usuario,
    contar_presencas_amigos_em_evento,
    get_ranking_eventos,
    get_seguindo,
    get_seguindo_ids,
    count_seguidores,
    count_seguindo,
    is_seguindo,
    insert_seguidor,
    delete_seguidor,
    get_sugestoes_usuarios,
    get_recomendacoes_cache,
    set_recomendacoes_cache,
    get_favoritos,
    add_favorito,
    remove_favorito,
)
from gemini_recommender import gerar_recomendacoes
from local_recommender import recomendar_por_tags, obter_coordenadas
import json
# =================================================================
# CÓDIGO SQLITE ORIGINAL — mantido comentado até validação final
# (remover após confirmar que tudo funciona no Supabase)
# -----------------------------------------------------------------
# import sqlite3
#
# def get_db():
#     conn = sqlite3.connect('themove.db')
#     conn.row_factory = sqlite3.Row
#     return conn
#
# def init_db():
#     with get_db() as db:
#         db.execute('''CREATE TABLE IF NOT EXISTS usuarios (...)''')
#         db.execute('''CREATE TABLE IF NOT EXISTS seguidores (...)''')
#         db.execute('''CREATE TABLE IF NOT EXISTS eventos (...)''')
#         db.execute('''CREATE TABLE IF NOT EXISTS presencas (...)''')
#         admin = db.execute("SELECT id FROM usuarios WHERE username = '@themove'").fetchone()
#         if not admin:
#             db.execute('''INSERT INTO usuarios ...''', (...))
#         db.commit()
#
# init_db()
# =================================================================

app = Flask(__name__)
app.secret_key = 'the_move_2026_pro_key'


# --- Módulo de IA (Recomendação Híbrida) ---
# NOTA: Esta função não foi alterada. Ela não acessa o banco diretamente,
# apenas recebe dados via parâmetros vindos das funções de abstração.
def calcular_similaridade_vetor(tags_user, tags_evento):
    """
    SISTEMA DE RECOMENDAÇÃO: CÁLCULO DE SIMILARIDADE (NOVO MÉTODO)
    Implementa a similaridade vetorial proposta pelo professor.
    Cria vetores, compara elementos iguais (u == e), soma os matches 
    e divide pelo tamanho do vetor.
    """
    # 1. Se o usuário ou o evento não tiverem tags, a similaridade é zero.
    if not tags_user or not tags_evento:
        return 0.0
        
    # 2. Transforma as palavras em listas únicas (sets) para remover duplicadas e padronizar
    set_user = set(tag.strip() for tag in tags_user.lower().split(',') if tag.strip())
    set_evento = set(tag.strip() for tag in tags_evento.lower().split(',') if tag.strip())
    
    # 3. Une todas as palavras (tags) possíveis em um único grupo (o tamanho do vetor)
    todas_tags = set_user.union(set_evento)
    
    if len(todas_tags) == 0:
        return 0.0
    
    # 4. Cria vetores (listas de 0 ou 1). 
    # Coloca 1 se a palavra existe no gosto da pessoa/evento, e 0 se não existe.
    vetor_u = [1 if tag in set_user else 0 for tag in todas_tags]
    vetor_e = [1 if tag in set_evento else 0 for tag in todas_tags]
    
    # 5. Cálculo dos Matches: soma +1 toda vez que o vetor do usuário for igual ao do evento
    # Conforme solicitado: int(u == e) -> soma -> divide pelo tamanho
    soma_matches = sum(int(u == e) for u, e in zip(vetor_u, vetor_e))
    
    # 6. A Similaridade final é a soma dividida pelo tamanho do vetor
    # O resultado é um número de 0.0 a 1.0
    similaridade = soma_matches / len(todas_tags)
    
    return similaridade

def recomendar_eventos(usuario_id):
    """
    SISTEMA DE RECOMENDAÇÃO HÍBRIDO (CONTEÚDO + REDE SOCIAL)
    Esta função varre o banco de dados e cria o ranking personalizado para o usuário atual.
    MIGRADO: usa funções do db_supabase.py em vez de sqlite3 direto.
    """
    # A. Busca os gostos musicais do usuário no Banco de Dados
    user = get_usuario_by_id(usuario_id)
    if not user:
        return []
        
    tags_user = user.get('tags') or ''
    
    # B. Busca todos os eventos cadastrados
    eventos = get_todos_eventos()
    
    # C. Busca os amigos que o usuário segue para ver a "prova social"
    amigos_ids = get_seguindo_ids(usuario_id)
    
    recomendacoes = []
    
    # Loop: Analisa cada evento individualmente para dar uma nota
    for ev in eventos:
        # PASSO 1: O evento bate com o meu gosto musical? (Similaridade de Conteúdo)
        sim_vetor = calcular_similaridade_vetor(tags_user, ev.get('tags'))
        
        # Variável que avisa o Front-end se pelo menos 1 gênero bateu (para mostrar o selo visual)
        is_tag_match = sim_vetor > 0.0
        
        # REGRA ESPECIAL DE NEGÓCIO: Patrocinador Master no Topo
        if ev.get('nome') == 'NA PRAIA FESTIVAL':
            is_tag_match = True
            match_final = 10.0 # Nota absurdamente alta para forçar o primeiro lugar na lista
            peso_social = 0.0
            amigos_confirmados = 0
            
            # Mesmo no topo, vamos contar quantos amigos vão para mostrar na interface
            if amigos_ids:
                amigos_confirmados = contar_presencas_amigos_em_evento(ev['id'], amigos_ids)
        else:
            # PASSO 2: Quantos amigos vão? (Peso de Prova Social Colaborativa)
            peso_social = 0.0
            amigos_confirmados = 0
            if amigos_ids:
                amigos_confirmados = contar_presencas_amigos_em_evento(ev['id'], amigos_ids)
                
                # Cada amigo dá +20% de bônus na nota social (limitado a 1.0 que é 100%)
                peso_social = min(amigos_confirmados * 0.2, 1.0)
            
            # PASSO 3: Cálculo Híbrido Final (A Mágica)
            # A nota final do evento é 70% o gosto musical do usuário + 30% pra onde os amigos estão indo
            match_final = (sim_vetor * 0.7) + (peso_social * 0.3)
        
        # PASSO 4: Formata a nota em Porcentagem (ex: 0.85 vira 85%)
        match_pct = round(match_final * 100)
        
        # Adiciona o evento na lista de resultados
        recomendacoes.append({
            'evento': ev,
            'match': match_pct,
            'is_tag_match': is_tag_match,
            'amigos_confirmados': amigos_confirmados if amigos_ids else 0
        })
        
    # Por fim, ordena a lista colocando a maior nota em 1º lugar, e a menor em último
    recomendacoes.sort(key=lambda x: x['match'], reverse=True)
    
    return recomendacoes

# --- ROTAS ---

@app.route('/')
def home():
    recomendacoes = []
    # MIGRADO: usa get_eventos_recentes() do Supabase
    eventos_recentes = get_eventos_recentes(limit=5)
    
    if 'user' in session and session['user']['id']:
        recomendacoes = recomendar_eventos(session['user']['id'])

    return render_template('index.html', user=session.get('user'), eventos=eventos_recentes, recomendacoes=recomendacoes)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html', user=session.get('user'))

@app.route('/anuncie')
def anuncie():
    return render_template('anuncie.html', user=session.get('user'))
    
@app.route('/historico')
def historico():
    # MIGRADO: usa get_todos_eventos() e limita em Python
    eventos = get_todos_eventos()[:3]
    return render_template('historico.html', user=session.get('user'), eventos=eventos)

# --- ÁREA DO ADMINISTRADOR (CENTRO DE COMANDO) ---
@app.route('/dashboard')
def dashboard():
    if not session.get('user') or session['user']['email'] != 'adm@themove.com':
        flash('Acesso restrito ao administrador!', 'danger')
        return redirect(url_for('login'))

    # MIGRADO: usa funções Supabase
    usuarios_lista = get_todos_usuarios()
    total_u = len(usuarios_lista)
    total_p = get_total_presencas()
    ranking = get_ranking_eventos()

    return render_template('dashboard.html', user=session['user'], usuarios=usuarios_lista, total_u=total_u, total_p=total_p, ranking=ranking)

@app.route('/eventos')
def eventos():
    presencas_db = {}
    
    # Buscar todos os eventos não-bares
    all_events_raw = get_todos_eventos(limit=200)
    all_events = [e for e in all_events_raw if e.get('tipo') != 'bar']
    eventos_patrocinados = [e for e in all_events if e.get('is_sponsored')]
    
    recomendacoes = []
    eventos_favoritos = []
    favoritos_ids = []
    
    is_admin = session.get('user') and session['user']['email'] == 'adm@themove.com'
    user_id = session['user']['id'] if session.get('user') else None
    
    if user_id:
        favoritos_ids = get_favoritos(user_id)
        eventos_favoritos = [e for e in all_events if e['id'] in favoritos_ids]
        
    amigos_ids = []
    if user_id and not is_admin:
        amigos_ids = get_seguindo_ids(user_id)
        amigos_ids.append(user_id)
    
    if user_id:
        user_profile = get_usuario_by_id(user_id)
        
        cache = get_recomendacoes_cache(user_id)
        if cache:
            eventos_dict = {e['id']: e for e in all_events}
            for rec in cache:
                ev = eventos_dict.get(rec['evento_id'])
                if ev:
                    recomendacoes.append({
                        "evento": ev,
                        "score": rec["score"],
                        "justificativa": rec["justificativa"]
                    })
        else:
            amostra_eventos = [e for e in all_events if e.get('is_sponsored')] + all_events[:30]
            amostra_unica = {e['id']: e for e in amostra_eventos}.values()
            
            # Para a apresentação não travar (e focar na lógica do professor), 
            # pulamos a API do Gemini e usamos direto a similaridade de vetor!
            gemini_results = recomendar_por_tags(user_profile, list(amostra_unica))
                
            if gemini_results:
                try:
                    set_recomendacoes_cache(user_id, gemini_results)
                except:
                    pass
                eventos_dict = {e['id']: e for e in all_events}
                for rec in gemini_results:
                    ev = eventos_dict.get(rec['evento_id'])
                    if ev:
                        recomendacoes.append({
                            "evento": ev,
                            "score": rec["score"],
                            "justificativa": rec["justificativa"]
                        })
        
        recomendacoes.sort(key=lambda x: x['score'], reverse=True)
        recomendacoes = [r for r in recomendacoes if r['score'] >= 70][:5]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_events = len(all_events)
    total_pages = math.ceil(total_events / per_page) if total_events > 0 else 1
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    eventos_paginados_bruto = all_events[start_idx:end_idx]
    
    patrocinados_ids = {e['id'] for e in eventos_patrocinados}
    
    if page == 1:
        recomendacoes = [r for r in recomendacoes if r['evento']['id'] not in patrocinados_ids and r['evento']['id'] not in favoritos_ids]
        recomendacoes_ids = {r['evento']['id'] for r in recomendacoes}
    else:
        recomendacoes_ids = set()

    ids_pra_esconder = patrocinados_ids | recomendacoes_ids | set(favoritos_ids)
    eventos_paginados = [e for e in eventos_paginados_bruto if e['id'] not in ids_pra_esconder]

    eventos_visiveis = []
    ids_visiveis = set()
    for lista in [eventos_favoritos, eventos_patrocinados, [r['evento'] for r in recomendacoes], eventos_paginados]:
        for ev in lista:
            if ev['id'] not in ids_visiveis:
                eventos_visiveis.append(ev)
                ids_visiveis.add(ev['id'])

    # Markers para mapa
    markers = []
    for ev in eventos_visiveis:
        lat, lng = obter_coordenadas(ev.get('local', ''))
        markers.append({
            'lat': lat,
            'lng': lng,
            'nome': ev['nome'],
            'local': ev.get('local', ''),
            'data': ev.get('data', ''),
            'sponsored': bool(ev.get('is_sponsored'))
        })
    markers_json = json.dumps(markers)

    # Otimização: Buscar presenças de uma vez só (evita N+1 queries que causam crash de socket no Windows)
    presencas_db = {}
    eventos_ids = [ev['id'] for ev in eventos_visiveis]
    if eventos_ids:
        # Busca presenças em lote
        if is_admin:
            from db_supabase import get_presencas_por_eventos
            presencas_lote = get_presencas_por_eventos(eventos_ids)
        elif user_id:
            from db_supabase import get_presencas_por_eventos_filtrado
            usuarios_filtro = amigos_ids if amigos_ids else [user_id]
            presencas_lote = get_presencas_por_eventos_filtrado(eventos_ids, usuarios_filtro)
        else:
            presencas_lote = {}
            
        for ev_id in eventos_ids:
            presencas_db[ev_id] = presencas_lote.get(ev_id, [])
            
    return render_template('eventos.html', 
                           user=session.get('user'), 
                           recomendacoes=recomendacoes, 
                           eventos=eventos_paginados, 
                           patrocinados=eventos_patrocinados,
                           favoritos=eventos_favoritos,
                           favoritos_ids=favoritos_ids,
                           presencas=presencas_db,
                           markers_json=markers_json,
                           page=page,
                           total_pages=total_pages)

@app.route('/bares')
def bares():
    # Buscar todos os bares
    all_events_raw = get_todos_eventos(limit=200)
    all_bares = [e for e in all_events_raw if e.get('tipo') == 'bar']
    bares_patrocinados = [e for e in all_bares if e.get('is_sponsored')]
    
    recomendacoes = []
    bares_favoritos = []
    favoritos_ids = []
    
    user_id = session['user']['id'] if session.get('user') else None
    is_admin = session.get('user') and session['user'].get('email') == 'adm@themove.com'
    
    if user_id:
        favoritos_ids = get_favoritos(user_id)
        bares_favoritos = [e for e in all_bares if e['id'] in favoritos_ids]
        
        user_profile = get_usuario_by_id(user_id)
        
        amostra_eventos = [e for e in all_bares if e.get('is_sponsored')] + all_bares[:30]
        amostra_unica = {e['id']: e for e in amostra_eventos}.values()
        
        # Para a apresentação não travar, pulamos a API do Gemini
        # e usamos direto a similaridade de vetor rápida!
        gemini_results = recomendar_por_tags(user_profile, list(amostra_unica))
            
        if gemini_results:
            bares_dict = {e['id']: e for e in all_bares}
            for rec in gemini_results:
                ev = bares_dict.get(rec['evento_id'])
                if ev:
                    recomendacoes.append({
                        "evento": ev,
                        "score": rec["score"],
                        "justificativa": rec["justificativa"]
                    })
        
        recomendacoes.sort(key=lambda x: x['score'], reverse=True)
        # Mostrar bares se tiver score razoável (>= 50 para garantir que apareça algo)
        recomendacoes = [r for r in recomendacoes if r['score'] >= 50][:5]

    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_bares = len(all_bares)
    total_pages = math.ceil(total_bares / per_page) if total_bares > 0 else 1
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    bares_paginados_bruto = all_bares[start_idx:end_idx]
    
    patrocinados_ids = {e['id'] for e in bares_patrocinados}
    
    if page == 1:
        recomendacoes = [r for r in recomendacoes if r['evento']['id'] not in patrocinados_ids and r['evento']['id'] not in favoritos_ids]
        recomendacoes_ids = {r['evento']['id'] for r in recomendacoes}
    else:
        recomendacoes_ids = set()

    ids_pra_esconder = patrocinados_ids | recomendacoes_ids | set(favoritos_ids)
    bares_paginados = [e for e in bares_paginados_bruto if e['id'] not in ids_pra_esconder]

    bares_visiveis = []
    ids_visiveis = set()
    for lista in [bares_favoritos, bares_patrocinados, [r['evento'] for r in recomendacoes], bares_paginados]:
        for ev in lista:
            if ev['id'] not in ids_visiveis:
                bares_visiveis.append(ev)
                ids_visiveis.add(ev['id'])

    # Markers para mapa
    markers = []
    for ev in bares_visiveis:
        lat, lng = obter_coordenadas(ev.get('local', ''))
        markers.append({
            'lat': lat,
            'lng': lng,
            'nome': ev['nome'],
            'local': ev.get('local', ''),
            'data': ev.get('data', ''),
            'sponsored': bool(ev.get('is_sponsored'))
        })
    markers_json = json.dumps(markers)

    presencas_db = {}
    bares_ids = [ev['id'] for ev in bares_visiveis]
    if bares_ids:
        if is_admin:
            from db_supabase import get_presencas_por_eventos
            presencas_lote = get_presencas_por_eventos(bares_ids)
        elif user_id:
            from db_supabase import get_presencas_por_eventos_filtrado
            # Nos bares, os alunos só veem presenças SE for de amigos
            amigos_ids = get_seguindo_ids(user_id) if not is_admin else []
            usuarios_filtro = amigos_ids if amigos_ids else [user_id]
            presencas_lote = get_presencas_por_eventos_filtrado(bares_ids, usuarios_filtro)
        else:
            presencas_lote = {}
            
        for ev_id in bares_ids:
            presencas_db[ev_id] = presencas_lote.get(ev_id, [])

    return render_template('bares.html', 
                           user=session.get('user'), 
                           recomendacoes=recomendacoes, 
                           bares=bares_paginados, 
                           patrocinados=bares_patrocinados,
                           favoritos=bares_favoritos,
                           favoritos_ids=favoritos_ids,
                           presencas=presencas_db,
                           markers_json=markers_json,
                           page=page,
                           total_pages=total_pages)

@app.route('/confirmar/<int:evento_id>')
def confirmar_presenca(evento_id):
    if 'user' not in session:
        flash('Faça login para marcar presença!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user']['id']
    data_presenca = request.args.get('data')
    
    existente = get_presenca(user_id, evento_id, data_presenca)
    if not existente:
        insert_presenca(user_id, evento_id, data_presenca)
    return redirect(request.referrer or url_for('eventos'))

@app.route('/remover/<int:evento_id>')
def remover_presenca(evento_id):
    if 'user' in session:
        user_id = session['user']['id']
        data_presenca = request.args.get('data')
        delete_presenca(user_id, evento_id, data_presenca)
    return redirect(request.referrer or url_for('eventos'))

@app.route('/favoritar/<int:evento_id>', methods=['POST'])
def favoritar(evento_id):
    if 'user' not in session:
        return {'success': False, 'error': 'Não logado'}, 401
    user_id = session['user']['id']
    add_favorito(user_id, evento_id)
    return {'success': True}

@app.route('/desfavoritar/<int:evento_id>', methods=['POST'])
def desfavoritar(evento_id):
    if 'user' in session:
        user_id = session['user']['id']
        remove_favorito(user_id, evento_id)
        return {'success': True}
    return {'success': False, 'error': 'Não logado'}, 401

@app.route('/agente_chat', methods=['POST'])
def agente_chat():
    from gemini_recommender import chat_agente_the_move
    data = request.json
    mensagem = data.get('mensagem', '')
    
    if not mensagem:
        return {'resposta': 'Fala comigo, qual é a boa?'}
        
    all_events = get_todos_eventos(limit=200)
    resposta = chat_agente_the_move(mensagem, all_events)
    
    return {'resposta': resposta}

@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user']['id']
    nome = request.form.get('nome')
    username = request.form.get('username')
    bio = request.form.get('bio')
    
    if not username.startswith('@'):
        username = '@' + username
        
    # MIGRADO: usa username_em_uso() e update_usuario_perfil() do Supabase
    if username_em_uso(username, user_id):
        flash('Este @username já está em uso por outra pessoa.', 'danger')
        return redirect(url_for('perfil', username=session['user']['username']))
        
    update_usuario_perfil(user_id, nome, username, bio)
    
    session['user']['nome'] = nome
    session['user']['username'] = username
        
    flash('Perfil atualizado com sucesso!', 'success')
    return redirect(url_for('perfil', username=username))

@app.route('/amigos')
def amigos():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user']['id']
    # MIGRADO: usa get_seguindo() e get_sugestoes_usuarios() do Supabase
    seguindo = get_seguindo(user_id)
    
    seguindo_ids = [r['id'] for r in seguindo]
    seguindo_ids.append(user_id)
    
    sugestoes = get_sugestoes_usuarios(excluir_ids=seguindo_ids)
        
    return render_template('amigos.html', user=session['user'], seguindo=seguindo, sugestoes=sugestoes)

@app.route('/perfil/<username>')
def perfil(username):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    # MIGRADO: usa get_usuario_by_username(), count_seguidores(), is_seguindo(), get_presencas_de_usuario()
    perfil_user = get_usuario_by_username(username)
    if not perfil_user:
        return "Perfil não encontrado", 404
        
    seguidores = count_seguidores(perfil_user['id'])
    seguindo_count = count_seguindo(perfil_user['id'])
    
    is_following = False
    if session['user']['id'] != perfil_user['id']:
        is_following = is_seguindo(session['user']['id'], perfil_user['id'])
            
    # Mostrar eventos confirmados apenas se o perfil for aberto para o usuário
    # ou seja, se for amigo/seguindo, se for ele mesmo, ou admin
    is_admin = session['user']['email'] == 'adm@themove.com'
    show_events = is_following or session['user']['id'] == perfil_user['id'] or is_admin
    
    eventos_confirmados = []
    if show_events:
        # Não mostrar bares (sigilosos) a menos que seja ele mesmo ou admin
        excluir_bar = not is_admin and session['user']['id'] != perfil_user['id']
        eventos_confirmados = get_presencas_de_usuario(perfil_user['id'], excluir_bar=excluir_bar)
            
    return render_template('perfil.html', user=session['user'], perfil=perfil_user, 
                           seguidores=seguidores, seguindo=seguindo_count, 
                           is_following=is_following, eventos=eventos_confirmados,
                           show_events=show_events)

@app.route('/seguir/<int:user_id>')
def seguir(user_id):
    if 'user' in session:
        meu_id = session['user']['id']
        # MIGRADO: usa insert_seguidor() do Supabase
        insert_seguidor(meu_id, user_id)
    return redirect(request.referrer or url_for('home'))

@app.route('/deixar_seguir/<int:user_id>')
def deixar_seguir(user_id):
    if 'user' in session:
        meu_id = session['user']['id']
        # MIGRADO: usa delete_seguidor() do Supabase
        delete_seguidor(meu_id, user_id)
    return redirect(request.referrer or url_for('home'))

@app.route('/busca')
def busca():
    q = request.args.get('q', '')
    usuarios = []
    if q and 'user' in session:
        # MIGRADO: usa buscar_usuarios() do Supabase
        usuarios = buscar_usuarios(q)
    return render_template('busca.html', user=session.get('user'), usuarios=usuarios, query=q)

@app.route('/criar_evento', methods=['GET', 'POST'])
def criar_evento():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        nome = request.form.get('nome')
        local = request.form.get('local')
        data = request.form.get('data')
        tipo = request.form.get('tipo')
        tags = request.form.get('tags')
        
        # MIGRADO: usa insert_evento() do Supabase
        insert_evento(
            nome=nome,
            local=local,
            data=data,
            tipo=tipo,
            tags=tags,
            criador_id=session['user']['id'],
            imagem='meskla.jpg',
            link='#'
        )
        flash('Evento criado com sucesso e submetido ao Contrato de Monetização!', 'success')
        return redirect(url_for('home'))
        
    return render_template('criar_evento.html', user=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        # MIGRADO: usa get_usuario_by_email_senha() do Supabase
        user_db = get_usuario_by_email_senha(email, senha)
        if user_db:
            session['user'] = {
                'id': user_db['id'],
                'nome': user_db['nome'], 
                'username': user_db['username'],
                'email': user_db['email'], 
                'is_admin': user_db['username'] == '@themove'
            }
            
            # Se não tem tags e não é admin, vai pro onboarding
            if not user_db.get('tags') and user_db['username'] != '@themove':
                return redirect(url_for('onboarding'))
                
            if session['user']['is_admin']:
                return redirect(url_for('dashboard'))
            return redirect(url_for('home'))

        flash('E-mail ou Senha incorretos!', 'danger')
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        nasc = request.form.get('nascimento')
        username = request.form.get('username')
        
        # garantir que @ está no username
        if not username.startswith('@'):
            username = '@' + username

        try:
            # MIGRADO: usa insert_usuario() do Supabase
            insert_usuario(nome, email, senha, nasc, username)
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
    return render_template('cadastrar.html')

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        tags = request.form.getlist('tags')
        regioes = request.form.getlist('regioes')
        tags_str = ','.join(tags)
        regioes_str = ','.join(regioes)
        
        update_usuario_preferencias(session['user']['id'], tags_str, '', regioes_str, '', '')
            
        return redirect(url_for('home'))
        
    return render_template('onboarding.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)