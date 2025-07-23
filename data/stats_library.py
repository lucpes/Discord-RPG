# data/stats_library.py

STATS = {
    # Status Ofensivos
    "DANO": {"nome": "Dano", "emoji": "⚔️"},
    "CRITICO_CHANCE": {"nome": "Chance de Crítico", "emoji": "💥", "is_percent": True},
    "CRITICO_DANO": {"nome": "Dano Crítico Extra", "emoji": "✨", "is_percent": True},
    
    # Status Defensivos
    "ARMADURA": {"nome": "Armadura", "emoji": "🛡️"},
    "VIDA_EXTRA": {"nome": "Vida Máxima", "emoji": "❤️"},
    "BLOQUEIO_CHANCE": {"nome": "Chance de Bloqueio", "emoji": "✋", "is_percent": True},
    
    # Status de Utilidade
    "CURA_PODER": {"nome": "Poder de Cura", "emoji": "💖"},
}

def format_stat(stat_id, value):
    """Formata um status para exibição com emoji e % se necessário."""
    stat_info = STATS.get(stat_id)
    if not stat_info:
        return f"{stat_id}: {value}"
    
    formatted_value = f"{value}%" if stat_info.get("is_percent") else f"{value}"
    return f"{stat_info['emoji']} **{stat_info['nome']}:** +{formatted_value}"