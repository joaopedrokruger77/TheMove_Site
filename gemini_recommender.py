# =================================================================
# gemini_recommender.py — Sistema de Recomendação com Google Gemini
#
# Este módulo recebe o perfil do usuário e a lista de eventos disponíveis,
# envia para a API do Gemini e retorna as notas de compatibilidade
# e as justificativas em formato estruturado (JSON).
# =================================================================

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)

# Configuração da API do Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usando o modelo Gemini Flash mais recente por ser mais rápido e barato
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    model = None

def gerar_recomendacoes(user_profile: dict, eventos_disponiveis: list[dict]) -> list[dict]:
    """
    Recebe os dados do usuário e os eventos.
    Retorna uma lista de recomendações no formato:
    [
      {
         "evento_id": 123,
         "score": 85,
         "justificativa": "Texto explicando porque o evento combina com o usuário..."
      },
      ...
    ]
    """
    if not model:
        print("AVISO: GEMINI_API_KEY não configurada. Retornando recomendações vazias.")
        return []
        
    if not eventos_disponiveis:
        return []

    # Extrair perfil do usuário
    idade = "Desconhecida"
    if user_profile.get("nascimento"):
        try:
            # Cálculo simplificado de idade
            ano_nasc = int(user_profile["nascimento"].split("-")[0])
            idade = str(2026 - ano_nasc) + " anos"
        except:
            pass

    perfil_str = f"""
    Perfil do Usuário:
    - Gosto musical: {user_profile.get('tags') or 'Não informado'}
    - Regiões onde costuma sair: {user_profile.get('regiao') or 'Não informado'}
    - Idade: {idade}
    """

    # Simplificar a lista de eventos para caber no prompt sem gastar muito token
    eventos_str = "Eventos Disponíveis:\n"
    for ev in eventos_disponiveis:
        patrocinado = "SIM" if ev.get("is_sponsored") else "NÃO"
        eventos_str += f"- ID {ev['id']}: {ev['nome']} | Tipo: {ev.get('tipo')} | Local: {ev.get('local')} | Tags: {ev.get('tags')} | Patrocinado: {patrocinado}\n"

    prompt = f"""
Você é um sistema de recomendação inteligente de eventos e bares de Brasília.
Analise o perfil do usuário e os eventos disponíveis. Para cada evento, calcule um score de compatibilidade de 0 a 100.

{perfil_str}

{eventos_str}

CRITÉRIOS DE AVALIAÇÃO (aplique todos):
1. **Gosto Musical (peso alto):** Se as tags musicais do evento batem com o gosto do usuário, score alto. Se não tem NADA a ver, score baixo (abaixo de 30).
2. **Idade:** Se o evento é tagueado como "jovem" e o usuário é mais velho (acima de 35), penalize. Se é "adulto" e o usuário é jovem (abaixo de 22), penalize. Se tem "jovem, adulto" ou não especifica, não penalize.
3. **Localidade:** Se o evento fica numa região que o usuário marcou como preferida, bônus de +10 a +15 pontos.
4. **Patrocinado:** Eventos patrocinados recebem um leve bônus (+5), mas NUNCA devem ter score alto se o perfil não combina.

REGRAS DE SAÍDA:
- Retorne APENAS um array JSON puro (sem markdown, sem ```).
- Cada objeto: {{"evento_id": int, "score": int, "justificativa": "string curta (1-2 frases)"}}
- Seja RIGOROSO. Só dê score acima de 75 se realmente combinar bem.

EXEMPLO:
[
  {{"evento_id": 1, "score": 92, "justificativa": "Show de sertanejo combina perfeitamente com seu gosto e fica na Asa Sul onde você costuma sair."}},
  {{"evento_id": 2, "score": 25, "justificativa": "Balada de eletrônica não combina com seu perfil musical."}}
]
"""

    try:
        response = model.generate_content(prompt)
        texto = response.text.strip()
        
        # Limpeza caso o modelo retorne com blocos de código markdown
        if texto.startswith("```json"):
            texto = texto[7:]
        if texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]
            
        texto = texto.strip()
        
        recomendacoes = json.loads(texto)
        
        # Garantir que todos os IDs de eventos presentes na entrada tenham uma nota, mesmo que não venham no JSON
        # Montar um dicionário para busca rápida
        rec_dict = {r["evento_id"]: r for r in recomendacoes}
        
        resultado_final = []
        for ev in eventos_disponiveis:
            ev_id = ev["id"]
            if ev_id in rec_dict:
                resultado_final.append(rec_dict[ev_id])
            else:
                # Fallback caso a IA esqueça algum evento
                bonus = 20 if ev.get("is_sponsored") else 0
                resultado_final.append({
                    "evento_id": ev_id,
                    "score": 50 + bonus,
                    "justificativa": "Este evento pode ser interessante para você explorar algo novo."
                })
                
        # Ordenar pelo score
        resultado_final.sort(key=lambda x: x["score"], reverse=True)
        return resultado_final

    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        return []

def chat_agente_the_move(mensagem: str, eventos: list[dict]) -> str:
    """
    Função de chat para o Agente The Move.
    """
    if not model:
        return "Desculpe, ainda não tenho informação para salvar seu rolê. (A IA está desligada!)"
        
    contexto = "Aqui está a lista atual de eventos e bares:\n"
    for ev in eventos:
        contexto += f"- Nome: {ev['nome']} | Local: {ev['local']} | Data: {ev['data']} | Tipo: {ev.get('tipo', 'evento')}\n"

    prompt = f"""
Você é o "Agente The Move", um robozinho futurista super animado e especialista supremo em rolês (festas, bares, shows, baladas) em Brasília (BSB).
Você fica no canto da tela do site The Move ajudando a galera a encontrar onde curtir.
Use MUITAS gírias jovens, divertidas e animadas de festa (ex: bora, partiu, rolê, monstro, hypado, colar).

Contexto dos eventos no banco de dados do site The Move atualmente:
{contexto}

A pergunta do usuário é: "{mensagem}"

Regras de Resposta:
1. Você deve usar TODO o seu conhecimento global como inteligência artificial para responder sobre QUALQUER festa, show, produtora (como R2, Ingresse, Cheers, etc.) ou bar em Brasília, mesmo que não esteja na lista do contexto acima.
2. Se o evento estiver no contexto acima, use as informações de lá (como data e local). Se não estiver, puxe da sua memória e passe a visão!
3. Seja sempre muito animado, parecendo um parceiro de rolê.
4. Responda de forma direta e curta (1 a 3 frases no máximo), ideal para um balão de chat.
5. SOMENTE se a pergunta não tiver ABSOLUTAMENTE NADA a ver com festas/rolês/Brasília ou se você de jeito nenhum souber a resposta, você DEVE dizer: "Desculpe, ainda não tenho informação para salvar seu rolê."
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro no chat do Agente The Move: {e}")
        return "Desculpe, ainda não tenho informação para salvar seu rolê."
