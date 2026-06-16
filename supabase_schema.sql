-- =================================================================
-- THE MOVE SITE — Supabase PostgreSQL Schema
-- Equivalente ao banco SQLite themove.db
-- Execute este script no Supabase SQL Editor:
--   https://supabase.com/dashboard/project/ikrhzfdnrodphsjfsmyj/sql
-- =================================================================

-- -----------------------------------------------------------------
-- TABELA: usuarios
-- Armazena todos os usuários cadastrados (admin e comuns)
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id        BIGSERIAL PRIMARY KEY,
    nome      TEXT NOT NULL,
    email     TEXT UNIQUE NOT NULL,
    senha     TEXT NOT NULL,
    nascimento TEXT,
    username  TEXT UNIQUE NOT NULL,
    foto      TEXT,
    bio       TEXT,
    tags      TEXT
);

-- -----------------------------------------------------------------
-- TABELA: seguidores
-- Relacionamento M:N entre usuários (quem segue quem)
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seguidores (
    id          BIGSERIAL PRIMARY KEY,
    seguidor_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    seguido_id  BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------
-- TABELA: eventos
-- Shows, bares e festas cadastrados no sistema
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS eventos (
    id         BIGSERIAL PRIMARY KEY,
    nome       TEXT,
    local      TEXT,
    data       TEXT,
    imagem     TEXT,
    tipo       TEXT,
    link       TEXT,
    tags       TEXT,
    criador_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL
);

-- -----------------------------------------------------------------
-- TABELA: presencas
-- Confirmações de presença de usuários em eventos
-- -----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS presencas (
    id         BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    evento_id  BIGINT NOT NULL REFERENCES eventos(id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------
-- SEED: Super Admin padrão (@themove)
-- Inserido apenas se não existir (ON CONFLICT DO NOTHING)
-- -----------------------------------------------------------------
INSERT INTO usuarios (nome, email, senha, nascimento, username, tags)
VALUES ('the move', 'adm@themove.com', 'themove10neymar@', '2026-01-01', '@themove', 'Admin,Todos')
ON CONFLICT (username) DO NOTHING;

-- -----------------------------------------------------------------
-- SEED: Eventos iniciais (equivalente ao seed_db.py)
-- Executar APÓS o admin já existir no banco
-- -----------------------------------------------------------------
INSERT INTO eventos (nome, local, data, imagem, tipo, link, tags, criador_id)
SELECT
    ev.nome, ev.local, ev.data, ev.imagem, ev.tipo, ev.link, ev.tags,
    (SELECT id FROM usuarios WHERE username = '@themove' LIMIT 1)
FROM (VALUES
    ('NA PRAIA FESTIVAL', 'Setor de Clubes',      'Junho a Setembro/2026', 'napraia.jpg', 'show',  'https://napraiafestival.r2.com.vc',                  'multi-eclético'),
    ('CAJU LIMÃO',        'Setor de Clubes S.',   'Sábados',               'caju.jpg',    'bar',   'https://www.instagram.com/botecocajulimao/',          'bar, eclético'),
    ('CONTEXTO BAR',      '408 Sul',               'Sexta e Sábado',        'contexto.jpg','bar',   'https://www.instagram.com/contextobar/',              'bar, pagode'),
    ('DEBOCHE BAR',       'Asa Norte (201)',        'Terça a Domingo',       'deboche.jpg', 'bar',   'https://www.instagram.com/deboche_bar/',              'bar'),
    ('PRIMO POBRE',       'Asa Norte (203)',        'Quarta a Domingo',      'primo.jpg',   'bar',   '#',                                                   'bar, pagode'),
    ('QUINTA MARCHA',     'Contexto Bar',           'Toda quinta-feira',     'contexto.jpg','festa', '#',                                                   'funk, forró'),
    ('TURNÊ LUAN SANTANA','Arena BRB',              '10/10/2026',            '',            'show',  '#',                                                   'sertanejo'),
    ('TURNÊ HENRIQUE E JULIANO','Arena BRB',        '12/09/2026',            '',            'show',  '#',                                                   'sertanejo'),
    ('DOMINGUINHO',       'Arena BRB',              '23/01/2027',            '',            'show',  '#',                                                   'forró, mpb')
) AS ev(nome, local, data, imagem, tipo, link, tags)
ON CONFLICT DO NOTHING;
