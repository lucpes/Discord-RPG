# data/mural_library.py

CONTRATOS = {
    "lobo_floresta": {
        "nome": "Lobo Cinzento",
        "monstro_id": "lobo_floresta", # ID do monstro em monstros_library.py
        "nivel_requerido": 1,
        "cooldown_s": 300, # 5 minutos de tempo de espera
        "recompensas_extras": {
            "moedas": 20,
            "xp": 15
        }
        # Custo não definido, então este contrato é GRÁTIS.
    },
    "c_goblin_ladrao": {
        "nome": "Goblin Ladrão",
        "monstro_id": "goblin_ladrao",
        "nivel_requerido": 3,
        "cooldown_s": 600, # 10 minutos
        "custo": 10, # Custa 10 moedas para aceitar
        "recompensas_extras": {
            "moedas": 50,
            "xp": 40
        }
    },
    "c_urso_furioso": {
        "nome": "Urso Furioso",
        "monstro_id": "urso_pardo",
        "nivel_requerido": 8,
        "cooldown_s": 1800, # 30 minutos
        "recompensas_extras": {
            "moedas": 150,
            "xp": 100
        }
    },
    # Adicione mais contratos aqui...
}