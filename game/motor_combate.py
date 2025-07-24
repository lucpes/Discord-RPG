# game/motor_combate.py
from data.habilidades_library import HABILIDADES
import random

def calcular_dano(dano_atacante: int, armadura_defensor: int) -> int:
    """
    Fórmula de cálculo de dano.
    Reduz o dano com base na armadura do defensor.
    """
    # Fórmula de redução de dano com retornos decrescentes
    reducao = armadura_defensor / (armadura_defensor + 100)
    dano_final = dano_atacante * (1 - reducao)
    
    # Adiciona uma pequena variação de +/- 10%
    variacao = dano_final * 0.1
    return int(random.uniform(dano_final - variacao, dano_final + variacao))

def processar_acao_jogador(jogador: dict, monstro: dict, skill_id: str) -> dict:
    """Processa a habilidade usada pelo jogador e retorna os resultados."""
    skill_data = HABILIDADES.get(skill_id)
    if not skill_data:
        return {"log": "Habilidade desconhecida."}

    # Verifica se o jogador tem mana suficiente
    custo_mana = skill_data.get('custo_mana', 0)
    if jogador['mana_atual'] < custo_mana:
        return {"log": f"Você não tem mana suficiente para usar {skill_data['nome']}!", "dano_causado": 0}

    jogador['mana_atual'] -= custo_mana
    
    log = f"Você usou **{skill_data['nome']}**!"
    dano_causado = 0
    
    # Aplica os efeitos da habilidade
    if efeitos := skill_data.get('efeitos'):
        dano_habilidade = efeitos.get('DANO', 0) + efeitos.get('DANO_MAGICO', 0)
        dano_total_base = jogador['stats'].get('DANO', 0) + jogador['stats'].get('DANO_MAGICO', 0) + dano_habilidade
        
        if dano_total_base > 0:
            dano_causado = calcular_dano(dano_total_base, monstro['stats'].get('ARMADURA', 0))
            monstro['vida_atual'] -= dano_causado
            log += f"\nVocê causou `{dano_causado}` de dano ao {monstro['nome']}!"

    return {
        "log": log,
        "dano_causado": dano_causado,
        "jogador_update": {"mana_atual": jogador['mana_atual']},
        "monstro_update": {"vida_atual": monstro['vida_atual']}
    }

def processar_turno_monstro(monstro: dict, jogador: dict) -> dict:
    """Processa o ataque do monstro."""
    dano_monstro = monstro['stats'].get('DANO', 5)
    dano_causado = calcular_dano(dano_monstro, jogador['stats'].get('ARMADURA', 0))
    jogador['vida_atual'] -= dano_causado
    
    log = f"O {monstro['nome']} ataca e causa `{dano_causado}` de dano!"
    
    return {
        "log": log,
        "dano_causado": dano_causado,
        "jogador_update": {"vida_atual": jogador['vida_atual']}
    }