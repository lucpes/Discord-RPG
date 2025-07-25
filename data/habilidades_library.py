# data/habilidades_library.py

HABILIDADES = {
    # --- HABILIDADES DE GUERREIRO ---
    "GRR_001": {
        "nome": "Golpe Poderoso", "emoji": "⚔️", "tipo": "ATIVA",
        "custo_mana": 15,
        "descricao": "Um ataque concentrado que causa dano físico extra.",
        "efeitos": {"DANO": 30}
    },
    "GRR_002": {
        "nome": "Bloqueio com Escudo", "emoji": "🛡️", "tipo": "ATIVA",
        "custo_mana": 20,
        "descricao": "Aumenta sua defesa por um curto período.",
        "efeitos": {"DEFESA_BUFF": 50, "DURACAO": 2}
    },
    # Exemplo de Habilidade Passiva
    "GRR_003": {
        "nome": "Vitalidade do Combatente", "emoji": "💪", "tipo": "PASSIVA",
        "descricao": "+50❤️ Passivo",
        "efeitos": {"VIDA_MAXIMA": 50} # Efeito permanente
    },
    "GRR_004": {
        "nome": "Teste de mana", "emoji": "🛡️", "tipo": "ATIVA",
        "descricao": "Aumenta sua defesa por um curto período.",
        "efeitos": {"MANA_MAXIMA": 100}
    },

    # --- HABILIDADES DE MAGO ---
    "MAG_001": {
        "nome": "Bola de Fogo", "emoji": "🔥", "tipo": "ATIVA",
        "custo_mana": 25,
        "descricao": "Lança uma esfera de fogo que causa dano em um alvo.",
        "efeitos": {"DANO_MAGICO": 45}
    },
    "MAG_002": {
        "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
        "custo_mana": 15,
        "descricao": "Dispara um raio de gelo que pode deixar o inimigo lento.",
        "efeitos": {"DANO_MAGICO": 20, "LENTIDAO": 1}
    },
    # Habilidade Ultimate com uso limitado
    "MAG_003": {
        "nome": "Meteoro", "emoji": "☄️", "tipo": "ATIVA",
        "custo_mana": 100,
        "descricao": "Invoca um meteoro que causa dano massivo em área.",
        "efeitos": {"DANO_MAGICO": 200}
    },
    # --- ATUALIZANDO HABILIDADE DE MAGO ---
    "MAG_002": {
        "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
        "custo_mana": 30,
        "descricao": "Dispara um raio de gelo que causa dano e pode congelar o inimigo por um turno.",
        "efeitos": {
            "DANO_MAGICO": 20,
            "CONGELAMENTO": { # Efeito de status
                "duracao": 1
            }
        }
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


"""
HABILIDADES = {
    # ... (habilidades existentes)
    
    # --- HABILIDADES DE ASSASSINO (Exemplo) ---
    "LAMINA_VENENOSA": {
        "nome": "Lâmina Venenosa", "emoji": "☠️", "tipo": "ATIVA",
        "custo_mana": 25,
        "descricao": "Um ataque rápido que aplica veneno no alvo, causando dano por vários turnos.",
        "efeitos": {
            "DANO": 10, # Dano inicial do golpe
            "ENVENENAMENTO": { # Efeito de status
                "dano": 8,
                "duracao": 3
            }
        }
    },
    
    # --- ATUALIZANDO HABILIDADE DE MAGO ---
    "MAG_002": {
        "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
        "custo_mana": 30,
        "descricao": "Dispara um raio de gelo que causa dano e pode congelar o inimigo por um turno.",
        "efeitos": {
            "DANO_MAGICO": 20,
            "CONGELAMENTO": { # Efeito de status
                "duracao": 1
            }
        }
    },
    # ...
}
"""