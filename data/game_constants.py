# data/game_constants.py
from collections import OrderedDict

# Usamos um OrderedDict para garantir que a ordem de exibição será sempre a mesma.
# A chave é o nome interno que usamos no template do item (em 'slot').
# O valor é o nome bonito que mostramos para o jogador.
EQUIPMENT_SLOTS = OrderedDict([
    ("CAPACETE", "Capacete"),
    ("PEITORAL", "Peitoral"),
    ("CALCA", "Calça"),
    ("BOTA", "Bota"),
    ("MAO_PRINCIPAL", "Mão Primária"),
    ("MAO_SECUNDARIA", "Mão Secundária"),
    ("ANEL", "Anel"),
    ("COLAR", "Colar"),
    ("RUNA_1", "Runa 1"),
    ("RUNA_2", "Runa 2"),
])