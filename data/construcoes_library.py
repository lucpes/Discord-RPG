# data/construcoes_library.py

# A chave é o ID da construção, que será usado no Firebase
CONSTRUCOES = {
    "CENTRO_VILA": {
        "nome": "Centro da Vila", "emoji": "🏛️",
        "descricao": "O coração da cidade. Seu nível determina o nível máximo das outras construções.",
        "niveis": [
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MERCADO": {
        "nome": "Mercado",
        "emoji": "⚖️",
        "categoria": "SERVICOS",
        "descricao": "Um lugar para comprar e vender itens com NPCs ou outros jogadores.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "FORNALHA": {
        "nome": "Fornalha", "emoji": "🔥",
        "categoria": "CRIACAO",
        "descricao": "Permite refinar materiais brutos, como minérios, em barras de metal prontas para a forja.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "FORJA": {
        "nome": "Forja",
        "emoji": "🔨",
        "categoria": "CRIACAO",
        "descricao": "Permite criar e aprimorar armas e armaduras.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MESA_TRABALHO": {
        "nome": "Mesa de Trabalho",
        "emoji": "🛠️",
        "categoria": "CRIACAO",
        "descricao": "Usada para criar itens diversos e acessórios.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MESA_POCOES": {
        "nome": "Mesa de Poções",
        "emoji": "⚗️",
        "categoria": "CRIACAO",
        "descricao": "Onde alquimistas podem criar poções e elixires.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MINA": {
        "nome": "Mina",
        "emoji": "⛏️",
        "categoria": "RECURSOS",
        "descricao": "Fonte de minérios e pedras preciosas. Níveis mais altos liberam recursos mais raros.",
        "niveis": [
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "FLORESTA": {
        "nome": "Floresta Mística",
        "emoji": "🌳",
        "categoria": "RECURSOS",
        "descricao": "Fonte de madeira, ervas e outros recursos naturais.",
        "niveis": [
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "LOJA": {
        "nome": "Loja de Utilidades",
        "emoji": "🏪",
        "categoria": "SERVICOS",
        "descricao": "Uma loja geral que vende itens básicos para aventureiros.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "TAVERNA": {
        "nome": "Taverna",
        "emoji": "🍺",
        "categoria": "SERVICOS",
        "descricao": "Um lugar para descansar, socializar e pegar novas quests."
    },
    "BANCO": {
        "nome": "Banco",
        "categoria": "SERVICOS",
        "emoji": "🏦",
        "descricao": "Guarde seus itens e moedas com segurança. Níveis mais altos aumentam a capacidade.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
    "PORTAL_ABISSAL": {
        "nome": "Portal Abissal", "emoji": "🌀",
        "categoria": "RECURSOS",
        "descricao": "Uma fenda instável para outras dimensões. Níveis mais altos permitem o acesso a tiers de maior perigo e recompensa.",
        "niveis": [
            # Custo para ir do Nível 0 -> 1 (construir)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 7200, "frequencia_h": 6, "duracao_min": 30},
            # Custo para ir do Nível 1 -> 2
            {"custo": {"MOEDAS": 25000}, "tempo_s": 14400, "frequencia_h": 5, "duracao_min": 35},
            # Custo para ir do Nível 2 -> 3
            {"custo": {"MOEDAS": 75000}, "tempo_s": 28800, "frequencia_h": 4, "duracao_min": 40},
        ]
    },
    "FAZENDA": {
        "nome": "Fazenda", "emoji": "🧑‍🌾",
        "categoria": "RECURSOS",
        "descricao": "Gera uma renda passiva de moedas para o tesouro da cidade, coletada diariamente.",
        "niveis": [
            # Nível 1: Renda de 20/dia. Custa 400 para upar (20 dias para pagar).
            {"custo": {"MOEDAS": 400}, "tempo_s": 1800, "renda": 5},
            
            # Nível 2: Renda de 50/dia. Custa 1200 para upar (24 dias para pagar).
            {"custo": {"MOEDAS": 1200}, "tempo_s": 7200, "renda": 10},
            
            # Nível 3: Renda de 120/dia. Custa 3000 para upar (25 dias para pagar).
            {"custo": {"MOEDAS": 3000}, "tempo_s": 21600, "renda": 20},
            
            # Nível 4: Renda de 300/dia. Custa 8000 para upar (aprox. 27 dias para pagar).
            {"custo": {"MOEDAS": 8000}, "tempo_s": 43200, "renda": 40},
            
            # Nível 5: Renda de 800/dia. Custa 20000 para upar (25 dias para pagar).
            {"custo": {"MOEDAS": 20000}, "tempo_s": 86400, "renda": 80},
            
            # Nível 6 (Máximo): Renda final de 2000/dia.
            {"custo": {}, "tempo_s": 0, "renda": 100},
        ]
    },
    "MESA_ENCANTAMENTO": {
        "nome": "Mesa de Encantamento", "emoji": "✨",
        "categoria": "CRIACAO",
        "descricao": "Onde magos e artesãos podem imbuir equipamentos com poderes mágicos.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 43200},      # Custo para ir do Nível 0 -> 1 (12 horas)
            {"custo": {"MOEDAS": 2000}, "tempo_s": 43200},      # Custo para ir do Nível 1 -> 2 (12 horas)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 86400},      # Custo para ir do Nível 2 -> 3 (1 dia)
            {"custo": {"MOEDAS": 10000}, "tempo_s": 172800},    # Custo para ir do Nível 3 -> 4 (2 dias)
            {"custo": {"MOEDAS": 25000}, "tempo_s": 259200},    # Custo para ir do Nível 4 -> 5 (3 dias)
            {"custo": {"MOEDAS": 100000}, "tempo_s": 518400},   # Custo para ir do Nível 5 -> 6 (6 dias)
            # Adicione mais níveis conforme necessário
        ]
    },
}