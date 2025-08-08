# data/forja_library.py

FORJA_BLUEPRINTS = {
    # =============================================================================
    # Exemplo 1: Fusão Criativa com "SOMA_DIRETA_MAIS_BASE"
    # Ideal para criar itens híbridos e únicos.
    # =============================================================================
    "fusao_arco_lamina": {
        "nome": "Fundir Arco com Adaga",
        "tipo_planta": "FUSAO",
        "nivel_forja": 4,
        "nivel_ferreiro": 8,
        "xp_concedido": 350,
        "ingredientes": [
            {"tipo": "EQUIPAMENTO", "template_id": "arco_curto"},
            {"tipo": "EQUIPAMENTO", "template_id": "adaga_agil"}
        ],
        "resultado": {
            "template_id": "arco_com_lamina",
            "regra_stats": "SOMA_DIRETA_MAIS_BASE"
        }
    },

    # =============================================================================
    # Exemplo 2: Upgrade de Tier com "SOMA_BALANCEADA" (multiplicador 0.7)
    # O padrão para evoluir equipamentos comuns/incomuns.
    # =============================================================================
    "fusao_peitoral_couro": {
        "nome": "Fundir Peitorais de Couro",
        "tipo_planta": "FUSAO",
        "nivel_forja": 2,
        "nivel_ferreiro": 2,
        "xp_concedido": 200,
        "ingredientes": [
            {"tipo": "EQUIPAMENTO", "template_id": "peitoral_couro", "quantidade": 2}
        ],
        "resultado": {
            "template_id": "peitoral_couro_reforcado",
            "regra_stats": "SOMA_DIRETA_MAIS_BASE"
        }
    },

    # =============================================================================
    # Exemplo 3: Item de Fim de Jogo com "SOMA_PONDERADA" (multiplicador 0.5)
    # Perfeito para receitas com 3+ itens ou itens já muito fortes.
    # =============================================================================
    "forjar_lamina_mestre": {
        "nome": "Forjar Lâmina de Mestre",
        "tipo_planta": "FUSAO",
        "nivel_forja": 6,
        "nivel_ferreiro": 30,
        "xp_concedido": 5000,
        "ingredientes": [
            {"tipo": "EQUIPAMENTO", "template_id": "espada_guerreira_raro"},
            {"tipo": "EQUIPAMENTO", "template_id": "espada_guerreira_raro"},
            {"tipo": "MATERIAL", "template_id": "essencia_magica_pura"}
        ],
        "resultado": {
            "template_id": "lamina_de_mestre_epica",
            "regra_stats": "SOMA_PONDERADA"
        }
    },
    
    # Adicione aqui outras plantas de reforja (item + material)
}