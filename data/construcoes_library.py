# data/construcoes_library.py

# A chave é o ID da construção, que será usado no Firebase
CONSTRUCOES = {
    "CENTRO_VILA": {
        "nome": "Centro da Vila", "emoji": "🏛️",
        "descricao": "O coração da cidade. Seu nível determina o nível máximo das outras construções.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MERCADO": {
        "nome": "Mercado",
        "emoji": "⚖️",
        "descricao": "Um lugar para comprar e vender itens com NPCs ou outros jogadores.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "FORJA": {
        "nome": "Forja",
        "emoji": "🔨",
        "descricao": "Permite criar e aprimorar armas e armaduras.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MESA_TRABALHO": {
        "nome": "Mesa de Trabalho",
        "emoji": "🛠️",
        "descricao": "Usada para criar itens diversos e acessórios.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MESA_POCOES": {
        "nome": "Mesa de Poções",
        "emoji": "⚗️",
        "descricao": "Onde alquimistas podem criar poções e elixires.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 120},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 240},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "MINA": {
        "nome": "Mina",
        "emoji": "⛏️",
        "descricao": "Fonte de minérios e pedras preciosas. Níveis mais altos liberam recursos mais raros.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "FLORESTA": {
        "nome": "Floresta Mística",
        "emoji": "🌳",
        "descricao": "Fonte de madeira, ervas e outros recursos naturais.",
        "niveis": [
            {"custo": {"MOEDAS": 1000}, "tempo_s": 3600},      # Custo para ir do Nível 1 -> 2 (1 hora)
            {"custo": {"MOEDAS": 5000}, "tempo_s": 14400},     # Custo para ir do Nível 2 -> 3 (4 horas)
            # Adicione mais níveis conforme necessário
        ]
    },
    "LOJA": {
        "nome": "Loja de Utilidades",
        "emoji": "🏪",
        "descricao": "Uma loja geral que vende itens básicos para aventureiros."
    },
    "TAVERNA": {
        "nome": "Taverna",
        "emoji": "🍺",
        "descricao": "Um lugar para descansar, socializar e pegar novas quests."
    },
    "BANCO": {
        "nome": "Banco",
        "emoji": "🏦",
        "descricao": "Guarde seus itens e moedas com segurança. Níveis mais altos aumentam a capacidade."
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
        "descricao": "Gera uma renda passiva de moedas para o tesouro da cidade.",
        "niveis": [
            {"custo": {"MOEDAS": 2000}, "tempo_s": 1800, "renda_por_hora": 50},
            {"custo": {"MOEDAS": 8000}, "tempo_s": 7200, "renda_por_hora": 120},
        ]
    },
    "FORNALHA": {
        "nome": "Fornalha", "emoji": "🔥",
        "categoria": "CRIACAO",
        "descricao": "Permite refinar materiais brutos, como minérios, em barras de metal prontas para a forja.",
        "niveis": [
            {"custo": {"MOEDAS": 1500}, "tempo_s": 2700},
            {"custo": {"MOEDAS": 6000}, "tempo_s": 10800},
        ]
    },
    "MESA_ENCANTAMENTO": {
        "nome": "Mesa de Encantamento", "emoji": "✨",
        "categoria": "SERVICOS",
        "descricao": "Onde magos e artesãos podem imbuir equipamentos com poderes mágicos.",
        "niveis": [
            {"custo": {"MOEDAS": 10000}, "tempo_s": 21600},
            {"custo": {"MOEDAS": 50000}, "tempo_s": 86400},
        ]
    },
}