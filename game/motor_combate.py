# game/motor_combate.py
from data.habilidades_library import HABILIDADES
import random

def processar_efeitos_de_turno(combatente: dict) -> str:
    log_efeitos = ""
    vida_alterada = 0
    efeitos_a_remover = []

    # Usamos uma cópia da lista para poder modificar a original com segurança
    for efeito in list(combatente.get('efeitos_ativos', [])):
        if efeito['id'] == 'ENVENENAMENTO':
            dano_dot = efeito.get('dano', 0)
            combatente['vida_atual'] -= dano_dot
            vida_alterada -= dano_dot
        
        efeito['turnos_restantes'] -= 1
        if efeito['turnos_restantes'] <= 0:
            efeitos_a_remover.append(efeito)

    if vida_alterada < 0:
        # Acessa o 'nome' ou o 'nick' para garantir que sempre haja um nome
        nome_combatente = combatente.get('nome', combatente.get('nick', 'Alguém'))
        log_efeitos += f"\n{nome_combatente} sofreu `{-vida_alterada}` de dano de veneno!"
    
    if efeitos_a_remover:
        combatente['efeitos_ativos'] = [ef for ef in combatente['efeitos_ativos'] if ef not in efeitos_a_remover]
        nome_combatente = combatente.get('nome', combatente.get('nick', 'Alguém'))
        log_efeitos += f"\nAlguns efeitos em {nome_combatente} expiraram."

    return log_efeitos.strip()

def calcular_dano(dano_atacante: int, armadura_defensor: int) -> int:
    reducao = armadura_defensor / (armadura_defensor + 100)
    dano_final = dano_atacante * (1 - reducao)
    variacao = dano_final * 0.1
    return int(random.uniform(dano_final - variacao, dano_final + variacao))

def processar_acao_jogador(jogador: dict, monstro: dict, skill_id: str) -> dict:
    # (O código que você enviou aqui já estava correto, mantivemos ele)
    if skill_id == "basic_attack":
        log = "Você usou **Ataque Básico**!"
        dano_base_jogador = jogador['stats'].get('DANO', 0)
        dano_causado = calcular_dano(dano_base_jogador, monstro['stats'].get('ARMADURA', 0))
        monstro['vida_atual'] = max(0, monstro['vida_atual'] - dano_causado)
        log += f"\nVocê causou `{dano_causado}` de dano físico!"
        return {"log": log, "dano_causado": dano_causado, "jogador_update": {}, "monstro_update": {"vida_atual": monstro['vida_atual']}}

    skill_data = HABILIDADES.get(skill_id)
    if not skill_data: return {"log": "Habilidade desconhecida."}

    custo_mana = skill_data.get('custo_mana', 0)
    if jogador['mana_atual'] < custo_mana: return {"log": f"Você não tem mana suficiente para usar {skill_data['nome']}!"}

    jogador['mana_atual'] -= custo_mana
    log = f"Você usou **{skill_data['nome']}**!"
    dano_total_causado = 0
    efeitos = skill_data.get('efeitos', {})

    if 'ENVENENAMENTO' in efeitos:
        efeito_data = efeitos['ENVENENAMENTO']
        monstro['efeitos_ativos'].append({'id': 'ENVENENAMENTO', 'dano': efeito_data['dano'], 'turnos_restantes': efeito_data['duracao']})
        log += f"\nO {monstro['nome']} foi envenenado!"
    if 'CONGELAMENTO' in efeitos:
        efeito_data = efeitos['CONGELAMENTO']
        monstro['efeitos_ativos'].append({'id': 'CONGELAMENTO', 'turnos_restantes': efeito_data['duracao']})
        log += f"\nO {monstro['nome']} foi congelado!"

    for efeito_id, valor in efeitos.items():
        if efeito_id == 'DANO':
            dano_base = jogador['stats'].get('DANO', 0) + valor
            dano_final = calcular_dano(dano_base, monstro['stats'].get('ARMADURA', 0))
            dano_total_causado += dano_final
            log += f"\nVocê causou `{dano_final}` de dano físico!"
        elif efeito_id == 'DANO_MAGICO':
            dano_base = jogador['stats'].get('DANO_MAGICO', 0) + valor
            dano_final = calcular_dano(dano_base, monstro['stats'].get('ARMADURA_MAGICA', 0))
            dano_total_causado += dano_final
            log += f"\nVocê causou `{dano_final}` de dano mágico!"
        elif efeito_id == 'CURA':
            vida_anterior = jogador['vida_atual']
            jogador['vida_atual'] = min(jogador['stats']['VIDA_MAXIMA'], vida_anterior + valor)
            log += f"\nVocê se curou em `{jogador['vida_atual'] - vida_anterior}` de vida!"
        elif "BUFF" in efeito_id or "MAXIMA" in efeito_id:
            stat_alvo = efeito_id.replace("_BUFF", "").replace("_MAXIMA", "")
            jogador['stats'][efeito_id] = jogador['stats'].get(efeito_id, 0) + valor
            if efeito_id == "VIDA_MAXIMA": jogador['vida_atual'] += valor
            if efeito_id == "MANA_MAXIMA": jogador['mana_atual'] += valor
            log += f"\nSeu status de **{stat_alvo}** aumentou em `{valor}`!"

    monstro['vida_atual'] = max(0, monstro['vida_atual'] - dano_total_causado)
    return {"log": log, "dano_causado": dano_total_causado, "jogador_update": {"mana_atual": jogador['mana_atual'], "vida_atual": jogador['vida_atual']}, "monstro_update": {"vida_atual": monstro['vida_atual']}}

def processar_turno_monstro(monstro: dict, jogador: dict) -> dict:
    for efeito in monstro.get('efeitos_ativos', []):
        if efeito['id'] == 'CONGELAMENTO':
            return {"log": f"O {monstro['nome']} está congelado e não pode agir!", "dano_causado": 0, "jogador_update": {}}
    
    dano_monstro = monstro['stats'].get('DANO', 5)
    dano_causado = calcular_dano(dano_monstro, jogador['stats'].get('ARMADURA', 0))
    jogador['vida_atual'] = max(0, jogador['vida_atual'] - dano_causado)
    log = f"O {monstro['nome']} ataca e causa `{dano_causado}` de dano!"
    return {"log": log, "dano_causado": dano_causado, "jogador_update": {"vida_atual": jogador['vida_atual']}}