# data/stats_library.py

STATS = {
    # Status de Itens e Base
    "DANO": {"nome": "Dano", "emoji": "⚔️"},
    "CRITICO_CHANCE": {"nome": "Chance de Crítico", "emoji": "💥", "is_percent": True},
    "CRITICO_DANO": {"nome": "Dano Crítico Extra", "emoji": "✨", "is_percent": True},
    "ARMADURA": {"nome": "Armadura", "emoji": "🛡️"},
    "ARMADURA_MAGICA": {"nome": "Resistência Mágica", "emoji": "💠"},
    "VIDA_MAXIMA": {"nome": "Vida Máxima", "emoji": "❤️"},
    "MANA_MAXIMA": {"nome": "Mana Máxima", "emoji": "💧"},
    "BLOQUEIO_CHANCE": {"nome": "Chance de Bloqueio", "emoji": "✋", "is_percent": True},
    
    # Status de Habilidades e Efeitos
    "CURA": {"nome": "Cura", "emoji": "💖"},
    "DANO_MAGICO": {"nome": "Dano Mágico", "emoji": "✨"},
    "ESCUDO": {"nome": "Escudo", "emoji": "💠"},
    "ATAQUE_BUFF": {"nome": "Bônus de Ataque", "emoji": "🔼"},
    "DEFESA_BUFF": {"nome": "Bônus de Defesa", "emoji": "🔼"},
    "DURACAO": {"nome": "Duração (turnos)", "emoji": "⏳"},
    "LENTIDAO": {"nome": "Lentidão (stacks)", "emoji": "🔽"},
}

def format_stat(stat_id, value):
    """Formata um status para exibição com emoji e % se necessário."""
    stat_info = STATS.get(stat_id)
    if not stat_info:
        return f"{stat_id}: {value}"
    
    # Mostra o sinal de + apenas para buffs, não para duração.
    valor_prefixo = "+" if "BUFF" in stat_id else ""
    valor_sufixo = "%" if stat_info.get("is_percent") else ""
    
    return f"{stat_info['emoji']} **{stat_info['nome']}:** {valor_prefixo}{value}{valor_sufixo}"