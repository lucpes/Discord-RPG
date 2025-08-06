# data/crafting_library.py

CRAFTING_RECIPES = {
    # Exemplo de item básico, sem chance de falha ou obra-prima
    "picareta_ferro_craft": {
        "nome": "Picareta de Ferro",
        "nivel_mesa_trabalho": 1,
        "item_criado_template_id": "picareta_ferro",
        "ingredientes": [
            {"template_id": "minerio_ferro", "quantidade": 5},
            {"template_id": "graveto", "quantidade": 2}
        ],
        "chance_falha": 0.0, # 0% de chance de falhar
    },

    # Exemplo de item avançado com chance de falha e obra-prima
    "espada_runica_craft": {
        "nome": "Espada Rúnica",
        "nivel_mesa_trabalho": 5,
        "item_criado_template_id": "espada_runica_comum",
        "ingredientes": [
            {"template_id": "barra_de_aco", "quantidade": 8},
            {"template_id": "essencia_magica", "quantidade": 3},
            {"template_id": "runa_antiga", "quantidade": 1}
        ],
        "chance_falha": 0.0, # 15% de chance de falhar 0.15
        
        # --- NOVAS CHAVES DE OBRA-PRIMA ---
        "chance_obra_prima": 0.0, # 10% de chance de criar uma obra-prima
        "item_obra_prima_template_id": "espada_runica_obra_prima" # Aponta para um template diferente
    },

    # Exemplo de consumível com obra-prima de quantidade
    "pocao_vida_media_craft": {
        "nome": "Poção de Vida Média",
        "nivel_mesa_trabalho": 3,
        "item_criado_template_id": "pocao_vida_media",
        "quantidade_criada": 3,
        "ingredientes": [
            {"template_id": "erva_forte", "quantidade": 5}
        ],
        "chance_falha": 0.0,
        
        # --- NOVAS CHAVES DE OBRA-PRIMA PARA CONSUMÍVEIS ---
        "chance_obra_prima": 0.0, # 20% de chance de um "craft perfeito"
        "quantidade_obra_prima": 5 # Se for obra-prima, cria 5 em vez de 3
    }
}


# Cria uma lista ordenada de IDs para a navegação
ORDERED_RECIPES = list(CRAFTING_RECIPES.keys())