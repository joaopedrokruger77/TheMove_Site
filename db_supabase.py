# =================================================================
# db_supabase.py — Camada de Abstração do Banco de Dados (Supabase)
#
# Este módulo substitui todas as queries SQLite do app.py.
# Cada função mapeia exatamente uma operação que existia no código
# original com sqlite3. O app.py chama estas funções em vez de
# usar sqlite3 diretamente.
#
# As funções retornam:
#   - listas de dicionários (em vez de sqlite3.Row)
#   - dicionários individuais (para um único registro)
#   - None (quando não encontrado)
#   - int / bool (para contagens e verificações)
# =================================================================

from supabase_client import supabase


# -----------------------------------------------------------------
# HELPERS INTERNOS
# -----------------------------------------------------------------

def _single(response) -> dict | None:
    """Retorna o primeiro item de uma resposta Supabase, ou None."""
    data = response.data
    return data[0] if data else None


def _list(response) -> list[dict]:
    """Retorna a lista de itens de uma resposta Supabase."""
    return response.data or []


# =================================================================
# USUÁRIOS
# =================================================================

def get_usuario_by_email_senha(email: str, senha: str) -> dict | None:
    """
    Login: busca usuário por email E senha.
    Equivale a: SELECT * FROM usuarios WHERE email = ? AND senha = ?
    """
    resp = supabase.table("usuarios") \
        .select("*") \
        .eq("email", email) \
        .eq("senha", senha) \
        .limit(1) \
        .execute()
    return _single(resp)


def get_usuario_by_username(username: str) -> dict | None:
    """
    Busca usuário pelo @username.
    Equivale a: SELECT * FROM usuarios WHERE username = ?
    """
    resp = supabase.table("usuarios") \
        .select("*") \
        .eq("username", username) \
        .limit(1) \
        .execute()
    return _single(resp)


def get_usuario_by_id(user_id: int) -> dict | None:
    """
    Busca usuário pelo ID.
    Equivale a: SELECT * FROM usuarios WHERE id = ?
    """
    resp = supabase.table("usuarios") \
        .select("*") \
        .eq("id", user_id) \
        .limit(1) \
        .execute()
    return _single(resp)


def get_todos_usuarios() -> list[dict]:
    """
    Retorna todos os usuários (para o dashboard admin).
    Equivale a: SELECT * FROM usuarios
    """
    resp = supabase.table("usuarios").select("*").execute()
    return _list(resp)


def buscar_usuarios(query: str) -> list[dict]:
    """
    Busca usuários por username OU nome (like).
    Equivale a: SELECT * FROM usuarios WHERE username LIKE ? OR nome LIKE ?
    """
    q = f"%{query}%"
    resp = supabase.table("usuarios") \
        .select("*") \
        .or_(f"username.ilike.{q},nome.ilike.{q}") \
        .execute()
    return _list(resp)


def insert_usuario(nome: str, email: str, senha: str, nascimento: str, username: str) -> dict | None:
    """
    Cadastra um novo usuário.
    Equivale a: INSERT INTO usuarios (nome, email, senha, nascimento, username) VALUES (?, ?, ?, ?, ?)
    Retorna o usuário inserido ou lança exceção em caso de email/username duplicado.
    """
    resp = supabase.table("usuarios").insert({
        "nome": nome,
        "email": email,
        "senha": senha,
        "nascimento": nascimento,
        "username": username,
    }).execute()
    return _single(resp)


def update_usuario_preferencias(user_id: int, tags: str, orcamento: str, regiao: str, tipo_lugar: str, companhia: str) -> None:
    """
    Salva as tags de gosto musical e as novas preferências após o onboarding/edição de perfil.
    """
    supabase.table("usuarios") \
        .update({
            "tags": tags,
            "orcamento": orcamento,
            "regiao": regiao,
            "tipo_lugar": tipo_lugar,
            "companhia": companhia
        }) \
        .eq("id", user_id) \
        .execute()


def update_usuario_perfil(user_id: int, nome: str, username: str, bio: str) -> None:
    """
    Atualiza nome, username e bio do perfil.
    Equivale a: UPDATE usuarios SET nome = ?, username = ?, bio = ? WHERE id = ?
    """
    supabase.table("usuarios") \
        .update({"nome": nome, "username": username, "bio": bio}) \
        .eq("id", user_id) \
        .execute()


def username_em_uso(username: str, excluir_id: int) -> bool:
    """
    Verifica se um @username já está em uso por outro usuário.
    Equivale a: SELECT id FROM usuarios WHERE username = ? AND id != ?
    """
    resp = supabase.table("usuarios") \
        .select("id") \
        .eq("username", username) \
        .neq("id", excluir_id) \
        .limit(1) \
        .execute()
    return len(resp.data) > 0


# =================================================================
# EVENTOS
# =================================================================

def get_todos_eventos(limit: int = 100) -> list[dict]:
    """
    Retorna todos os eventos com limite para não quebrar o layout,
    trazendo primeiro os mais recentes ou aleatórios.
    """
    resp = supabase.table("eventos").select("*").limit(limit).execute()
    return _list(resp)

def get_eventos_patrocinados() -> list[dict]:
    """
    Retorna apenas os eventos patrocinados (destaques).
    """
    resp = supabase.table("eventos") \
        .select("*") \
        .eq("is_sponsored", True) \
        .execute()
    return _list(resp)

def get_eventos_proximos(regiao: str, limit: int = 20) -> list[dict]:
    """
    Tenta buscar eventos baseados na região preferida do usuário.
    Se a região bater com algo no 'local', ele retorna.
    """
    if not regiao or regiao == "Indefinido":
        return []
    
    # Exemplo simples de busca por keyword do local
    palavra_chave = regiao.split()[0]
    resp = supabase.table("eventos") \
        .select("*") \
        .ilike("local", f"%{palavra_chave}%") \
        .limit(limit) \
        .execute()
    return _list(resp)


def get_eventos_recentes(limit: int = 5) -> list[dict]:
    """
    Retorna os últimos N eventos cadastrados.
    Equivale a: SELECT * FROM eventos ORDER BY id DESC LIMIT N
    """
    resp = supabase.table("eventos") \
        .select("*") \
        .order("id", desc=True) \
        .limit(limit) \
        .execute()
    return _list(resp)


def get_evento_by_id(evento_id: int) -> dict | None:
    """
    Busca um evento pelo ID.
    Equivale a: SELECT * FROM eventos WHERE id = ?
    """
    resp = supabase.table("eventos") \
        .select("*") \
        .eq("id", evento_id) \
        .limit(1) \
        .execute()
    return _single(resp)


def insert_evento(nome: str, local: str, data: str, tipo: str, tags: str,
                  criador_id: int, imagem: str = 'meskla.jpg', link: str = '#', is_sponsored: bool = True) -> None:
    """
    Cria um novo evento.
    Eventos criados por usuários comuns também podem ser considerados patrocinados se pagarem,
    mas por padrão marcamos como True pelo admin.
    """
    supabase.table("eventos").insert({
        "nome": nome,
        "local": local,
        "data": data,
        "tipo": tipo,
        "tags": tags,
        "criador_id": criador_id,
        "imagem": imagem,
        "link": link,
        "is_sponsored": is_sponsored,
        "source": "themove"
    }).execute()

# =================================================================
# CACHE DO GEMINI
# =================================================================

def get_recomendacoes_cache(usuario_id: int) -> list[dict] | None:
    """
    Tenta buscar recomendações do cache para este usuário.
    """
    resp = supabase.table("recomendacoes_cache") \
        .select("recomendacoes_json") \
        .eq("usuario_id", usuario_id) \
        .limit(1) \
        .execute()
    
    if resp.data:
        return resp.data[0].get("recomendacoes_json")
    return None

def set_recomendacoes_cache(usuario_id: int, recomendacoes_json: list[dict]) -> None:
    """
    Salva ou atualiza as recomendações no cache do usuário (Upsert).
    """
    supabase.table("recomendacoes_cache").upsert({
        "usuario_id": usuario_id,
        "recomendacoes_json": recomendacoes_json
    }).execute()


# =================================================================
# PRESENÇAS
# =================================================================

def get_presenca(usuario_id: int, evento_id: int, data_presenca: str = None) -> dict | None:
    """
    Verifica se o usuário já confirmou presença em um evento (e data opcional).
    """
    query = supabase.table("presencas").select("id").eq("usuario_id", usuario_id).eq("evento_id", evento_id)
    if data_presenca:
        query = query.eq("data_presenca", data_presenca)
    else:
        query = query.is_("data_presenca", "null")
        
    resp = query.limit(1).execute()
    return _single(resp)


def insert_presenca(usuario_id: int, evento_id: int, data_presenca: str = None) -> dict | None:
    """Registra a presença (vou estar lá)"""
    data = {
        "usuario_id": usuario_id,
        "evento_id": evento_id
    }
    if data_presenca:
        data["data_presenca"] = data_presenca
        
    resp = supabase.table("presencas").insert(data).execute()
    return _single(resp)

def delete_presenca(usuario_id: int, evento_id: int, data_presenca: str = None):
    """Remove a presença (cancelar)"""
    query = supabase.table("presencas").delete().eq("usuario_id", usuario_id).eq("evento_id", evento_id)
    if data_presenca:
        query = query.eq("data_presenca", data_presenca)
    else:
        query = query.is_("data_presenca", "null")
    query.execute()

# =================================================================
# FAVORITOS
# =================================================================

def get_favoritos(usuario_id: int) -> list[int]:
    try:
        resp = supabase.table("favoritos").select("evento_id").eq("usuario_id", usuario_id).execute()
        return [r['evento_id'] for r in _list(resp)]
    except:
        return []

def is_favorito(usuario_id: int, evento_id: int) -> bool:
    try:
        resp = supabase.table("favoritos").select("*").eq("usuario_id", usuario_id).eq("evento_id", evento_id).execute()
        return bool(_single(resp))
    except:
        return False

def add_favorito(usuario_id: int, evento_id: int):
    try:
        if not is_favorito(usuario_id, evento_id):
            supabase.table("favoritos").insert({"usuario_id": usuario_id, "evento_id": evento_id}).execute()
    except:
        pass

def remove_favorito(usuario_id: int, evento_id: int):
    try:
        supabase.table("favoritos").delete().eq("usuario_id", usuario_id).eq("evento_id", evento_id).execute()
    except:
        pass


def get_total_presencas() -> int:
    """
    Conta o total de presenças confirmadas (para o dashboard).
    Equivale a: SELECT COUNT(*) as total FROM presencas
    """
    resp = supabase.table("presencas").select("id", count="exact").execute()
    return resp.count or 0


def get_presencas_de_evento_com_usuario(evento_id: int) -> list[dict]:
    """
    Retorna lista de usuários que confirmaram presença em um evento (com JOIN).
    Para admin: vê todos.
    Equivale a:
      SELECT u.nome, u.username, u.foto
      FROM presencas p JOIN usuarios u ON p.usuario_id = u.id
      WHERE p.evento_id = ?
    Retorna lista de dicts com chaves: nome, username, foto
    """
    resp = supabase.table("presencas") \
        .select("data_presenca, usuarios(nome, username, foto)") \
        .eq("evento_id", evento_id) \
        .execute()
    # Desembala o relacionamento aninhado
    result = []
    for row in (resp.data or []):
        u = row.get("usuarios")
        if u:
            u['data_presenca'] = row.get('data_presenca')
            result.append(u)
    return result


def get_presencas_de_evento_filtrado(evento_id: int, usuario_ids: list[int]) -> list[dict]:
    """
    Retorna usuários que confirmaram presença em um evento,
    filtrando apenas por uma lista de IDs (amigos + eu mesmo).
    Equivale ao query dinâmico com IN(placeholders).
    """
    if not usuario_ids:
        return []
    resp = supabase.table("presencas") \
        .select("data_presenca, usuarios(nome, username, foto)") \
        .eq("evento_id", evento_id) \
        .in_("usuario_id", usuario_ids) \
        .execute()
    result = []
    for row in (resp.data or []):
        u = row.get("usuarios")
        if u:
            u['data_presenca'] = row.get('data_presenca')
            result.append(u)
    return result


def get_presencas_de_evento_filtrado_sem_bar(evento_id: int, usuario_ids: list[int], tipo_evento: str) -> list[dict]:
    """
    Retorna presenças filtrando amigos, excluindo tipo 'bar' para não-admin.
    Usado na rota /eventos para usuários comuns.
    """
    if tipo_evento == 'bar':
        return []
    return get_presencas_de_evento_filtrado(evento_id, usuario_ids)


def get_presencas_de_usuario(usuario_id: int, excluir_bar: bool = False) -> list[dict]:
    """
    Retorna eventos em que o usuário confirmou presença (para o perfil).
    Equivale a:
      SELECT e.* FROM presencas p JOIN eventos e ON p.evento_id = e.id
      WHERE p.usuario_id = ? [AND e.tipo != 'bar']
    """
    resp = supabase.table("presencas") \
        .select("data_presenca, eventos(*)") \
        .eq("usuario_id", usuario_id) \
        .execute()
    result = []
    for row in (resp.data or []):
        ev = row.get("eventos")
        if ev:
            if excluir_bar and ev.get("tipo") == "bar":
                continue
            ev['data_presenca'] = row.get('data_presenca')
            result.append(ev)
    return result


def contar_presencas_amigos_em_evento(evento_id: int, amigos_ids: list[int]) -> int:
    """
    Conta quantos amigos confirmaram presença em um evento.
    Usado no sistema de recomendação.
    Equivale a: SELECT COUNT(*) FROM presencas WHERE evento_id = ? AND usuario_id IN (...)
    """
    if not amigos_ids:
        return 0
    resp = supabase.table("presencas") \
        .select("id", count="exact") \
        .eq("evento_id", evento_id) \
        .in_("usuario_id", amigos_ids) \
        .execute()
    return resp.count or 0


def get_ranking_eventos() -> list[dict]:
    """
    Retorna o ranking de eventos por número de presenças.
    Equivale a:
      SELECT e.nome, COUNT(p.id) as qtd
      FROM presencas p JOIN eventos e ON p.evento_id = e.id
      GROUP BY p.evento_id ORDER BY qtd DESC
    Retorna lista de dicts com chaves: nome, qtd
    """
    # Supabase REST API não suporta GROUP BY nativo.
    # Fazemos o agrupamento em Python.
    resp = supabase.table("presencas") \
        .select("evento_id, eventos(nome)") \
        .execute()

    contagem: dict[int, dict] = {}
    for row in (resp.data or []):
        eid = row.get("evento_id")
        nome = (row.get("eventos") or {}).get("nome", "")
        if eid not in contagem:
            contagem[eid] = {"nome": nome, "qtd": 0}
        contagem[eid]["qtd"] += 1

    ranking = sorted(contagem.values(), key=lambda x: x["qtd"], reverse=True)
    return ranking


# =================================================================
# SEGUIDORES
# =================================================================

def get_seguindo(seguidor_id: int) -> list[dict]:
    """
    Retorna lista de usuários que 'seguidor_id' segue (com dados completos).
    Equivale a:
      SELECT u.* FROM seguidores s
      JOIN usuarios u ON s.seguido_id = u.id
      WHERE s.seguidor_id = ?
    """
    resp = supabase.table("seguidores") \
        .select("usuarios!seguido_id(*)") \
        .eq("seguidor_id", seguidor_id) \
        .execute()
    result = []
    for row in (resp.data or []):
        u = row.get("usuarios!seguido_id") or row.get("usuarios")
        if u:
            result.append(u)
    return result


def get_seguindo_ids(seguidor_id: int) -> list[int]:
    """
    Retorna apenas os IDs dos usuários que 'seguidor_id' segue.
    Equivale a: SELECT seguido_id FROM seguidores WHERE seguidor_id = ?
    """
    resp = supabase.table("seguidores") \
        .select("seguido_id") \
        .eq("seguidor_id", seguidor_id) \
        .execute()
    return [r["seguido_id"] for r in (resp.data or [])]


def count_seguidores(seguido_id: int) -> int:
    """
    Conta quantas pessoas seguem um usuário.
    Equivale a: SELECT COUNT(*) FROM seguidores WHERE seguido_id = ?
    """
    resp = supabase.table("seguidores") \
        .select("id", count="exact") \
        .eq("seguido_id", seguido_id) \
        .execute()
    return resp.count or 0


def count_seguindo(seguidor_id: int) -> int:
    """
    Conta quantas pessoas um usuário segue.
    Equivale a: SELECT COUNT(*) FROM seguidores WHERE seguidor_id = ?
    """
    resp = supabase.table("seguidores") \
        .select("id", count="exact") \
        .eq("seguidor_id", seguidor_id) \
        .execute()
    return resp.count or 0


def is_seguindo(seguidor_id: int, seguido_id: int) -> bool:
    """
    Verifica se seguidor_id já segue seguido_id.
    Equivale a: SELECT id FROM seguidores WHERE seguidor_id = ? AND seguido_id = ?
    """
    resp = supabase.table("seguidores") \
        .select("id") \
        .eq("seguidor_id", seguidor_id) \
        .eq("seguido_id", seguido_id) \
        .limit(1) \
        .execute()
    return len(resp.data) > 0


def insert_seguidor(seguidor_id: int, seguido_id: int) -> None:
    """
    Registra que seguidor_id passou a seguir seguido_id.
    Equivale a: INSERT INTO seguidores (seguidor_id, seguido_id) VALUES (?, ?)
    """
    supabase.table("seguidores").insert({
        "seguidor_id": seguidor_id,
        "seguido_id": seguido_id,
    }).execute()


def delete_seguidor(seguidor_id: int, seguido_id: int) -> None:
    """
    Remove o relacionamento de seguir.
    Equivale a: DELETE FROM seguidores WHERE seguidor_id = ? AND seguido_id = ?
    """
    supabase.table("seguidores") \
        .delete() \
        .eq("seguidor_id", seguidor_id) \
        .eq("seguido_id", seguido_id) \
        .execute()


def get_sugestoes_usuarios(excluir_ids: list[int], limit: int = 10) -> list[dict]:
    """
    Retorna sugestões de usuários que o usuário ainda não segue.
    Equivale a:
      SELECT * FROM usuarios
      WHERE id NOT IN (...) AND username != '@themove'
      LIMIT 10
    """
    query = supabase.table("usuarios").select("*")
    if excluir_ids:
        ids_str = ",".join(str(i) for i in excluir_ids)
        query = query.filter("id", "not.in", f"({ids_str})")
    
    resp = query.neq("username", "@themove").limit(limit).execute()
    return _list(resp)
