# =================================================================
# seed_supabase.py — Seed de Eventos no Supabase
# Equivalente ao seed_db.py, mas usando a API do Supabase.
#
# Execute: python seed_supabase.py
# Isso irá:
#   1. Limpar todas as presenças e eventos existentes
#   2. Reinserir os eventos padrão do The Move
# =================================================================

from supabase_client import supabase


def reset_eventos():
    print("Conectando ao Supabase...")

    try:
        # 1. Limpar presenças e eventos (ordem importa por causa das FKs)
        print("Limpando presenças e eventos existentes...")
        supabase.table("presencas").delete().neq("id", 0).execute()
        supabase.table("eventos").delete().neq("id", 0).execute()

        # 2. Buscar o ID do admin (@themove)
        admin_resp = supabase.table("usuarios") \
            .select("id") \
            .eq("username", "@themove") \
            .limit(1) \
            .execute()

        if not admin_resp.data:
            print("ERRO: Admin @themove não encontrado. Execute o SQL do supabase_schema.sql primeiro.")
            return

        criador_id = admin_resp.data[0]["id"]

        # 3. Inserir eventos padrão
        print("Inserindo eventos...")
        eventos = [
            {
                "nome": "NA PRAIA FESTIVAL",
                "local": "Setor de Clubes",
                "data": "Junho a Setembro/2026",
                "imagem": "napraia.jpg",
                "tipo": "show",
                "link": "https://napraiafestival.r2.com.vc",
                "tags": "multi-eclético",
                "criador_id": criador_id,
            },
            {
                "nome": "CAJU LIMÃO",
                "local": "Setor de Clubes S.",
                "data": "Sábados",
                "imagem": "caju.jpg",
                "tipo": "bar",
                "link": "https://www.instagram.com/botecocajulimao/",
                "tags": "bar, eclético",
                "criador_id": criador_id,
            },
            {
                "nome": "CONTEXTO BAR",
                "local": "408 Sul",
                "data": "Sexta e Sábado",
                "imagem": "contexto.jpg",
                "tipo": "bar",
                "link": "https://www.instagram.com/contextobar/",
                "tags": "bar, pagode",
                "criador_id": criador_id,
            },
            {
                "nome": "DEBOCHE BAR",
                "local": "Asa Norte (201)",
                "data": "Terça a Domingo",
                "imagem": "deboche.jpg",
                "tipo": "bar",
                "link": "https://www.instagram.com/deboche_bar/",
                "tags": "bar",
                "criador_id": criador_id,
            },
            {
                "nome": "PRIMO POBRE",
                "local": "Asa Norte (203)",
                "data": "Quarta a Domingo",
                "imagem": "primo.jpg",
                "tipo": "bar",
                "link": "#",
                "tags": "bar, pagode",
                "criador_id": criador_id,
            },
            {
                "nome": "QUINTA MARCHA",
                "local": "Contexto Bar",
                "data": "Toda quinta-feira",
                "imagem": "contexto.jpg",
                "tipo": "festa",
                "link": "#",
                "tags": "funk, forró",
                "criador_id": criador_id,
            },
            {
                "nome": "TURNÊ LUAN SANTANA",
                "local": "Arena BRB",
                "data": "10/10/2026",
                "imagem": "",
                "tipo": "show",
                "link": "#",
                "tags": "sertanejo",
                "criador_id": criador_id,
            },
            {
                "nome": "TURNÊ HENRIQUE E JULIANO",
                "local": "Arena BRB",
                "data": "12/09/2026",
                "imagem": "",
                "tipo": "show",
                "link": "#",
                "tags": "sertanejo",
                "criador_id": criador_id,
            },
            {
                "nome": "DOMINGUINHO",
                "local": "Arena BRB",
                "data": "23/01/2027",
                "imagem": "",
                "tipo": "show",
                "link": "#",
                "tags": "forró, mpb",
                "criador_id": criador_id,
            },
        ]

        supabase.table("eventos").insert(eventos).execute()
        print(f"✅ {len(eventos)} eventos inseridos com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao executar seed: {e}")
        raise


if __name__ == "__main__":
    reset_eventos()
