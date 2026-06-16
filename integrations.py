import requests
import json
from supabase_client import supabase

def fetch_overpass_brasilia():
    print("Iniciando busca na Overpass API (OpenStreetMap) por bares/baladas em Brasília...")
    
    # Raio de 15km ao redor das coordenadas centrais do Plano Piloto (Torre de TV)
    # Procuramos por nodes com amenity=bar, pub ou nightclub
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    (
      node["amenity"~"bar|nightclub|pub"](around:15000, -15.7922, -47.8928);
    );
    out center;
    """
    
    try:
        headers = {
            "User-Agent": "TheMoveApp/1.0",
            "Accept": "application/json"
        }
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Erro ao acessar Overpass API: {e}")
        # Tentar imprimir a resposta de erro caso disponível
        if hasattr(e, 'response') and e.response is not None:
            print(f"Detalhes: {e.response.text}")
        return

    elements = data.get("elements", [])
    print(f"Encontrados {len(elements)} estabelecimentos. Filtrando apenas os que têm nome...")
    
    # Buscar o ID do admin (@themove) para atrelar a ele
    admin_resp = supabase.table("usuarios").select("id").eq("username", "@themove").limit(1).execute()
    if not admin_resp.data:
        print("Erro: Admin @themove não encontrado no Supabase.")
        return
    admin_id = admin_resp.data[0]["id"]
    
    novos_eventos = []
    
    for el in elements:
        tags = el.get("tags", {})
        nome = tags.get("name")
        
        # Ignorar estabelecimentos sem nome
        if not nome:
            continue
            
        # Tentar construir um local amigável (Rua, bairro)
        local = tags.get("addr:street")
        if not local:
            local = tags.get("addr:suburb", "Brasília, DF")
        
        tipo_amenity = tags.get("amenity", "bar")
        tipo_mapeado = "bar" if tipo_amenity in ["bar", "pub"] else "balada"
        
        # Site ou rede social
        link = tags.get("website") or tags.get("contact:instagram") or tags.get("facebook") or "#"
        if link != "#" and not link.startswith("http"):
            link = f"https://www.instagram.com/{link}" if "instagram" in tags.keys() else f"https://{link}"
            
        # Tags adicionais baseadas no nome (simplificado)
        tags_locais = f"{tipo_mapeado}, gratuito, bebida"
        if "sertanejo" in nome.lower(): tags_locais += ", sertanejo"
        if "rock" in nome.lower(): tags_locais += ", rock"
        
        novos_eventos.append({
            "nome": nome,
            "local": local,
            "data": "Aberto (Confira o horário no local)",
            "imagem": "contexto.jpg", # Imagem genérica para testes
            "tipo": tipo_mapeado,
            "link": link,
            "tags": tags_locais,
            "criador_id": admin_id,
            "is_sponsored": False,
            "source": "overpass"
        })

    print(f"Filtrados {len(novos_eventos)} estabelecimentos com nome. Inserindo no Supabase...")
    
    # Inserir em lotes para não sobrecarregar a API
    batch_size = 50
    inseridos = 0
    for i in range(0, len(novos_eventos), batch_size):
        batch = novos_eventos[i:i+batch_size]
        try:
            supabase.table("eventos").insert(batch).execute()
            inseridos += len(batch)
            print(f" Inseridos {inseridos}/{len(novos_eventos)}...")
        except Exception as e:
            print(f"Erro ao inserir lote no Supabase: {e}")
            
    print(f"✅ Concluído! {inseridos} novos estabelecimentos adicionados de forma 100% gratuita.")

if __name__ == "__main__":
    fetch_overpass_brasilia()
