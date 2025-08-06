# game/motor_status.py
import random

# --- CÁLCULOS DE COMBATE ---

def calcular_dano(dano_atacante: int, armadura_defensor: int) -> int:
    """Calcula o dano final após a redução da armadura e uma pequena variação."""
    if dano_atacante <= 0: return 0
    
    reducao = armadura_defensor / (armadura_defensor + 100)
    dano_reduzido = dano_atacante * (1 - reducao)
    variacao = dano_reduzido * 0.1 # Variação de 10% para mais ou para menos
    
    return int(random.uniform(dano_reduzido - variacao, dano_reduzido + variacao))

# --- CÁLCULOS DE COLETA (Mineração, etc.) ---

def calcular_tempo_final(tempo_base_s: int, eficiencia: float) -> int:
    """Calcula o tempo final de uma tarefa com base na eficiência."""
    tempo_reduzido = tempo_base_s * (1 - eficiencia)
    return int(tempo_reduzido)

def calcular_chance_final(chance_base: float, poder_coleta: float) -> float:
    """Calcula a chance final de coleta com base no poder de coleta."""
    return chance_base * (1 + poder_coleta)

def calcular_quantidade_final(range_quantidade: tuple, fortuna: int) -> int:
    """Calcula a quantidade final de um recurso coletado, aplicando a fortuna."""
    if not isinstance(range_quantidade, (list, tuple)) or len(range_quantidade) != 2:
        range_quantidade = (1, 1) # Valor padrão seguro
        
    quantidade_base = random.randint(range_quantidade[0], range_quantidade[1])
    return quantidade_base + fortuna