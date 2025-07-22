# --- DADOS DAS CLASSES (Nossos "Templates") ---
# Mapeamento de nome de classe para seus dados para acesso rápido
CLASSES_DATA = {
    "Guerreiro": {
        "estilo": "Combatente corpo a corpo robusto, mestre em defesa e ataque com armas pesadas.",
        "evolucoes": ["Paladino", "Berserker"],
        "habilidades": ["Golpe Poderoso", "Bloqueio com Escudo", "Grito de Guerra"],
        "image_url": "https://i.imgur.com/vV42M5I.jpeg"
    },
    "Anão": {
        "estilo": "Resistente e forte, especialista em forja e combate com machados e martelos.",
        "evolucoes": ["Guardião da Montanha", "Mestre das Runas"],
        "habilidades": ["Golpe de Martelo", "Pele de Pedra", "Arremesso de Machado"],
        "image_url": "https://i.imgur.com/m5w2p3h.jpeg"
    },
    "Arqueira": {
        "estilo": "Atiradora de longa distância, ágil e precisa, que domina o campo de batalha de longe.",
        "evolucoes": ["Caçadora de Feras", "Sombra Silenciosa"],
        "habilidades": ["Flecha Precisa", "Chuva de Flechas", "Salto para Trás"],
        "image_url": "https://i.imgur.com/TCoT15S.jpeg"
    },
    "Mago": {
        "estilo": "Conjurador de poderosas magias arcanas que manipulam os elementos para causar dano em área.",
        "evolucoes": ["Arquimago", "Bruxo"],
        "habilidades": ["Bola de Fogo", "Raio Congelante", "Barreira Mágica"],
        "image_url": "https://i.imgur.com/mN23a27.jpeg"
    },
    "Curadora": {
        "estilo": "Suporte vital para qualquer grupo, capaz de curar ferimentos e conceder bênçãos divinas.",
        "evolucoes": ["Sacerdotisa", "Druida"],
        "habilidades": ["Toque Curativo", "Bênção de Proteção", "Luz Sagrada"],
        "image_url": "https://i.imgur.com/2e2xG0N.jpeg"
    },
    "Assassino": {
        "estilo": "Mestre da furtividade e dos golpes críticos, que elimina alvos importantes rapidamente.",
        "evolucoes": ["Ladrão das Sombras", "Duelista"],
        "habilidades": ["Ataque Furtivo", "Lançar Adaga Envenenada", "Desaparecer"],
        "image_url": "https://i.imgur.com/jHhC5jH.jpeg"
    },
    "Goblin": {
        "estilo": "Engenhoso e caótico, usa truques sujos e invenções instáveis para superar os inimigos.",
        "evolucoes": ["Engenhoqueiro", "Trapaceiro"],
        "habilidades": ["Bomba Improvisada", "Golpe Baixo", "Fingir de Morto"],
        "image_url": "https://i.imgur.com/Yv6Qd2Y.jpeg"
    },
}
# Lista de nomes de classes para navegação ordenada
ORDERED_CLASSES = list(CLASSES_DATA.keys())