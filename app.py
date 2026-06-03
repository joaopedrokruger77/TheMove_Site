import math
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'the_move_2026_pro_key'

def get_db():
    conn = sqlite3.connect('themove.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT NOT NULL, 
            email TEXT UNIQUE NOT NULL, 
            senha TEXT NOT NULL, 
            nascimento TEXT,
            username TEXT UNIQUE NOT NULL,
            foto TEXT,
            bio TEXT,
            tags TEXT
        )''')
        
        db.execute('''CREATE TABLE IF NOT EXISTS seguidores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seguidor_id INTEGER,
            seguido_id INTEGER,
            FOREIGN KEY(seguidor_id) REFERENCES usuarios(id),
            FOREIGN KEY(seguido_id) REFERENCES usuarios(id)
        )''')
        
        db.execute('''CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            local TEXT,
            data TEXT,
            imagem TEXT,
            tipo TEXT,
            link TEXT,
            tags TEXT,
            criador_id INTEGER,
            FOREIGN KEY(criador_id) REFERENCES usuarios(id)
        )''')

        db.execute('''CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            usuario_id INTEGER, 
            evento_id INTEGER,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY(evento_id) REFERENCES eventos(id)
        )''')
        
        
        # Super Admin Seed apenas se não existir
        admin = db.execute("SELECT id FROM usuarios WHERE username = '@themove'").fetchone()
        if not admin:
            db.execute('''INSERT INTO usuarios (nome, email, senha, nascimento, username, tags) 
                          VALUES (?, ?, ?, ?, ?, ?)''', 
                       ('the move', 'adm@themove.com', 'themove10neymar@', '2026-01-01', '@themove', 'Admin,Todos'))
        
        # Seed Inicial de Eventos foi movido para seed_db.py
        db.commit()

init_db()

# --- Módulo de IA (Recomendação Híbrida) ---
def calcular_similaridade_cosseno(tags_user, tags_evento):
    """
    SISTEMA DE RECOMENDAÇÃO: CÁLCULO DE SIMILARIDADE
    Esta função é o "cérebro" matemático do protótipo. Ela calcula a Similaridade de Cosseno
    entre o que o usuário gosta (tags do usuário) e o que o evento oferece (tags do evento).
    """
    # 1. Se o usuário ou o evento não tiverem tags, a similaridade é zero.
    if not tags_user or not tags_evento:
        return 0.0
        
    # 2. Transforma as palavras em listas únicas (sets) para remover duplicadas e padronizar em letras minúsculas
    set_user = set(tags_user.lower().split(','))
    set_evento = set(tags_evento.lower().split(','))
    
    # 3. Une todas as palavras (tags) possíveis em um único grupo (o "universo" de palavras)
    todas_tags = set_user.union(set_evento)
    
    # 4. Cria vetores (listas de 0 ou 1). 
    # Coloca 1 se a palavra existe no gosto da pessoa/evento, e 0 se não existe.
    vetor_u = [1 if tag in set_user else 0 for tag in todas_tags]
    vetor_e = [1 if tag in set_evento else 0 for tag in todas_tags]
    
    # 5. Cálculo do Produto Escalar (multiplica e soma os itens dos vetores que batem)
    produto_escalar = sum(u * e for u, e in zip(vetor_u, vetor_e))
    
    # 6. Cálculo das Magnitudes (o tamanho geométrico de cada vetor no espaço)
    mag_u = math.sqrt(sum(u**2 for u in vetor_u))
    mag_e = math.sqrt(sum(e**2 for e in vetor_e))
    
    # Previne divisão por zero (erro matemático)
    if mag_u == 0 or mag_e == 0:
        return 0.0
        
    # 7. A Similaridade final é o produto escalar dividido pela multiplicação das magnitudes
    # O resultado é um número de 0.0 a 1.0 (onde 1.0 é um "Match Perfeito")
    return produto_escalar / (mag_u * mag_e)

def recomendar_eventos(usuario_id):
    """
    SISTEMA DE RECOMENDAÇÃO HÍBRIDO (CONTEÚDO + REDE SOCIAL)
    Esta função varre o banco de dados e cria o ranking personalizado para o usuário atual.
    """
    with get_db() as db:
        # A. Busca os gostos musicais do usuário no Banco de Dados
        user = db.execute("SELECT tags FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        if not user:
            return []
            
        tags_user = user['tags'] if user['tags'] else ''
        
        # B. Busca todos os eventos cadastrados
        eventos = db.execute("SELECT * FROM eventos").fetchall()
        
        # C. Busca os amigos que o usuário segue para ver a "prova social"
        amigos_rows = db.execute("SELECT seguido_id FROM seguidores WHERE seguidor_id = ?", (usuario_id,)).fetchall()
        amigos_ids = [r['seguido_id'] for r in amigos_rows]
        
        recomendacoes = []
        
        # Loop: Analisa cada evento individualmente para dar uma nota
        for ev in eventos:
            # PASSO 1: O evento bate com o meu gosto musical? (Similaridade de Conteúdo)
            sim_cosseno = calcular_similaridade_cosseno(tags_user, ev['tags'])
            
            # Variável que avisa o Front-end se pelo menos 1 gênero bateu (para mostrar o selo visual)
            is_tag_match = sim_cosseno > 0.0
            
            # REGRA ESPECIAL DE NEGÓCIO: Patrocinador Master no Topo
            if ev['nome'] == 'NA PRAIA FESTIVAL':
                is_tag_match = True
                match_final = 10.0 # Nota absurdamente alta para forçar o primeiro lugar na lista
                peso_social = 0.0
                amigos_confirmados = 0
                
                # Mesmo no topo, vamos contar quantos amigos vão para mostrar na interface
                if amigos_ids:
                    placeholders = ','.join('?' for _ in amigos_ids)
                    query = f"SELECT COUNT(*) as qtd FROM presencas WHERE evento_id = ? AND usuario_id IN ({placeholders})"
                    amigos_confirmados = db.execute(query, [ev['id']] + amigos_ids).fetchone()['qtd']
            else:
                # PASSO 2: Quantos amigos vão? (Peso de Prova Social Colaborativa)
                peso_social = 0.0
                amigos_confirmados = 0
                if amigos_ids:
                    placeholders = ','.join('?' for _ in amigos_ids)
                    query = f"SELECT COUNT(*) as qtd FROM presencas WHERE evento_id = ? AND usuario_id IN ({placeholders})"
                    amigos_confirmados = db.execute(query, [ev['id']] + amigos_ids).fetchone()['qtd']
                    
                    # Cada amigo dá +20% de bônus na nota social (limitado a 1.0 que é 100%)
                    peso_social = min(amigos_confirmados * 0.2, 1.0)
                
                # PASSO 3: Cálculo Híbrido Final (A Mágica)
                # A nota final do evento é 70% o gosto musical do usuário + 30% pra onde os amigos estão indo
                match_final = (sim_cosseno * 0.7) + (peso_social * 0.3)
            
            # PASSO 4: Formata a nota em Porcentagem (ex: 0.85 vira 85%)
            match_pct = round(match_final * 100)
            
            # Adiciona o evento na lista de resultados
            recomendacoes.append({
                'evento': dict(ev),
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
    with get_db() as db:
        eventos_recentes = db.execute("SELECT * FROM eventos ORDER BY id DESC LIMIT 5").fetchall()
        
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
    with get_db() as db:
        # Apenas exemplo de filtro, pegando eventos aleatórios
        eventos = db.execute("SELECT * FROM eventos LIMIT 3").fetchall()
    return render_template('historico.html', user=session.get('user'), eventos=eventos)

# --- ÁREA DO ADMINISTRADOR (CENTRO DE COMANDO) ---
@app.route('/dashboard')
def dashboard():
    if not session.get('user') or session['user']['email'] != 'adm@themove.com':
        flash('Acesso restrito ao administrador!', 'danger')
        return redirect(url_for('login'))

    with get_db() as db:
        usuarios_lista = db.execute("SELECT * FROM usuarios").fetchall()
        total_u = len(usuarios_lista)
        total_p = db.execute("SELECT COUNT(*) as total FROM presencas").fetchone()['total']
        
        # Ranking com acesso irrestrito a todos
        ranking = db.execute('''
            SELECT e.nome, COUNT(p.id) as qtd 
            FROM presencas p 
            JOIN eventos e ON p.evento_id = e.id 
            GROUP BY p.evento_id ORDER BY qtd DESC
        ''').fetchall()

    return render_template('dashboard.html', user=session['user'], usuarios=usuarios_lista, total_u=total_u, total_p=total_p, ranking=ranking)

@app.route('/eventos')
def eventos():
    presencas_db = {}
    with get_db() as db:
        all_events = db.execute("SELECT * FROM eventos").fetchall()
        
        recomendacoes = []
        eventos_gerais = []
        # Filtro de privacidade: só pega quem o usuario segue, a nao ser que seja admin
        is_admin = session.get('user') and session['user']['email'] == 'adm@themove.com'
        user_id = session['user']['id'] if session.get('user') else None
        
        if user_id and not is_admin:
            amigos_rows = db.execute("SELECT seguido_id FROM seguidores WHERE seguidor_id = ?", (user_id,)).fetchall()
            amigos_ids = [r['seguido_id'] for r in amigos_rows]
            # Inclui ele mesmo
            amigos_ids.append(user_id)
        
        if user_id:
            recomendacoes = recomendar_eventos(user_id)
        else:
            eventos_gerais = all_events
            
        for ev in all_events:
            if is_admin:
                rows = db.execute('''
                    SELECT u.nome, u.username, u.foto 
                    FROM presencas p 
                    JOIN usuarios u ON p.usuario_id = u.id 
                    WHERE p.evento_id = ?
                ''', (ev['id'],)).fetchall()
                presencas_db[ev['id']] = rows
            elif user_id and ev['tipo'] != 'bar': 
                # Presença em 'bar' é secreta (só admin vê), 'show' os amigos veem
                if amigos_ids:
                    placeholders = ','.join('?' for _ in amigos_ids)
                    query = f'''
                        SELECT u.nome, u.username, u.foto 
                        FROM presencas p 
                        JOIN usuarios u ON p.usuario_id = u.id 
                        WHERE p.evento_id = ? AND p.usuario_id IN ({placeholders})
                    '''
                    rows = db.execute(query, [ev['id']] + amigos_ids).fetchall()
                    presencas_db[ev['id']] = rows
                else:
                    # Se não tem amigos (só ele mesmo), checa só ele
                    rows = db.execute('''
                        SELECT u.nome, u.username, u.foto 
                        FROM presencas p 
                        JOIN usuarios u ON p.usuario_id = u.id 
                        WHERE p.evento_id = ? AND p.usuario_id = ?
                    ''', (ev['id'], user_id)).fetchall()
                    presencas_db[ev['id']] = rows
            else:
                presencas_db[ev['id']] = []
                
    return render_template('eventos.html', user=session.get('user'), recomendacoes=recomendacoes, eventos=eventos_gerais, presencas=presencas_db)

@app.route('/confirmar/<int:evento_id>')
def confirmar_presenca(evento_id):
    if 'user' not in session:
        flash('Faça login para marcar presença!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user']['id']
    with get_db() as db:
        existente = db.execute("SELECT id FROM presencas WHERE usuario_id = ? AND evento_id = ?", (user_id, evento_id)).fetchone()
        if not existente:
            db.execute("INSERT INTO presencas (usuario_id, evento_id) VALUES (?, ?)", (user_id, evento_id))
            db.commit()
    return redirect(url_for('eventos'))

@app.route('/remover/<int:evento_id>')
def remover_presenca(evento_id):
    if 'user' in session:
        user_id = session['user']['id']
        with get_db() as db:
            db.execute("DELETE FROM presencas WHERE usuario_id = ? AND evento_id = ?", (user_id, evento_id))
            db.commit()
    return redirect(url_for('eventos'))

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
        
    with get_db() as db:
        existing = db.execute("SELECT id FROM usuarios WHERE username = ? AND id != ?", (username, user_id)).fetchone()
        if existing:
            flash('Este @username já está em uso por outra pessoa.', 'danger')
            return redirect(url_for('perfil', username=session['user']['username']))
            
        db.execute("UPDATE usuarios SET nome = ?, username = ?, bio = ? WHERE id = ?", (nome, username, bio, user_id))
        db.commit()
        
        session['user']['nome'] = nome
        session['user']['username'] = username
        
    flash('Perfil atualizado com sucesso!', 'success')
    return redirect(url_for('perfil', username=username))

@app.route('/amigos')
def amigos():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user']['id']
    with get_db() as db:
        seguindo = db.execute('''
            SELECT u.* FROM seguidores s
            JOIN usuarios u ON s.seguido_id = u.id
            WHERE s.seguidor_id = ?
        ''', (user_id,)).fetchall()
        
        seguindo_ids = [r['id'] for r in seguindo]
        seguindo_ids.append(user_id)
        
        placeholders = ','.join('?' for _ in seguindo_ids)
        query_sugestoes = f'''
            SELECT * FROM usuarios 
            WHERE id NOT IN ({placeholders}) AND username != '@themove'
            LIMIT 10
        '''
        sugestoes = db.execute(query_sugestoes, seguindo_ids).fetchall()
        
    return render_template('amigos.html', user=session['user'], seguindo=seguindo, sugestoes=sugestoes)

@app.route('/perfil/<username>')
def perfil(username):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    with get_db() as db:
        perfil_user = db.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
        if not perfil_user:
            return "Perfil não encontrado", 404
            
        seguidores = db.execute("SELECT COUNT(*) as qtd FROM seguidores WHERE seguido_id = ?", (perfil_user['id'],)).fetchone()['qtd']
        seguindo = db.execute("SELECT COUNT(*) as qtd FROM seguidores WHERE seguidor_id = ?", (perfil_user['id'],)).fetchone()['qtd']
        
        is_following = False
        if session['user']['id'] != perfil_user['id']:
            check_follow = db.execute("SELECT id FROM seguidores WHERE seguidor_id = ? AND seguido_id = ?", 
                                      (session['user']['id'], perfil_user['id'])).fetchone()
            if check_follow:
                is_following = True
                
        # Mostrar eventos confirmados apenas se o perfil for aberto para o usuário
        # ou seja, se for amigo/seguindo, se for ele mesmo, ou admin
        is_admin = session['user']['email'] == 'adm@themove.com'
        show_events = is_following or session['user']['id'] == perfil_user['id'] or is_admin
        
        eventos_confirmados = []
        if show_events:
            # Não mostrar bares (sigilosos) a menos que seja ele mesmo ou admin
            condicao_extra = ""
            if not is_admin and session['user']['id'] != perfil_user['id']:
                condicao_extra = " AND e.tipo != 'bar'"
                
            query = f'''
                SELECT e.* 
                FROM presencas p 
                JOIN eventos e ON p.evento_id = e.id 
                WHERE p.usuario_id = ? {condicao_extra}
            '''
            eventos_confirmados = db.execute(query, (perfil_user['id'],)).fetchall()
            
    return render_template('perfil.html', user=session['user'], perfil=perfil_user, 
                           seguidores=seguidores, seguindo=seguindo, 
                           is_following=is_following, eventos=eventos_confirmados,
                           show_events=show_events)

@app.route('/seguir/<int:user_id>')
def seguir(user_id):
    if 'user' in session:
        meu_id = session['user']['id']
        with get_db() as db:
            db.execute("INSERT INTO seguidores (seguidor_id, seguido_id) VALUES (?, ?)", (meu_id, user_id))
            db.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/deixar_seguir/<int:user_id>')
def deixar_seguir(user_id):
    if 'user' in session:
        meu_id = session['user']['id']
        with get_db() as db:
            db.execute("DELETE FROM seguidores WHERE seguidor_id = ? AND seguido_id = ?", (meu_id, user_id))
            db.commit()
    return redirect(request.referrer or url_for('home'))

@app.route('/busca')
def busca():
    q = request.args.get('q', '')
    usuarios = []
    if q and 'user' in session:
        with get_db() as db:
            q_like = f"%{q}%"
            usuarios = db.execute("SELECT * FROM usuarios WHERE username LIKE ? OR nome LIKE ?", (q_like, q_like)).fetchall()
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
        
        with get_db() as db:
            db.execute('''INSERT INTO eventos (nome, local, data, tipo, tags, criador_id, imagem, link) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (nome, local, data, tipo, tags, session['user']['id'], 'meskla.jpg', '#'))
            db.commit()
        flash('Evento criado com sucesso e submetido ao Contrato de Monetização!', 'success')
        return redirect(url_for('home'))
        
    return render_template('criar_evento.html', user=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        with get_db() as db:
            user_db = db.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha)).fetchone()
            if user_db:
                session['user'] = {
                    'id': user_db['id'],
                    'nome': user_db['nome'], 
                    'username': user_db['username'],
                    'email': user_db['email'], 
                    'is_admin': user_db['username'] == '@themove'
                }
                
                # Se não tem tags e não é admin, vai pro onboarding
                if not user_db['tags'] and user_db['username'] != '@themove':
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
            with get_db() as db:
                db.execute("INSERT INTO usuarios (nome, email, senha, nascimento, username) VALUES (?, ?, ?, ?, ?)",
                           (nome, email, senha, nasc, username))
                db.commit()
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
    return render_template('cadastrar.html')

@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        # Receber as tags selecionadas (checkboxes com name='tags')
        tags = request.form.getlist('tags')
        tags_str = ','.join(tags)
        
        with get_db() as db:
            db.execute("UPDATE usuarios SET tags = ? WHERE id = ?", (tags_str, session['user']['id']))
            db.commit()
            
        return redirect(url_for('home'))
        
    return render_template('onboarding.html', user=session['user'])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)