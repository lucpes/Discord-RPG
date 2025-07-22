# game/item.py

class Item:
    """Classe base para todos os itens do jogo."""
    def __init__(self, nome: str, descricao: str, valor: int):
        self.nome = nome
        self.descricao = descricao
        self.valor = valor

    def __str__(self):
        return f"{self.nome}: {self.descricao}"

class Arma(Item):
    """Um item que pode ser equipado para aumentar o ataque."""
    def __init__(self, nome: str, descricao: str, valor: int, dano: int):
        super().__init__(nome, descricao, valor)
        self.dano = dano

    def __str__(self):
        return f"{self.nome} (Dano: {self.dano}) - {self.descricao}"

class Pocao(Item):
    """Um item consumível que pode restaurar vida."""
    def __init__(self, nome: str, descricao: str, valor: int, cura: int):
        super().__init__(nome, descricao, valor)
        self.cura = cura

    def usar(self, alvo):
        """Aplica o efeito da poção no alvo."""
        alvo.hp_atual += self.cura
        if alvo.hp_atual > alvo.hp_max:
            alvo.hp_atual = alvo.hp_max
        print(f"{alvo.nome} usou {self.nome} e curou {self.cura} de vida!")