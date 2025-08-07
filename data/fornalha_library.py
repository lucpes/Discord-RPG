# data/fornalha_library.py

FORNALHA_RECIPES = {
    "barra_ferro": {
        "nome": "Barra de Ferro",
        "nivel_fornalha": 1, # Nível do edifício da cidade
        "nivel_ferreiro": 1, # Nível da profissão do jogador
        "tempo_s": 30, # 30 minutos  1800
        "xp_concedido": 25, # XP para a profissão de Ferreiro
        "item_criado_template_id": "barra_ferro", # O ID do item final em item_templates
        "quantidade_criada": 1,
        "ingredientes": [
            {"template_id": "minerio_ferro", "quantidade": 10},
            {"template_id": "carvao", "quantidade": 5} # Carvão como combustível
        ]
    },
    "barra_aco": {
        "nome": "Barra de Aço",
        "nivel_fornalha": 3,
        "nivel_ferreiro": 5,
        "tempo_s": 3600, # 1 hora
        "xp_concedido": 100,
        "item_criado_template_id": "barra_aco",
        "quantidade_criada": 1,
        "ingredientes": [
            {"template_id": "barra_ferro", "quantidade": 2},
            {"template_id": "carvao", "quantidade": 10}
        ]
    },
}

# Cria uma lista ordenada de IDs para a navegação
ORDERED_FORNALHA_RECIPES = list(FORNALHA_RECIPES.keys())