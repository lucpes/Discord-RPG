# game/forja_helpers.py
import random
from typing import List, Dict

def calcular_stats_fusao(ingredientes: List[Dict], blueprint_resultado: Dict, item_templates_cache: Dict) -> Dict:
    """
    Calcula os stats finais de um item criado na forja, com base nos ingredientes,
    nas regras da planta (blueprint) e no cache de templates.
    """
    stats_combinados = {}
    regra = blueprint_resultado.get('regra_stats', 'SOMA_DIRETA_MAIS_BASE')
    multiplicador = 1.0

    if regra == "SOMA_BALANCEADA":
        multiplicador = 0.7
    elif regra == "SOMA_PONDERADA":
        multiplicador = 0.5

    # 1. Soma os stats dos ingredientes (aplicando o multiplicador)
    for item in ingredientes:
        if 'instance_data' in item:
            for stat_id, value in item['instance_data'].get('stats_gerados', {}).items():
                stats_combinados[stat_id] = stats_combinados.get(stat_id, 0) + (value * multiplicador)

    # 2. Pega o template do item final a partir do CACHE
    template_final_id = blueprint_resultado['template_id']
    template_final_data = item_templates_cache.get(template_final_id, {})
    
    # 3. Sorteia os stats base do novo item (como se fosse um drop)
    if stats_base_template := template_final_data.get('stats_base'):
        stats_base_novo_item = {
            s: random.randint(v['min'], v['max']) 
            for s, v in stats_base_template.items()
        }

        # 4. Soma os stats combinados dos ingredientes com os stats base do novo item
        for stat_id, value in stats_base_novo_item.items():
            stats_combinados[stat_id] = stats_combinados.get(stat_id, 0) + value

    # Arredonda todos os valores para o inteiro mais próximo
    return {stat: round(val) for stat, val in stats_combinados.items()}