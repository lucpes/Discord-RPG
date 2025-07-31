# data/dungeon_monsters.py

# Define quais monstros podem aparecer em cada tier da fenda.
# O sistema escolherá aleatoriamente UM dos grupos para cada batalha.
TIER_MONSTERS = {
    1: [
        {"monstros": ["goblin_fraco", "goblin_fraco2"]},
        {"monstros": ["goblin_fraco", "slime_verde"]},
    ],
    2: [
        {"monstros": ["lobo_floresta", "goblin_fraco"]},
        {"monstros": ["esqueleto_guerreiro"]},
    ],
    3: [
        {"monstros": ["esqueleto_guerreiro", "lobo_floresta"]},
        {"monstros": ["esqueleto_guerreiro", "esqueleto_guerreiro"]},
    ],
    # Adicione Tiers 4 e 5 conforme criar mais monstros
}