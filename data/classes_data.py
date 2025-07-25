# data/classes_data.py

CLASSES_DATA = {
    "Guerreiro": {
        "estilo": "...",
        "evolucoes": ["..."],
        #"image_url": "https://i.imgur.com/VYXEo2n.jpeg",
        "image_url": "https://i.imgur.com/55VuduV.png",
        "habilidades_iniciais": ["GRR_001", "GRR_002", "GRR_003"],
        "stats_base": {
            "VIDA_MAXIMA": 120,
            "MANA_MAXIMA": 80,
            "DANO": 10,
            "ARMADURA": 15
        }
    },
    "Mago": {
        "estilo": "...",
        "evolucoes": ["..."],
        "image_url": "...",
        "habilidades_iniciais": ["MAG_001", "MAG_002", "MAG_003"],
        "stats_base": {
            "VIDA_MAXIMA": 90,
            "MANA_MAXIMA": 150,
            "DANO": 5,
            "DANO_MAGICO": 15, # Mago começa com dano mágico
            "ARMADURA": 5
        }
    },
    "Arqueira": {
        "estilo": "...",
        "evolucoes": ["..."],
        "image_url": "...",
        "habilidades_iniciais": ["ARQ_001", "ARQ_002", "ARQ_003"],
        "stats_base": {
            "VIDA_MAXIMA": 100,
            "MANA_MAXIMA": 100,
            "DANO": 12,
            "ARMADURA": 8
        }
    },
    # Adicione stats_base para as outras classes...
}

ORDERED_CLASSES = list(CLASSES_DATA.keys())