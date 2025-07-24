# data/game_config.py

# --- CONFIGURAÇÕES DE PROGRESSÃO ---
BASE_XP = 100
XP_EXPONENT = 1.5

def calcular_xp_para_nivel(level: int) -> int:
    """
    Calcula a quantidade de XP necessária para passar do nível atual para o próximo.
    Ex: para ir do nível 1 para o 2, use level=1.
    """
    # Usamos int() para garantir que o resultado seja sempre um número inteiro.
    return int(BASE_XP * (level ** XP_EXPONENT))