import sqlite3
import os

DB_NAME = 'themove.db'

def reset_eventos():
    print("Conectando ao banco de dados...")
    if not os.path.exists(DB_NAME):
        print(f"Erro: O banco {DB_NAME} não existe. Execute o app.py primeiro para criar as tabelas.")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    db = conn.cursor()

    try:
        # 1. Limpar tabela de eventos
        print("Limpando a tabela de eventos e presenças atuais...")
        db.execute("DELETE FROM presencas")
        db.execute("DELETE FROM eventos")
        
        # Obter o id do admin (The Move)
        admin = db.execute("SELECT id FROM usuarios WHERE username = '@themove'").fetchone()
        criador_id = admin['id'] if admin else 1

        print("Inserindo Bares e Eventos...")
        eventos = [
            ('NA PRAIA FESTIVAL', 'Setor de Clubes', 'Junho a Setembro/2026', 'napraia.jpg', 'show', 'https://napraiafestival.r2.com.vc', 'multi-eclético'),
            ('CAJU LIMÃO', 'Setor de Clubes S.', 'Sábados', 'caju.jpg', 'bar', 'https://www.instagram.com/botecocajulimao/', 'bar, eclético'),
            ('CONTEXTO BAR', '408 Sul', 'Sexta e Sábado', 'contexto.jpg', 'bar', 'https://www.instagram.com/contextobar/', 'bar, pagode'),
            ('DEBOCHE BAR', 'Asa Norte (201)', 'Terça a Domingo', 'deboche.jpg', 'bar', 'https://www.instagram.com/deboche_bar/', 'bar'),
            ('PRIMO POBRE', 'Asa Norte (203)', 'Quarta a Domingo', 'primo.jpg', 'bar', '#', 'bar, pagode'),
            ('QUINTA MARCHA', 'Contexto Bar', 'Toda quinta-feira', 'contexto.jpg', 'festa', '#', 'funk, forró'),
            ('TURNÊ LUAN SANTANA', 'Arena BRB', '10/10/2026', '', 'show', '#', 'sertanejo'),
            ('TURNÊ HENRIQUE E JULIANO', 'Arena BRB', '12/09/2026', '', 'show', '#', 'sertanejo'),
            ('DOMINGUINHO', 'Arena BRB', '23/01/2027', '', 'show', '#', 'forró, mpb')
        ]

        for ev in eventos:
            db.execute('''INSERT INTO eventos (nome, local, data, imagem, tipo, link, tags, criador_id) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (ev[0], ev[1], ev[2], ev[3], ev[4], ev[5], ev[6], criador_id))

        conn.commit()
        print("Seed concluído com sucesso!")

    except Exception as e:
        print(f"Erro ao executar seed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    reset_eventos()
