from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'the_move_2026_pro_key'


def get_db():
    conn = sqlite3.connect('themove.db')
    conn.row_factory = sqlite3.Row
    return conn


# Inicialização do Banco de Dados
with get_db() as db:
    db.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT UNIQUE, senha TEXT, nascimento TEXT)''')
    db.execute('''CREATE TABLE IF NOT EXISTS presencas 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_nome TEXT, evento_id TEXT)''')


@app.route('/')
def home():
    return render_template('index.html', user=session.get('user'))


@app.route('/sobre')
def sobre():
    return render_template('sobre.html', user=session.get('user'))


@app.route('/anuncie')
def anuncie():
    return render_template('anuncie.html', user=session.get('user'))


# --- ÁREA DO ADMINISTRADOR (CENTRO DE COMANDO) ---
@app.route('/dashboard')
def dashboard():
    # Segurança: Só deixa entrar se for o seu e-mail de ADM
    if not session.get('user') or session['user']['email'] != 'adm@themove.com':
        flash('Acesso restrito ao administrador!', 'danger')
        return redirect(url_for('login'))

    with get_db() as db:
        usuarios_lista = db.execute("SELECT nome, email, nascimento FROM usuarios").fetchall()
        total_u = len(usuarios_lista)
        total_p = db.execute("SELECT COUNT(*) as total FROM presencas").fetchone()['total']
        ranking = db.execute(
            "SELECT evento_id, COUNT(*) as qtd FROM presencas GROUP BY evento_id ORDER BY qtd DESC").fetchall()

    return render_template('dashboard.html', user=session['user'], usuarios=usuarios_lista, total_u=total_u,
                           total_p=total_p, ranking=ranking)


@app.route('/eventos')
def eventos():
    lista_eventos = [
        {'id': 'MESKLA', 'nome': 'FESTIVAL MESKLA', 'local': 'Arena BRB', 'data': '16 de Maio', 'imagem': 'meskla.jpg',
         'tipo': 'show', 'link': 'https://www.instagram.com/festivalmeskla/'},
        {'id': 'CETA', 'nome': 'CÊ TÁ DOIDO', 'local': 'Brasília', 'data': 'Em Breve', 'imagem': 'ceta.webp',
         'tipo': 'show', 'link': 'https://r2.com.vc/ce-ta-doido/'},
        {'id': 'NAPRAIA', 'nome': 'NA PRAIA FESTIVAL', 'local': 'Setor de Clubes', 'data': 'Julho/2026',
         'imagem': 'napraia.jpg', 'tipo': 'show', 'link': 'https://napraiafestival.r2.com.vc'},
        {'id': 'CONTEXTO', 'nome': 'BAR CONTEXTO', 'local': '408 Sul', 'data': 'Sexta e Sábado',
         'imagem': 'contexto.jpg', 'tipo': 'bar', 'link': 'https://www.instagram.com/contextobar/'},
        {'id': 'DEBOCHE', 'nome': 'DEBOCHE! BAR', 'local': 'Asa Norte (201)', 'data': 'Terça a Domingo',
         'imagem': 'deboche.jpg', 'tipo': 'bar', 'link': 'https://www.instagram.com/deboche_bar/'},
        {'id': 'PRIMO', 'nome': 'PRIMO POBRE', 'local': 'Asa Norte (203)', 'data': 'Quarta a Domingo',
         'imagem': 'primo.jpg', 'tipo': 'bar', 'link': '#'},
        {'id': 'CAJU', 'nome': 'CAJU LIMÃO', 'local': 'Setor de Clubes S.', 'data': 'Sábados', 'imagem': 'caju.jpg',
         'tipo': 'bar', 'link': 'https://www.instagram.com/botecocajulimao/'}
    ]
    presencas_db = {}
    with get_db() as db:
        for ev in lista_eventos:
            rows = db.execute("SELECT usuario_nome FROM presencas WHERE evento_id = ?", (ev['id'],)).fetchall()
            presencas_db[ev['id']] = [row['usuario_nome'] for row in rows]
    return render_template('eventos.html', user=session.get('user'), eventos=lista_eventos, presencas=presencas_db)


# --- ROTAS DE PRESENÇA ---
@app.route('/confirmar/<evento_id>')
def confirmar_presenca(evento_id):
    if 'user' not in session:
        flash('Faça login para marcar presença!', 'danger')
        return redirect(url_for('login'))

    nome_usuario = session['user']['nome']
    with get_db() as db:
        existente = db.execute("SELECT id FROM presencas WHERE usuario_nome = ? AND evento_id = ?",
                               (nome_usuario, evento_id)).fetchone()
        if not existente:
            db.execute("INSERT INTO presencas (usuario_nome, evento_id) VALUES (?, ?)", (nome_usuario, evento_id))
            db.commit()
    return redirect(url_for('eventos'))


@app.route('/remover/<evento_id>')
def remover_presenca(evento_id):
    if 'user' in session:
        nome_usuario = session['user']['nome']
        with get_db() as db:
            db.execute("DELETE FROM presencas WHERE usuario_nome = ? AND evento_id = ?", (nome_usuario, evento_id))
            db.commit()
    return redirect(url_for('eventos'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        # VERIFICAÇÃO DE ADM
        if email == 'adm@themove.com' and senha == 'movebsb2026':
            session['user'] = {'nome': 'JOÃO (CEO)', 'email': email, 'is_admin': True}
            return redirect(url_for('dashboard'))

        # USUÁRIO COMUM
        with get_db() as db:
            user_db = db.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha)).fetchone()
            if user_db:
                session['user'] = {'nome': user_db['nome'], 'email': user_db['email'], 'is_admin': False}
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
        try:
            with get_db() as db:
                db.execute("INSERT INTO usuarios (nome, email, senha, nascimento) VALUES (?, ?, ?, ?)",
                           (nome, email, senha, nasc))
                db.commit()
            return redirect(url_for('login'))
        except:
            flash('Erro ao cadastrar.', 'danger')
    return render_template('cadastrar.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)