# =================================================================
# local_recommender.py — Sistema de Recomendação Local (sem API)
#
# Fallback para quando o Gemini não está configurado.
# Faz matching simples de tags entre o perfil do usuário e os eventos.
# =================================================================

# Coordenadas aproximadas de locais em Brasília para o mapa
COORDENADAS_BSB = {
    # Regiões
    'asa sul': (-15.8267, -47.9218),
    'asa norte': (-15.7631, -47.8829),
    'sudoeste': (-15.7989, -47.9350),
    'noroeste': (-15.7700, -47.9100),
    'águas claras': (-15.8400, -48.0200),
    'taguatinga': (-15.8364, -48.0500),
    'guará': (-15.8300, -47.9800),
    'cruzeiro': (-15.8000, -47.9400),
    'lago sul': (-15.8500, -47.8700),
    'lago norte': (-15.7400, -47.8500),
    'ceilândia': (-15.8200, -48.1100),
    'plano piloto': (-15.7939, -47.8828),
    'saan': (-15.7600, -47.9300),
    'sia': (-15.8100, -47.9600),
    'park way': (-15.8900, -47.9500),
    'conic': (-15.7960, -47.8860),
    
    # Locais específicos
    'arena brb': (-15.7800, -47.8700),
    'parque da cidade': (-15.8100, -47.9100),
    'torre de tv': (-15.7900, -47.8900),
    'pontão do lago sul': (-15.8350, -47.8600),
    'estádio mané garrincha': (-15.7834, -47.8990),
    'teatro nacional': (-15.7880, -47.8820),
    'centro de convenções': (-15.7890, -47.8750),
    'setor de clubes sul': (-15.8200, -47.8900),
    'setor comercial sul': (-15.7950, -47.8850),
    'granja do torto': (-15.7300, -47.8900),
    'aabb': (-15.8400, -47.8650),
    'aeroporto': (-15.8711, -47.9186),
    'casa da manchete': (-15.7900, -47.9250),
    'sig': (-15.7900, -47.9250),
    'eixo monumental': (-15.7900, -47.8900),
}


def obter_coordenadas(local_str: str) -> tuple:
    """Tenta encontrar coordenadas aproximadas para um local."""
    if not local_str:
        return (-15.7939, -47.8828)  # Centro de Brasília como fallback
    
    local_lower = local_str.lower()
    
    # Buscar match exato primeiro
    for chave, coords in COORDENADAS_BSB.items():
        if chave in local_lower:
            return coords
    
    # Fallback: centro de Brasília
    return (-15.7939, -47.8828)


def recomendar_por_tags(user_profile: dict, eventos: list[dict]) -> list[dict]:
    """
    Recomendação local baseada em matching de tags.
    Não precisa de Gemini. Funciona para todo mundo.
    
    Analisa:
    - Gosto musical (tags do usuário vs tags do evento)
    - Região (regiões do usuário vs local do evento)
    - Idade (tags de faixa etária do evento)
    
    Retorna lista ordenada por score com justificativa.
    """
    user_tags_raw = user_profile.get('tags') or ''
    user_regioes_raw = user_profile.get('regiao') or ''
    
    user_tags = set(t.strip().lower() for t in user_tags_raw.split(',') if t.strip())
    user_regioes = set(r.strip().lower() for r in user_regioes_raw.split(',') if r.strip())
    
    # Calcular idade
    idade = None
    if user_profile.get('nascimento'):
        try:
            ano_nasc = int(user_profile['nascimento'].split('-')[0])
            idade = 2027 - ano_nasc
        except:
            pass
    
    resultados = []
    
    for ev in eventos:
        score = 50  # Base
        justificativas = []
        
        ev_tags_raw = ev.get('tags') or ''
        ev_tags = set(t.strip().lower() for t in ev_tags_raw.split(',') if t.strip())
        ev_local = (ev.get('local') or '').lower()
        
        # 1. Matching de gosto musical via cálculo Vetorial (u == e)
        if user_tags and ev_tags:
            todas_tags = user_tags.union(ev_tags)
            if todas_tags:
                vetor_u = [1 if tag in user_tags else 0 for tag in todas_tags]
                vetor_e = [1 if tag in ev_tags else 0 for tag in todas_tags]
                
                # Soma matches: int(u == e) e divide pelo tamanho do vetor
                soma_matches = sum(int(u == e) for u, e in zip(vetor_u, vetor_e))
                similaridade = soma_matches / len(todas_tags)
                
                if similaridade > 0:
                    bonus = min(35, int(similaridade * 50))
                    score += bonus
                    justificativas.append(f"combina com seu gosto ({int(similaridade*100)}% similaridade vetorial)")
                else:
                    score -= 15
        
        # 2. Matching de região
        if user_regioes:
            for regiao in user_regioes:
                if regiao in ev_local:
                    score += 10
                    justificativas.append(f"fica na região que você curte")
                    break
        
        # 3. Faixa etária
        if idade:
            if idade < 25 and 'adulto' in ev_tags and 'jovem' not in ev_tags:
                score -= 10
            elif idade >= 35 and 'jovem' in ev_tags and 'adulto' not in ev_tags:
                score -= 10
            elif idade < 25 and 'jovem' in ev_tags:
                score += 5
                justificativas.append("é pra sua faixa etária")
            elif idade >= 30 and 'adulto' in ev_tags:
                score += 5
                justificativas.append("é pra sua faixa etária")
        
        # 4. Bônus patrocinado
        if ev.get('is_sponsored'):
            score += 5
        
        # Limitar score
        score = max(0, min(100, score))
        
        justificativa = '. '.join(justificativas[:2]).capitalize() if justificativas else 'Pode ser uma boa experiência nova.'
        
        resultados.append({
            'evento_id': ev['id'],
            'score': score,
            'justificativa': justificativa
        })
    
    resultados.sort(key=lambda x: x['score'], reverse=True)
    return resultados
