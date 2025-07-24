# game/stat_calculator.py
from data.classes_data import CLASSES_DATA
from data.habilidades_library import HABILIDADES

def calcular_stats_completos(char_data: dict, equipped_items: list) -> dict:
    """
    Calcula os status finais de um personagem somando os status base,
    bônus de itens e bônus de habilidades passivas.
    """
    classe = char_data.get('classe')
    if not classe:
        return {}

    # 1. Começa com os status base da classe
    stats_finais = CLASSES_DATA[classe].get('stats_base', {}).copy()

    # 2. Adiciona os status dos itens equipados
    for item in equipped_items:
        item_stats = item.get('instance_data', {}).get('stats_gerados', {})
        for stat_id, value in item_stats.items():
            stats_finais[stat_id] = stats_finais.get(stat_id, 0) + value

    # 3. Adiciona os bônus de habilidades passivas equipadas
    habilidades_equipadas = char_data.get('habilidades_equipadas', [])
    for skill_id in habilidades_equipadas:
        skill_info = HABILIDADES.get(skill_id)
        # Verifica se a habilidade é PASSIVA e tem efeitos
        if skill_info and skill_info.get('tipo') == 'PASSIVA':
            if efeitos := skill_info.get('efeitos'):
                for stat_id, value in efeitos.items():
                    stats_finais[stat_id] = stats_finais.get(stat_id, 0) + value
    
    return stats_finais