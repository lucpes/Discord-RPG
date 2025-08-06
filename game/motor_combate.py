# game/motor_combate.py
from data.habilidades_library import HABILIDADES
import random
from typing import Tuple, List, Dict
# --- IMPORTA O NOVO MOTOR DE STATUS ---
from .motor_status import calcular_dano, calcular_dano_critico


def aplicar_efeitos_periodicos(combatente: dict) -> str:
    log = ""
    vida_alterada = 0
    for efeito in list(combatente.get('efeitos_ativos', [])):
        if efeito['id'] == 'ENVENENAMENTO':
            dano_dot = efeito.get('dano', 0)
            combatente['vida_atual'] -= dano_dot
            vida_alterada -= dano_dot
    if vida_alterada < 0:
        nome = combatente.get('nome', combatente.get('nick', 'Alguém'))
        log += f"\n{nome} sofreu `{-vida_alterada}` de dano de veneno!"
    return log.strip()

def decrementar_duracao_efeitos(combatente: dict) -> str:
    log = ""
    efeitos_a_remover = []
    for efeito in combatente.get('efeitos_ativos', []):
        efeito['turnos_restantes'] -= 1
        if efeito['turnos_restantes'] <= 0:
            efeitos_a_remover.append(efeito)
    if efeitos_a_remover:
        combatente['efeitos_ativos'] = [ef for ef in combatente['efeitos_ativos'] if ef not in efeitos_a_remover]
        nome = combatente.get('nome', combatente.get('nick', 'Alguém'))
        log += f"\nAlguns efeitos em {nome} expiraram."
    return log.strip()

def esta_incapacitado(combatente: dict) -> Tuple[bool, str]:
    """Verifica se o combatente pode agir neste turno."""
    for efeito in combatente.get('efeitos_ativos', []):
        if efeito['id'] == 'CONGELAMENTO':
            nome = combatente.get('nome', combatente.get('nick', 'Alguém'))
            return True, f"\n{nome} está congelado e não pode agir!"
    return False, ""

# ---------------------------------------------------------------------------
# NOVO MOTOR DE COMBATE EM GRUPO
# ---------------------------------------------------------------------------

def processar_acao_em_grupo(conjurador: Dict, alvos: List[Dict], habilidade_id: str) -> Dict:
    """
    Processa uma ação de um conjurador em uma lista de alvos no combate em grupo.
    """
    if habilidade_id == "basic_attack":
        habilidade = {"nome": "Ataque Básico", "custo_mana": 0, "efeitos": {"DANO": conjurador['stats'].get('DANO', 5)}, "alvo": "inimigo"}
    else:
        habilidade = HABILIDADES.get(habilidade_id)

    if not habilidade:
        return {"log": "Habilidade desconhecida."}

    custo_mana = habilidade.get('custo_mana', 0)
    if conjurador.get('mana_atual', 0) < custo_mana:
        return {"log": f"**{conjurador['nick']}** tentou usar **{habilidade['nome']}**, mas não tem mana suficiente!"}

    conjurador['mana_atual'] -= custo_mana
    log_acao = [f"**{conjurador.get('nick', conjurador.get('nome'))}** usa **{habilidade['nome']}**!"]
    
    efeitos_no_alvo = habilidade.get('efeitos', {}).get('no_alvo', habilidade.get('efeitos', {}))
    efeitos_no_self = habilidade.get('efeitos', {}).get('no_self', {})

    for alvo in alvos:
        nome_alvo = alvo.get('nick', alvo.get('nome'))
        
        # Dano Físico
        if dano_fisico := efeitos_no_alvo.get('DANO', 0):
            dano_base = conjurador['stats'].get('DANO', 0) + dano_fisico if habilidade_id != "basic_attack" else dano_fisico
            
            # --- LÓGICA DE CRÍTICO ADICIONADA AQUI ---
            dano_apos_crit, foi_critico = calcular_dano_critico(dano_base, conjurador['stats'])
            if foi_critico:
                log_acao.append(f"  -> 💥 **ACERTO CRÍTICO!**")

            dano_final = calcular_dano(dano_apos_crit, alvo['stats'].get('ARMADURA', 0))
            alvo['vida_atual'] -= dano_final
            log_acao.append(f"  -> **{nome_alvo}** sofreu `{dano_final}` de dano físico!")
            
        # Dano Mágico
        if dano_magico := efeitos_no_alvo.get('DANO_MAGICO', 0):
            dano_base = conjurador['stats'].get('DANO_MAGICO', 0) + dano_magico

            # --- LÓGICA DE CRÍTICO ADICIONADA AQUI ---
            dano_apos_crit, foi_critico = calcular_dano_critico(dano_base, conjurador['stats'])
            if foi_critico:
                log_acao.append(f"  -> 💥 **ACERTO CRÍTICO!**")
            
            dano_final = calcular_dano(dano_apos_crit, alvo['stats'].get('ARMADURA_MAGICA', alvo['stats'].get('ARMADURA', 0)))
            alvo['vida_atual'] -= dano_final
            log_acao.append(f"  -> **{nome_alvo}** sofreu `{dano_final}` de dano mágico!")

        # Cura
        cura = efeitos_no_alvo.get('CURA', 0)
        if cura > 0:
            vida_max = alvo['stats'].get('VIDA_MAXIMA', 100)
            vida_anterior = alvo['vida_atual']
            alvo['vida_atual'] = min(vida_max, vida_anterior + cura)
            log_acao.append(f"  -> **{nome_alvo}** recuperou `{alvo['vida_atual'] - vida_anterior}` de vida!")
        
        # --- LÓGICA DE EFEITOS DE STATUS ATUALIZADA ---
        chance_efeito = efeitos_no_alvo.get('CHANCE_EFEITO', 1.0)
        if random.random() < chance_efeito:
            # Lista de todos os possíveis efeitos de status que uma habilidade pode aplicar
            status_effects = ["ATORDOADO", "LENTIDAO", "ENVENENAMENTO", "SILENCIO"]
            for efeito_id in status_effects:
                if efeito_id in efeitos_no_alvo:
                    duracao = efeitos_no_alvo[efeito_id]
                    # Evita aplicar o mesmo efeito duas vezes
                    if not any(e['id'] == efeito_id for e in alvo.get('efeitos_ativos', [])):
                        alvo.setdefault('efeitos_ativos', []).append({'id': efeito_id, 'turnos_restantes': duracao})
                        log_acao.append(f"  -> **{nome_alvo}** foi afetado por **{efeito_id.capitalize()}**!")

    # Processa efeitos no próprio conjurador (para habilidades de "rebote")
    if efeitos_no_self:
        nome_conjurador = conjurador.get('nick', conjurador.get('nome'))
        if 'ATORDOADO' in efeitos_no_self:
            duracao = efeitos_no_self['ATORDOADO']
            conjurador['efeitos_ativos'].append({'id': 'ATORDOADO', 'turnos_restantes': duracao})
            log_acao.append(f"  -> O recuo da magia atordoa **{nome_conjurador}**!")

    return {"log": "\n".join(log_acao)}


def processar_turno_monstro_em_grupo(monstro: Dict, jogadores: List[Dict]) -> Dict:
    """
    Processa o turno de um único monstro contra o grupo de jogadores.
    (Será implementado no próximo passo)
    """
    # Escolhe um alvo aleatório que esteja vivo
    alvos_vivos = [p for p in jogadores if p['vida_atual'] > 0]
    if not alvos_vivos:
        return {"log": ""} # Ninguém para atacar

    alvo = random.choice(alvos_vivos)
    
    dano_base = monstro['stats'].get('DANO', 5)
    dano_final = calcular_dano(dano_base, alvo['stats'].get('ARMADURA', 0))
    alvo['vida_atual'] -= dano_final

    log = (
        f"O **{monstro['nome']}** ataca **{alvo['nick']}**!\n"
        f"  -> **{alvo['nick']}** sofreu `{dano_final}` de dano!"
    )
    return {"log": log}

# ---------------------------------------------------------------------------
# FUNÇÕES 1v1 (LEGADO - Usadas pelo /explorar)
# ---------------------------------------------------------------------------

def processar_acao_jogador(jogador: dict, monstro: dict, skill_id: str) -> dict:
    if skill_id == "basic_attack":
        log = "Você usou **Ataque Básico**!"
        dano_base_jogador = jogador['stats'].get('DANO', 0)
        dano_causado = calcular_dano(dano_base_jogador, monstro['stats'].get('ARMADURA', 0))
        monstro['vida_atual'] = max(0, monstro['vida_atual'] - dano_causado)
        log += f"\nVocê causou `{dano_causado}` de dano físico!"
        # --- CORREÇÃO 1: O retorno do ataque básico estava incompleto ---
        return {
            "log": log, "dano_causado": dano_causado,
            "jogador_update": {}, # Ataque básico não muda status do jogador
            "monstro_update": {"vida_atual": monstro['vida_atual']}
        }

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
    return {
        "log": log, "dano_causado": dano_total_causado,
        "jogador_update": {"mana_atual": jogador['mana_atual'], "vida_atual": jogador['vida_atual']},
        "monstro_update": {"vida_atual": monstro['vida_atual']}
    }

# --- CORREÇÃO 2: A função do turno do monstro estava incompleta ---
def processar_turno_monstro(monstro: dict, jogador: dict) -> dict:
    incapacitado, log_incapacitado = esta_incapacitado(monstro)
    if incapacitado:
        return {"log": log_incapacitado, "dano_causado": 0, "jogador_update": {}}

    dano_monstro = monstro['stats'].get('DANO', 5)
    dano_causado = calcular_dano(dano_monstro, jogador['stats'].get('ARMADURA', 0))
    jogador['vida_atual'] = max(0, jogador['vida_atual'] - dano_causado)
    log = f"O {monstro['nome']} ataca e causa `{dano_causado}` de dano!"
    return {
        "log": log,
        "dano_causado": dano_causado,
        "jogador_update": {"vida_atual": jogador['vida_atual']}
    }