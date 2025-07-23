# data/enchantments_library.py
# Cada encantamento pode modificar um ou mais status base.

ENCHANTMENTS = {
    "FOGO_1": {
        "nome": "Encantamento de Fogo I",
        "descricao": "A arma arde em chamas fracas.",
        "bonus": {
            "DANO": 5  # Adiciona 5 de dano base
        }
    },
    "VAMPIRO_1": {
        "nome": "Encantamento Vampírico Menor",
        "descricao": "Concede uma pequena chance de roubar vida.",
        "bonus": {
            "ROUBO_DE_VIDA": 3 # Um novo status que a lógica de combate entenderia
        }
    },
    "FORTIFICACAO_1": {
        "nome": "Encantamento de Fortificação I",
        "descricao": "A armadura é reforçada magicamente.",
        "bonus": {
            "ARMADURA": 10,
            "VIDA_EXTRA": 25
        }
    },
}