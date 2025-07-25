# game/motor_combate.py
from data.habilidades_library import HABILIDADES
import random

def calcular_dano(dano_atacante: int, armadura_defensor: int) -> int:
    # (Esta função não precisa de alterações)
    reducao = armadura_defensor / (armadura_defensor + 100)
    dano_final = dano_atacante * (1 - reducao)
    variacao = dano_final * 0.1
    return int(random.uniform(dano_final - variacao, dano_final + variacao))

# --- FUNÇÃO DE AÇÃO DO JOGADOR (Totalmente Refatorada) ---
def processar_acao_jogador(jogador: dict, monstro: dict, skill_id: str) -> dict:
    """Processa a habilidade usada pelo jogador e retorna os resultados."""
    skill_data = HABILIDADES.get(skill_id)
    if not skill_data:
        return {"log": "Habilidade desconhecida."}

    custo_mana = skill_data.get('custo_mana', 0)
    if jogador['mana_atual'] < custo_mana:
        return {"log": f"Você não tem mana suficiente para usar {skill_data['nome']}!", "dano_causado": 0, "jogador_update": {}, "monstro_update": {}}

    jogador['mana_atual'] -= custo_mana
    
    log = f"Você usou **{skill_data['nome']}**!"
    dano_causado = 0
    
    efeitos = skill_data.get('efeitos', {})

    # --- LÓGICA DE DANO SEPARADA ---
    # Verifica se a habilidade tem algum tipo de dano em seus efeitos
    dano_habilidade = efeitos.get('DANO', 0) + efeitos.get('DANO_MAGICO', 0)
    if dano_habilidade > 0:
        # Apenas se a habilidade causa dano, somamos o dano base do jogador
        dano_base_jogador = jogador['stats'].get('DANO', 0) + jogador['stats'].get('DANO_MAGICO', 0)
        dano_total_base = dano_base_jogador + dano_habilidade
        
        dano_causado = calcular_dano(dano_total_base, monstro['stats'].get('ARMADURA', 0))
        monstro['vida_atual'] -= dano_causado
        log += f"\nVocê causou `{dano_causado}` de dano ao {monstro['nome']}!"
    
    # --- LÓGICA DE BUFFS/CURAS (Exemplo) ---
    if "DEFESA_BUFF" in efeitos:
        # A lógica para aplicar o buff iria aqui. Por enquanto, só adicionamos ao log.
        log += f"\nSua defesa aumentou!"

    if "CURA" in efeitos:
        # A lógica de cura iria aqui.
        vida_curada = efeitos["CURA"]
        jogador['vida_atual'] = min(jogador['stats']['VIDA_MAXIMA'], jogador['vida_atual'] + vida_curada)
        log += f"\nVocê se curou em `{vida_curada}` pontos de vida!"
        
    return {
        "log": log,
        "dano_causado": dano_causado,
        "jogador_update": {"mana_atual": jogador['mana_atual'], "vida_atual": jogador['vida_atual']},
        "monstro_update": {"vida_atual": monstro['vida_atual']}
    }

def processar_turno_monstro(monstro: dict, jogador: dict) -> dict:
    # (Esta função não precisa de alterações)
    dano_monstro = monstro['stats'].get('DANO', 5)
    dano_causado = calcular_dano(dano_monstro, jogador['stats'].get('ARMADURA', 0))
    jogador['vida_atual'] -= dano_causado
    
    log = f"O {monstro['nome']} ataca e causa `{dano_causado}` de dano!"
    
    return {
        "log": log,
        "dano_causado": dano_causado,
        "jogador_update": {"vida_atual": jogador['vida_atual']}
    }