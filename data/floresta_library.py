# data/floresta_library.py

FLORESTA_LOCATIONS = {
    # NÍVEL 1 DE CONSTRUÇÃO
    "arbusto": {
        "nome": "Arbusto",
        "nivel_minimo_edificio": 1,
        "nivel_lenhador": 1,
        "nivel_machado": 1,
        "tempo_s": 600,
        "xp_concedido": 10,
        "loot_table": [
            {"template_id": "graveto", "chance_base": 1.0, "quantidade": (1,2)},
        ]
    },
    "clareira_serena": {
        "nome": "Clareira Serena",
        "nivel_minimo_edificio": 6,
        "nivel_lenhador": 1,
        "nivel_machado": 1,
        "tempo_s": 600,  # 10 minutos
        "xp_concedido": 10,
        "loot_table": [
            {"template_id": "madeira_comum", "chance_base": 1.0, "quantidade": (5, 10)},
            {"template_id": "seiva_arvore", "chance_base": 0.2, "quantidade": (1, 2)}
        ]
    },
    # NÍVEL 2 DE CONSTRUÇÃO
    "bosque_antigo": {
        "nome": "Bosque Antigo",
        "nivel_minimo_edificio": 6,
        "nivel_lenhador": 5,
        "nivel_machado": 2,
        "tempo_s": 3600,  # 1 hora
        "xp_concedido": 75,
        "loot_table": [
            {"template_id": "madeira_carvalho", "chance_base": 0.75, "quantidade": (2, 5)},
            {"template_id": "fruta_silvestre", "chance_base": 0.50, "quantidade": (2, 4)},
        ]
    },
    # Adicione mais locais conforme sua necessidade
}