# data/monstros_library.py

MONSTROS = {
    # O ID do monstro (a chave) é único
    "goblin_fraco": {
        "nome": "Goblin Fraco",
        "emoji": "👺",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 1,
        "stats": {
            "VIDA_MAXIMA": 30,
            "DANO": 8,
            "ARMADURA": 2
        },
        "xp_recompensa": 15,
        "moedas_recompensa": {"min": 5, "max": 20}, # Sorteia um valor entre 5 e 20 moedas
        "loot_table": [
            # Um item pode ter uma chance de dropar
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            # Outro item pode ter quantidade variável
            #{"item_template_id": "moeda_cobre", "chance": 0.9, "quantidade": (1, 5)} # 90% de chance de dropar de 1 a 5 moedas
        ]
    },
    "goblin_fraco2": {
        "nome": "Goblin Bombado",
        "emoji": "👺",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 1,
        "stats": {
            "VIDA_MAXIMA": 100,
            "DANO": 5,
            "ARMADURA": 10
        },
        "xp_recompensa": 15,
        "moedas_recompensa": {"min": 5, "max": 20}, # Sorteia um valor entre 5 e 20 moedas
        "loot_table": [
            # Um item pode ter uma chance de dropar
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            # Outro item pode ter quantidade variável
            #{"item_template_id": "moeda_cobre", "chance": 0.9, "quantidade": (1, 5)} # 90% de chance de dropar de 1 a 5 moedas
        ]
    },
    "lobo_floresta": {
        "nome": "Lobo da Floresta",
        "emoji": "🐺",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 2,
        "stats": {
            "VIDA_MAXIMA": 50,
            "DANO": 12,
            "ARMADURA": 5
        },
        "xp_recompensa": 25,
        "loot_table": [
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "pele_de_lobo", "chance": 0.7},      # 70% de chance
            #{"item_template_id": "dente_de_lobo", "chance": 0.25}     # 25% de chance
        ],
        "moedas_recompensa": {"min": 10, "max": 30}
    },
    "slime_verde": {
        "nome": "Slime Verde",
        "emoji": "🟢",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 1,
        "stats": {
            "VIDA_MAXIMA": 25,
            "DANO": 5,
            "ARMADURA": 10 # Alta armadura, mas baixo dano/vida
        },
        "xp_recompensa": 10,
        "moedas_recompensa": {"min": 5, "max": 20}, # Sorteia um valor entre 5 e 20 moedas
        "loot_table": [
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "gosma_verde", "chance": 1.0, "quantidade": (1, 2)} # Sempre dropa (100%)
        ]
    },
    "esqueleto_guerreiro": {
        "nome": "Esqueleto Guerreiro",
        "emoji": "💀",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 3,
        "stats": {
            "VIDA_MAXIMA": 60,
            "DANO": 15,
            "ARMADURA": 12
        },
        "xp_recompensa": 40,
        "loot_table": [
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "espada_ferro_comum", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "fragmento_osso", "chance": 0.8}
        ],
        "moedas_recompensa": {"min": 10, "max": 30}
    },
    "thanos": {
        "nome": "Thanos",
        "emoji": "💀",
        "imagem_url": "https://i.imgur.com/83be9K2.png",
        "nivel": 99999,
        "stats": {
            "VIDA_MAXIMA": 9999999,
            "DANO": 999999,
            "ARMADURA": 9999999
        },
        "xp_recompensa": 40,
        "loot_table": [
            {"item_template_id": "adaga_agil", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "espada_ferro_comum", "chance": 0.1}, # 10% de chance
            #{"item_template_id": "fragmento_osso", "chance": 0.8}
        ],
        "moedas_recompensa": {"min": 10, "max": 30}
    }
}