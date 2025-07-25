# data/habilidades_library.py

HABILIDADES = {
    # --- HABILIDADES DE GUERREIRO ---
    "GRR_001": {
        "nome": "Golpe Poderoso", "emoji": "⚔️", "tipo": "ATIVA",
        "custo_mana": 15,
        "usos_por_batalha": None, # Usos ilimitados
        "descricao": "Um ataque concentrado que causa dano físico extra.",
        "efeitos": {"DANO": 30}
    },
    "GRR_002": {
        "nome": "Bloqueio com Escudo", "emoji": "🛡️", "tipo": "ATIVA",
        "custo_mana": 20,
        "usos_por_batalha": 3, # Pode usar 3 vezes por batalha
        "descricao": "Aumenta sua defesa por um curto período.",
        "efeitos": {"DEFESA_BUFF": 50, "DURACAO": 2}
    },
    # Exemplo de Habilidade Passiva
    "GRR_003": {
        "nome": "Vitalidade do Combatente", "emoji": "💪", "tipo": "PASSIVA",
        "descricao": "+50❤️ Passivo",
        "efeitos": {"VIDA_MAXIMA": 50} # Efeito permanente
    },

    # --- HABILIDADES DE MAGO ---
    "MAG_001": {
        "nome": "Bola de Fogo", "emoji": "🔥", "tipo": "ATIVA",
        "custo_mana": 25,
        "usos_por_batalha": None,
        "descricao": "Lança uma esfera de fogo que causa dano em um alvo.",
        "efeitos": {"DANO_MAGICO": 45}
    },
    "MAG_002": {
        "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
        "custo_mana": 15,
        "usos_por_batalha": None,
        "descricao": "Dispara um raio de gelo que pode deixar o inimigo lento.",
        "efeitos": {"DANO_MAGICO": 20, "LENTIDAO": 1}
    },
    # Habilidade Ultimate com uso limitado
    "MAG_003": {
        "nome": "Meteoro", "emoji": "☄️", "tipo": "ATIVA",
        "custo_mana": 100,
        "usos_por_batalha": 1, # Só pode usar uma vez!
        "descricao": "Invoca um meteoro que causa dano massivo em área.",
        "efeitos": {"DANO_MAGICO": 200}
    },
    # Exemplo de Passiva de Mago
    "MAG_P01": {
        "nome": "Inteligência Arcana", "emoji": "🧠", "tipo": "PASSIVA",
        "descricao": "Seu intelecto superior aumenta sua mana máxima permanentemente.",
        "efeitos": {"MANA_MAXIMA": 75} # Novo status que vamos criar
    },

    # --- Exemplo de Habilidade de Cura ---
    "CUR_001": {
        "nome": "Toque Curativo", "emoji": "💖", "tipo": "ATIVA",
        "descricao": "Restaura pontos de vida de um alvo.",
        "efeitos": {
            "CURA": 75 # Restaura 75 de HP
        }
    },
}