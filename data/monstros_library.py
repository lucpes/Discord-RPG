# data/monstros_library.py

MONSTROS = {
    # O ID do monstro (a chave) é único
    "goblin_fraco": {
        "nome": "Goblin Fraco",
        "emoji": "👺",
        "imagem_url": "https://i.pinimg.com/736x/47/e7/29/47e7299bf52940434ffa46f2334b4110.jpg",
        "nivel": 1,
        "stats": {
            "VIDA_MAXIMA": 30,
            "DANO": 8,
            "ARMADURA": 2
        },
        "xp_recompensa": 15,
        "loot_table": [
            # Um item pode ter uma chance de dropar
            {"item_template_id": "adaga_enferrujada", "chance": 0.5}, # 50% de chance
            # Outro item pode ter quantidade variável
            {"item_template_id": "moeda_cobre", "chance": 0.9, "quantidade": (1, 5)} # 90% de chance de dropar de 1 a 5 moedas
        ]
    },
    "lobo_floresta": {
        "nome": "Lobo da Floresta",
        "emoji": "🐺",
        "imagem_url": "https://i.pinimg.com/736x/47/e7/29/47e7299bf52940434ffa46f2334b4110.jpg",
        "nivel": 2,
        "stats": {
            "VIDA_MAXIMA": 50,
            "DANO": 12,
            "ARMADURA": 5
        },
        "xp_recompensa": 25,
        "loot_table": [
            {"item_template_id": "pele_de_lobo", "chance": 0.7},      # 70% de chance
            {"item_template_id": "dente_de_lobo", "chance": 0.25}     # 25% de chance
        ]
    },
    "slime_verde": {
        "nome": "Slime Verde",
        "emoji": "🟢",
        "imagem_url": "https://i.pinimg.com/736x/47/e7/29/47e7299bf52940434ffa46f2334b4110.jpg",
        "nivel": 1,
        "stats": {
            "VIDA_MAXIMA": 25,
            "DANO": 5,
            "ARMADURA": 10 # Alta armadura, mas baixo dano/vida
        },
        "xp_recompensa": 10,
        "loot_table": [
            {"item_template_id": "gosma_verde", "chance": 1.0, "quantidade": (1, 2)} # Sempre dropa (100%)
        ]
    },
    "esqueleto_guerreiro": {
        "nome": "Esqueleto Guerreiro",
        "emoji": "💀",
        "imagem_url": "https://i.pinimg.com/736x/47/e7/29/47e7299bf52940434ffa46f2334b4110.jpg",
        "nivel": 3,
        "stats": {
            "VIDA_MAXIMA": 60,
            "DANO": 15,
            "ARMADURA": 12
        },
        "xp_recompensa": 40,
        "loot_table": [
            {"item_template_id": "espada_ferro_comum", "chance": 0.1}, # 10% de chance
            {"item_template_id": "fragmento_osso", "chance": 0.8}
        ]
    }
}