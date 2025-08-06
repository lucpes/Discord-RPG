# data/profissoes_library.py

PROFISSOES = {
    "minerador": {
        "nome": "Minerador",
        "emoji": "⛏️",
        "descricao": "Especialista na extração de minérios e gemas das profundezas da terra.",
        "niveis": [
            # Nível 1 para 2
            {"xp_para_upar": 500, "recompensas": {
                "passivas": {"fortuna": 1},
                "desbloqueios": ["Acesso a Minas de Cobre"]
            }},
            # Nível 2 para 3
            {"xp_para_upar": 1200, "recompensas": {
                "passivas": {"fortuna": 2, "eficiencia": 0.02}, # +2% de eficiência
                "desbloqueios": ["Receita: Barra de Cobre"]
            }},
        ]
    },
    "ferreiro": {
        "nome": "Ferreiro",
        "emoji": "🔨",
        "descricao": "Mestre na arte de forjar metais em armas e armaduras poderosas.",
        "niveis": [
            # Nível 1 para 2
            {"xp_para_upar": 800, "recompensas": {
                "passivas": {"chance_obra_prima": 0.01}, # +1% de chance de obra-prima
                "desbloqueios": ["Receitas de Equipamentos de Ferro"]
            }},
        ]
    },
    "alquimista": {
        "nome": "Alquimista",
        "emoji": "🧪",
        "descricao": "Estudioso de poções e elixires que alteram a realidade.",
        "niveis": [
            # Nível 1 para 2
            {"xp_para_upar": 400, "recompensas": {
                "passivas": {"quantidade_obra_prima_pocao": 1}, # Cria +1 poção em um craft perfeito
                "desbloqueios": ["Receita: Poção de Força Fraca"]
            }},
        ]
    }
}

# Cria uma lista ordenada de IDs para o Select menu
ORDERED_PROFS = list(PROFISSOES.keys())