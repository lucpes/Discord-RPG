# data/game_constants.py
from collections import OrderedDict

# Agora o valor é um dicionário com nome de exibição e um emoji
EQUIPMENT_SLOTS = OrderedDict([
    ("CAPACETE", {"display": "Capacete", "emoji": "👑"}),
    ("PEITORAL", {"display": "Peitoral", "emoji": "👕"}),
    ("CALCA",    {"display": "Calça",    "emoji": "👖"}),
    ("BOTA",     {"display": "Bota",     "emoji": "👢"}),
    ("MAO_PRINCIPAL",  {"display": "Mão Primária", "emoji": "⚔️"}),
    ("MAO_SECUNDARIA", {"display": "Mão Secundária", "emoji": "🛡️"}),
    ("ANEL",     {"display": "Anel",     "emoji": "💍"}),
    ("COLAR",    {"display": "Colar",    "emoji": "📿"}),
    ("RUNA_1",   {"display": "Runa 1",   "emoji": "🌀"}),
    ("RUNA_2",   {"display": "Runa 2",   "emoji": "🌀"}),
    ("PICARETA", {"display": "Picareta", "emoji": "⛏️"}), # ADICIONE ESTA LINHA
    ("MACHADO", {"display": "Machado", "emoji": "🪓"}),   # ADICIONE ESTA L
])

# Dicionário de emojis para cada raridade
RARITY_EMOJIS = {
    "COMUM": "⚪️",
    "INCOMUM": "🟢",
    "RARO": "🔵",
    "EPICO": "🟣",
    "LENDARIO": "🟠"
}