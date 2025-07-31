# data/habilidades_library.py

HABILIDADES = {
    # --- HABILIDADES DE GUERREIRO ---
    "GRR_001": {
        "nome": "Golpe Poderoso", "emoji": "⚔️", "tipo": "ATIVA",
        "custo_mana": 15,
        "descricao": "Um ataque concentrado que causa dano físico extra.",
        "efeitos": {"DANO": 30},
        "alvo": "inimigo"
    },
    "GRR_002": {
        "nome": "Bloqueio com Escudo", "emoji": "🛡️", "tipo": "ATIVA",
        "custo_mana": 20,
        "descricao": "Aumenta sua defesa por um curto período.",
        "efeitos": {"DEFESA_BUFF": 50, "DURACAO": 2},
        "alvo": "grupo_aliado"
    },
    # Exemplo de Habilidade Passiva
    "GRR_003": {
        "nome": "Vitalidade do Combatente", "emoji": "💪", "tipo": "PASSIVA",
        "descricao": "+50❤️ Passivo",
        "efeitos": {"VIDA_MAXIMA": 50}, # Efeito permanente
        "alvo": "passivo"
    },
    "GRR_004": {
        "nome": "Teste de mana", "emoji": "🛡️", "tipo": "ATIVA",
        "descricao": "Aumenta sua defesa por um curto período.",
        "efeitos": {"MANA_MAXIMA": 100},
        "alvo": "self"
    },

    # --- HABILIDADES DE MAGO ---
    "MAG_001": {
        "nome": "Bola de Fogo", "emoji": "🔥", "tipo": "ATIVA",
        "custo_mana": 10,
        "descricao": "Lança uma esfera de fogo que causa dano em um alvo.",
        "efeitos": {"DANO_MAGICO": 45},
        "alvo": "todos_inimigos"
    },
    "MAG_002": {
        "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
        "custo_mana": 15,
        "descricao": "Dispara um raio de gelo que pode deixar o inimigo lento.",
        "efeitos": {"DANO_MAGICO": 20, "LENTIDAO": 1},
        "alvo": "inimigo"
    },
    # Habilidade Ultimate com uso limitado
    "MAG_003": {
        "nome": "Meteoro", "emoji": "☄️", "tipo": "ATIVA",
        "custo_mana": 100,
        "descricao": "Invoca um meteoro que causa dano massivo em área.",
        "efeitos": {"DANO_MAGICO": 50},
        "alvo": "inimigo"
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
        },
        "alvo": "inimigo"
    },
    "MAG_005": {
    "nome": "Raio Congelante", "emoji": "❄️", "tipo": "ATIVA",
    "custo_mana": 45,
    "descricao": "Dispara um raio de gelo puro. Tem chance de congelar o alvo por 1 turno, mas o frio intenso também afeta o conjurador.",
    "alvo": "inimigo_e_self",
    "efeitos": {
        # Efeitos aplicados no inimigo selecionado
        "no_alvo": {
            "ATORDOADO": 1, # Chance de aplicar o status "Atordoado" por 1 turno
            "CHANCE_EFEITO": 0.8 # 80% de chance de funcionar
        },
        # Efeitos aplicados no próprio conjurador
        "no_self": {
            "ATORDOADO": 1, # O conjurador também fica atordoado por 1 turno
            "CHANCE_EFEITO": 1.0 # 100% de chance de se auto-congelar
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


"""

A Lista de Alvos (Versão 2.0 - Final)
Com a sua nova sugestão, nossa lista de alvos fica ainda mais completa e robusta.

"inimigo": Seleciona um inimigo.

"aliado": Seleciona um aliado.

"self": Afeta apenas o conjurador.

"todos_inimigos": Afeta todos os inimigos.

"grupo_aliado": Afeta todos os aliados, incluindo o conjurador.

"outros_aliados": Afeta todos os aliados, exceto o conjurador.

"aleatorio_inimigo": Afeta um inimigo aleatório.

"inimigo_e_self": (NOVO) Requer seleção de um inimigo e também aplica um efeito no conjurador.

"passivo": Efeito constante, não pode ser usado em batalha.

"""



"""A Lista Final de Alvos (Versão Definitiva)
Com todos os seus refinamentos, nossa lista final de alvos para a chave "alvo" no arquivo habilidades_library.py fica assim:

-- "inimigo"

Ação: Requer seleção de alvo. O painel mostrará os botões dos inimigos.

Uso: Ataques diretos, debuffs de alvo único.

-- "aliado"

Ação: Requer seleção de alvo. O painel mostrará os botões dos membros do seu grupo.

Uso: Curas direcionadas, buffs de alvo único.

-- "self"

Ação: Instantânea. Não requer seleção de alvo.

Uso: Buffs pessoais (aumento de defesa, dano, etc.).

-- "todos_inimigos"

Ação: Instantânea. Não requer seleção de alvo.

Uso: Ataques em área (AoE - Area of Effect) que atingem todos os monstros.

-- "grupo_aliado"

Ação: Instantânea. Não requer seleção de alvo.

Uso: Buffs ou curas em área que afetam todos os jogadores, incluindo o conjurador.

-- "outros_aliados"

Ação: Instantânea. Não requer seleção de alvo.

Uso: Buffs ou curas em área que afetam apenas os companheiros de equipe, excluindo o conjurador.

-- "aleatorio_inimigo"

Ação: Instantânea. Não requer seleção de alvo.

Uso: Habilidades "caóticas" ou "em ricochete" que atingem um inimigo ao acaso.

-- "passivo"

Ação: Nenhuma. O botão da habilidade fica desativado na batalha.

Uso: Bônus permanentes aplicados aos status do personagem."""