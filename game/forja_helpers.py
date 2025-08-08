# game/forja_helpers.py
from data.forja_library import FORJA_BLUEPRINTS
from upload_templates import TEMPLATES_PARA_UPLOAD # Assumindo que este arquivo existe ou será um cache
import random

def calcular_stats_fusao(ingredientes: list, blueprint_resultado: dict) -> dict:
    """
    Calcula os stats finais de um item criado na forja, com base nos ingredientes
    e nas regras da planta (blueprint).
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
        # Pula materiais, pois eles não têm stats_gerados
        if 'instance_data' in item:
            for stat_id, value in item['instance_data'].get('stats_gerados', {}).items():
                stats_combinados[stat_id] = stats_combinados.get(stat_id, 0) + (value * multiplicador)

    # 2. Pega o template do item final para adicionar os seus stats base
    template_final_id = blueprint_resultado['template_id']
    template_final_data = TEMPLATES_PARA_UPLOAD.get(template_final_id, {})
    
    # Sorteia os stats base do novo item (como se fosse um drop)
    stats_base_novo_item = {
        s: random.randint(v['min'], v['max']) 
        for s, v in template_final_data.get('stats_base', {}).items()
    }

    # 3. Soma os stats combinados dos ingredientes com os stats base do novo item
    for stat_id, value in stats_base_novo_item.items():
        stats_combinados[stat_id] = stats_combinados.get(stat_id, 0) + value

    # Arredonda todos os valores para o inteiro mais próximo
    return {stat: round(val) for stat, val in stats_combinados.items()}