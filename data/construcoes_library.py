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
}