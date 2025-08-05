# data/minas_library.py

MINAS = {
    "veio_cobre": {
        "nome": "Veio de Cobre",
        "nivel_minimo_edificio": 1,
        "nivel_picareta": 1,
        "tempo_s": 3600, # 1 hora
        "loot_table": [
            {"template_id": "minerio_cobre", "chance_base": 0.80, "quantidade": (1, 3)},
            {"template_id": "pedra_bruta", "chance_base": 1.0, "quantidade": (2, 5)}
        ]
    },
    "deposito_ferro": {
        "nome": "Depósito de Ferro",
        "nivel_minimo_edificio": 3,
        "nivel_picareta": 2,
        "tempo_s": 30, # 4 horas   14400
        "loot_table": [
            {"template_id": "minerio_ferro", "chance_base": 0.75, "quantidade": (1, 4)},
            #{"template_id": "carvao", "chance_base": 0.90, "quantidade": (3, 8)}
        ]
    },
    "geodo_cristalino": {
        "nome": "Geodo Cristalino",
        "nivel_minimo_edificio": 5,
        "nivel_picareta": 3,
        "tempo_s": 43200, # 12 horas
        "loot_table": [
            {"template_id": "fragmento_cristal", "chance_base": 0.60, "quantidade": (1, 2)},
            {"template_id": "gema_rara", "chance_base": 0.15, "quantidade": (1, 1)}
        ]
    }
}