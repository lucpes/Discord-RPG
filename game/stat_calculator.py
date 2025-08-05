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
        # --- LÓGICA CORRIGIDA E MAIS ROBUSTA ---
        # Primeiro, pegamos a "instância" do item, não importa como ela chegue.
        # Se o dicionário 'item' tiver a chave 'instance_data', ele a usa.
        # Senão, ele assume que o próprio 'item' já é a instância.
        instance_data = item.get('instance_data', item)
        template_data = item.get('template_data', {})
        
        # Agora, buscamos os status de combate DENTRO da instância correta.
        if item_stats := instance_data.get('stats_gerados'):
            for stat_id, value in item_stats.items():
                stats_finais[stat_id] = stats_finais.get(stat_id, 0) + value
            
        # A lógica para ferramentas continua a mesma, mas agora não interfere com a de combate.
        if tool_attributes := template_data.get('atributos_ferramenta'):
            for attr_id, value in tool_attributes.items():
                if attr_id != 'durabilidade_max':
                    stats_finais[attr_id] = stats_finais.get(attr_id, 0) + value

    # 3. Adiciona os bônus de habilidades passivas (sem alterações)
    habilidades_equipadas = char_data.get('habilidades_equipadas', [])
    for skill_id in habilidades_equipadas:
        skill_info = HABILIDADES.get(skill_id)
        if skill_info and skill_info.get('tipo') == 'PASSIVA':
            if efeitos := skill_info.get('efeitos'):
                for stat_id, value in efeitos.items():
                    stats_finais[stat_id] = stats_finais.get(stat_id, 0) + value
    
    return stats_finais