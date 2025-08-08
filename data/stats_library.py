# data/stats_library.py

# Define a ordem de exibição das categorias de status
STAT_CATEGORIES = ["COMBATE", "DEFESA", "COLETA"]

# Define todos os status, seus nomes de exibição, emojis e a qual categoria pertencem
STATS = {
    # --- STATUS DE COMBATE ---
    "DANO": {"nome": "Dano Físico", "emoji": "⚔️", "category": "COMBATE"},
    "DANO_MAGICO": {"nome": "Dano Mágico", "emoji": "✨", "category": "COMBATE"},
    "CRITICO_CHANCE": {"nome": "Chance de Crítico", "emoji": "💥", "category": "COMBATE", "is_percent": True},
    "CRITICO_DANO": {"nome": "Dano Crítico Extra", "emoji": "✨", "category": "COMBATE", "is_percent": True},
    "ATAQUE_BUFF": {"nome": "Bônus de Ataque", "emoji": "🔼", "category": "COMBATE"},
    
    # --- STATUS DE DEFESA ---
    "VIDA_MAXIMA": {"nome": "Vida Máxima", "emoji": "❤️", "category": "DEFESA"},
    "MANA_MAXIMA": {"nome": "Mana Máxima", "emoji": "💧", "category": "DEFESA"},
    "ARMADURA": {"nome": "Armadura", "emoji": "🛡️", "category": "DEFESA"},
    "ARMADURA_MAGICA": {"nome": "Armadura Mágica", "emoji": "💠", "category": "DEFESA"},
    "BLOQUEIO_CHANCE": {"nome": "Chance de Bloqueio", "emoji": "✋", "category": "DEFESA", "is_percent": True},
    "DEFESA_BUFF": {"nome": "Bônus de Defesa", "emoji": "🔼", "category": "DEFESA"},
    "ESCUDO": {"nome": "Escudo", "emoji": "💠", "category": "DEFESA"},
    
     # --- STATUS DE COLETA (AGORA ESPECÍFICOS) ---
    "poder_coleta_mineracao": {"nome": "Poder de Coleta (⛏️)", "emoji": "🍀", "category": "COLETA", "is_percent": True},
    "eficiencia_mineracao": {"nome": "Eficiência (⛏️)", "emoji": "⚡", "category": "COLETA", "is_percent": True},
    "fortuna_mineracao": {"nome": "Fortuna (⛏️)", "emoji": "💰", "category": "COLETA"},
    "nivel_mineração": {"nome": "Nível de Mineração", "emoji": "⛏️", "category": "COLETA"},
    # Exemplo para o futuro Lenhador

    # --- STATUS DE HABILIDADES E EFEITOS (SEM CATEGORIA VISÍVEL) ---
    "CURA": {"nome": "Cura", "emoji": "💖"},
    "DURACAO": {"nome": "Duração (turnos)", "emoji": "⏳"},
    "LENTIDAO": {"nome": "Lentidão (stacks)", "emoji": "🔽"},
    "ENVENENAMENTO": {"nome": "Envenenamento", "emoji": "☠️"},
    "CONGELAMENTO": {"nome": "Congelamento", "emoji": "🥶"},
}


def format_stat(stat_id, value):
    """Formata um status para exibição com emoji e % se necessário."""
    stat_info = STATS.get(stat_id)
    if not stat_info:
        return f"{stat_id}: {value}"
    
    valor_prefixo = "+" if "BUFF" in stat_id else ""
    
    # --- CORREÇÃO APLICADA AQUI ---
    if stat_info.get("is_percent"):
        # Usa .0f para remover as casas decimais e formatar como inteiro
        valor_str = f"{value * 100:.0f}%" 
    else:
        # Garante que números não percentuais também sejam formatados de forma limpa
        valor_str = f"{value:,}"

    return f"{stat_info['emoji']} **{stat_info['nome']}:** {valor_prefixo}{valor_str}"