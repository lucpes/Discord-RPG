# data/loja_library.py

# O inventário agora é um dicionário com categorias como chaves
LOJA_INVENTARIO = {
    "CONSUMIVEIS": [
        {
            "template_id": "pocao_vida_pequena",
            "nivel_loja_req": 1,
            "preco_compra": 50, "tipo_moeda": "MOEDAS"
        },
    ],
    "MATERIAIS": [
        {
            "template_id": "graveto",
            "nivel_loja_req": 1,
            "preco_compra": 10, "tipo_moeda": "MOEDAS"
        },
        {
            "template_id": "minerio_ferro",
            "nivel_loja_req": 2,
            "preco_compra": 25, "tipo_moeda": "MOEDAS"
        },
    ],
    "FERRAMENTAS": [
        {
            "template_id": "picareta_simples",
            "nivel_loja_req": 2,
            "preco_compra": 250, "tipo_moeda": "MOEDAS"
        },
    ],
    # Adicione mais categorias e itens conforme necessário
}