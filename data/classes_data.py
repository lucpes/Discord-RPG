# data/classes_data.py

CLASSES_DATA = {
    "Guerreiro": {
        "estilo": "Combatente corpo a corpo robusto, mestre em defesa e ataque com armas pesadas.",
        "evolucoes": ["Paladino", "Berserker"],
        "image_url": "https://i.imgur.com/vV42M5I.jpeg",
        # Apenas os IDs das habilidades iniciais
        "habilidades_iniciais": ["GRR_001", "GRR_002", "GRR_003"]
    },
    "Mago": {
        "estilo": "Conjurador de poderosas magias arcanas que manipulam os elementos para causar dano em área.",
        "evolucoes": ["Arquimago", "Bruxo"],
        "image_url": "https://i.imgur.com/mN23a27.jpeg",
        "habilidades_iniciais": ["MAG_001", "MAG_002", "MAG_003"]
    },
    "Arqueira": {
        "estilo": "Atiradora de longa distância, ágil e precisa, que domina o campo de batalha de longe.",
        "evolucoes": ["Caçadora de Feras", "Sombra Silenciosa"],
        "image_url": "https://i.imgur.com/TCoT15S.jpeg",
        "habilidades_iniciais": ["ARQ_001", "ARQ_002", "ARQ_003"]
    },
    # Adicione as outras classes aqui. Se deixar 'habilidades_iniciais' vazio, o personagem começará sem habilidades.
    "Anão": {
        "estilo": "Resistente e forte, especialista em forja e combate com machados e martelos.",
        "evolucoes": ["Guardião da Montanha", "Mestre das Runas"],
        "image_url": "https://i.imgur.com/m5w2p3h.jpeg",
        "habilidades_iniciais": [] 
    },
}

ORDERED_CLASSES = list(CLASSES_DATA.keys())