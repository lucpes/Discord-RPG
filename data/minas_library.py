# data/minas_library.py

MINAS = {
    # =============================================================================
    # NÍVEL 1 DE CONSTRUÇÃO
    # =============================================================================
    "afloramento_rochoso": {
        "nome": "Afloramento Rochoso",
        "nivel_minimo_edificio": 1,
        "nivel_minerador": 1,
        "nivel_picareta": 1,
        "tempo_s": 600,  # 10 minutos
        "xp_concedido": 10,
        "loot_table": [
            {"template_id": "pedra_bruta", "chance_base": 1.0, "quantidade": (5, 10)},
            {"template_id": "carvao", "chance_base": 0.3, "quantidade": (1, 3)}
        ]
    },
    "veio_cobre": {
        "nome": "Veio de Cobre",
        "nivel_minimo_edificio": 1,
        "nivel_minerador": 2,
        "nivel_picareta": 1,
        "tempo_s": 1800,  # 30 minutos
        "xp_concedido": 25,
        "loot_table": [
            {"template_id": "minerio_cobre", "chance_base": 0.80, "quantidade": (2, 4)},
            {"template_id": "pedra_bruta", "chance_base": 0.5, "quantidade": (3, 6)}
        ]
    },

    # =============================================================================
    # NÍVEL 2 DE CONSTRUÇÃO
    # =============================================================================
    "deposito_ferro": {
        "nome": "Depósito de Ferro",
        "nivel_minimo_edificio": 2,
        "nivel_minerador": 5,
        "nivel_picareta": 2,
        "tempo_s": 3600,  # 1 hora
        "xp_concedido": 75,
        "loot_table": [
            {"template_id": "minerio_ferro", "chance_base": 0.75, "quantidade": (2, 5)},
            {"template_id": "carvao", "chance_base": 0.50, "quantidade": (2, 4)},
            {"template_id": "gema_simples", "chance_base": 0.05, "quantidade": (1, 1)}
        ]
    },

    # =============================================================================
    # NÍVEL 3 DE CONSTRUÇÃO
    # =============================================================================
    "filao_prata": {
        "nome": "Filão de Prata",
        "nivel_minimo_edificio": 3,
        "nivel_minerador": 10,
        "nivel_picareta": 3,
        "tempo_s": 7200,  # 2 horas
        "xp_concedido": 150,
        "loot_table": [
            {"template_id": "minerio_prata", "chance_base": 0.60, "quantidade": (2, 4)},
            {"template_id": "minerio_ferro", "chance_base": 0.2, "quantidade": (1, 3)}
        ]
    },
    "caverna_cristais": {
        "nome": "Caverna de Cristais",
        "nivel_minimo_edificio": 3,
        "nivel_minerador": 12,
        "nivel_picareta": 3,
        "tempo_s": 10800,  # 3 horas
        "xp_concedido": 200,
        "loot_table": [
            {"template_id": "fragmento_cristalino", "chance_base": 0.8, "quantidade": (3, 6)},
            {"template_id": "gema_simples", "chance_base": 0.5, "quantidade": (1, 3)},
            {"template_id": "gema_rara", "chance_base": 0.1, "quantidade": (1, 1)}
        ]
    },

    # =============================================================================
    # NÍVEL 4 DE CONSTRUÇÃO
    # =============================================================================
    "veio_ouro": {
        "nome": "Veio de Ouro",
        "nivel_minimo_edificio": 4,
        "nivel_minerador": 18,
        "nivel_picareta": 4,
        "tempo_s": 21600,  # 6 horas
        "xp_concedido": 400,
        "loot_table": [
            {"template_id": "minerio_ouro", "chance_base": 0.5, "quantidade": (1, 3)},
            {"template_id": "gema_rara", "chance_base": 0.08, "quantidade": (1, 1)}
        ]
    },
    "mina_ana_abandonada": {
        "nome": "Mina Anã Abandonada",
        "nivel_minimo_edificio": 4,
        "nivel_minerador": 25,
        "nivel_picareta": 5,
        "tempo_s": 43200,  # 12 horas
        "xp_concedido": 800,
        "loot_table": [
            {"template_id": "minerio_mithril", "chance_base": 0.2, "quantidade": (1, 2)},
            {"template_id": "minerio_ferro", "chance_base": 0.8, "quantidade": (10, 20)},
            {"template_id": "carvao", "chance_base": 1.0, "quantidade": (15, 30)}
        ]
    },

    # =============================================================================
    # NÍVEL 5 DE CONSTRUÇÃO
    # =============================================================================
    "geodo_gigante": {
        "nome": "Geodo Gigante",
        "nivel_minimo_edificio": 5,
        "nivel_minerador": 35,
        "nivel_picareta": 5,
        "tempo_s": 86400,  # 24 horas
        "xp_concedido": 1500,
        "loot_table": [
            {"template_id": "gema_rara", "chance_base": 0.7, "quantidade": (2, 4)},
            {"template_id": "gema_epica", "chance_base": 0.15, "quantidade": (1, 1)}
        ]
    },
    
    # =============================================================================
    # NÍVEL 6 DE CONSTRUÇÃO
    # =============================================================================
    "fenda_vulcanica": {
        "nome": "Fenda Vulcânica",
        "nivel_minimo_edificio": 6,
        "nivel_minerador": 50,
        "nivel_picareta": 6,
        "tempo_s": 172800,  # 48 horas
        "xp_concedido": 3000,
        "loot_table": [
            {"template_id": "minerio_obsidiana", "chance_base": 0.4, "quantidade": (1, 3)},
            {"template_id": "essencia_fogo", "chance_base": 0.2, "quantidade": (1, 2)}
        ]
    }
}